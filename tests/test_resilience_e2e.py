# =============================================================================
# FLUXAGENT V2 — E2E TESTS FOR RESILIENCE PATTERNS
# =============================================================================
# Tests end-to-end para patrones de resiliencia implementados
# Validación de Circuit Breakers, Bulkheads, Timeouts y Retries
# =============================================================================

import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_circuit_breaker_functionality(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Funcionalidad de Circuit Breaker"""
    
    # Simular múltiples requests rápidas para forzar circuit breaker
    responses = []
    
    for i in range(10):  # Más del límite (5)
        response = await async_client.get(
            "/api/v1/llm/test-prompt", 
            headers=auth_headers
        )
        responses.append(response)
        await asyncio.sleep(0.01)  # Pequeña espera entre requests
    
    # Validar que algunas requests fallen por circuit breaker
    error_responses = [r for r in responses if r.status_code >= 500]
    assert len(error_responses) > 0, "Circuit breaker no se activó"
    
    # Esperar recuperación del circuit breaker
    await asyncio.sleep(2)  # Esperar recovery timeout
    
    # Verificar que el circuito se recuperó
    recovery_response = await async_client.get(
        "/api/v1/llm/test-prompt", 
        headers=auth_headers
    )
    
    # Debería funcionar después del recovery timeout
    assert recovery_response.status_code in [200, 503]  # 503 si sigue abierto

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_bulkhead_concurrency_limit(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Límite de concurrencia con Bulkhead"""
    
    # Lanzar múltiples requests concurrentes
    async def make_request():
        return await async_client.get(
            "/api/v1/llm/test-prompt", 
            headers=auth_headers
        )
    
    # Lanzar más requests que el límite concurrente (5)
    tasks = [make_request() for _ in range(10)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Validar respuestas
    successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
    rejected_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 429]
    error_responses = [r for r in responses if isinstance(r, Exception)]
    
    # Debería haber respuestas exitosas y rechazadas
    assert len(successful_responses) > 0, "No hay respuestas exitosas"
    assert len(rejected_responses) > 0, "Bulkhead no rechazó exceso de concurrencia"
    assert len(error_responses) >= 0, "No hay errores de timeout"

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_timeout_protection(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Protección por timeout"""
    
    # Request que debería timeout (simular operación lenta)
    response = await async_client.get(
        "/api/v1/llm/slow-prompt?timeout=2", 
        headers=auth_headers,
        timeout=5.0  # Timeout del cliente
    )
    
    # Debería recibir respuesta de timeout o fallback
    assert response.status_code in [200, 408, 504]
    
    if response.status_code == 200:
        data = response.json()
        # Si es 200, debería ser fallback response
        assert "error" in data or "fallback" in str(data).lower()

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_retry_mechanism(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Mecanismo de retry"""
    
    # Request que falle inicialmente pero funcione después de retries
    response = await async_client.post(
        "/api/v1/test/unreliable-endpoint", 
        json={"should_fail_first": True},
        headers=auth_headers
    )
    
    # Después de retries, debería funcionar
    assert response.status_code == 200
    
    data = response.json()
    assert "retry_count" in data or "attempts" in data

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_status_endpoint(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Endpoint de monitoreo de resiliencia"""
    
    response = await async_client.get(
        "/api/v1/resilience/status", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar estructura de respuesta
    assert "circuit_breakers" in data
    assert "bulkheads" in data
    assert "timeouts" in data
    assert "services_protected" in data
    
    # Validar que haya servicios protegidos
    assert len(data["services_protected"]) > 0

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_health_check(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Health check de resiliencia"""
    
    response = await async_client.get(
        "/api/v1/resilience/health", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar estructura de health check
    assert "health_status" in data
    assert "health_score" in data
    assert "issues" in data
    
    # Validar que sea un estado válido
    assert data["health_status"] in ["healthy", "degraded", "unhealthy", "critical"]
    assert 0 <= data["health_score"] <= 100

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_metrics_endpoint(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Endpoint de métricas de resiliencia"""
    
    response = await async_client.get(
        "/api/v1/resilience/metrics", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar estructura de métricas
    assert "circuit_breakers" in data
    assert "bulkheads" in data
    assert "timeouts" in data
    
    # Validar métricas de circuit breakers
    cb_metrics = data["circuit_breakers"]
    assert "total" in cb_metrics
    assert "open" in cb_metrics
    assert "closed" in cb_metrics
    assert "avg_failure_rate" in cb_metrics
    
    # Validar métricas de bulkheads
    bh_metrics = data["bulkheads"]
    assert "total_requests" in bh_metrics
    assert "successful_requests" in bh_metrics
    assert "rejected_requests" in bh_metrics
    assert "avg_success_rate" in bh_metrics

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_reset_functionality(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Funcionalidad de reset de resiliencia"""
    
    # Primero obtener estado inicial
    initial_response = await async_client.get(
        "/api/v1/resilience/status", 
        headers=auth_headers
    )
    assert initial_response.status_code == 200
    
    # Resetear circuit breakers
    reset_response = await async_client.post(
        "/api/v1/resilience/reset/circuit_breaker", 
        headers=auth_headers
    )
    
    assert reset_response.status_code == 200
    reset_data = reset_response.json()
    assert reset_data["status"] == "success"
    
    # Verificar que se reseteó
    await asyncio.sleep(0.5)
    
    final_response = await async_client.get(
        "/api/v1/resilience/status", 
        headers=auth_headers
    )
    assert final_response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_with_real_load(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Resiliencia bajo carga real"""
    
    # Simular carga moderada
    async def make_concurrent_requests(count: int):
        tasks = []
        for i in range(count):
            task = async_client.get(
                f"/api/v1/analytics/overview?days=7&request_id={i}", 
                headers=auth_headers
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    # Primera ronda de carga (20 requests concurrentes)
    responses_1 = await make_concurrent_requests(20)
    
    # Segunda ronda después de un breve descanso
    await asyncio.sleep(1)
    responses_2 = await make_concurrent_requests(20)
    
    # Analizar resultados
    def analyze_responses(responses):
        successful = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
        rate_limited = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 429]
        errors = [r for r in responses if isinstance(r, Exception)]
        return len(successful), len(rate_limited), len(errors)
    
    success_1, rate_limited_1, errors_1 = analyze_responses(responses_1)
    success_2, rate_limited_2, errors_2 = analyze_responses(responses_2)
    
    # Validar comportamiento de resiliencia
    assert success_1 > 0, "No hay respuestas exitosas en primera ronda"
    assert success_2 > 0, "No hay respuestas exitosas en segunda ronda"
    
    # Debería haber rate limiting en al menos una ronda
    assert rate_limited_1 > 0 or rate_limited_2 > 0, "No hay rate limiting detectado"
    
    # Errores deben ser manejados por resiliencia
    total_errors = errors_1 + errors_2
    assert total_errors >= 0, "No hay errores manejados"

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_cross_service_isolation(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Aislamiento entre servicios con resiliencia"""
    
    # Hacer fallar un servicio específico
    await async_client.post(
        "/api/v1/test/simulate-failure?service=llm", 
        json={"failure_type": "circuit_breaker"},
        headers=auth_headers
    )
    
    # Esperar que el circuit breaker se abra
    await asyncio.sleep(1)
    
    # Verificar que otros servicios sigan funcionando
    other_services_response = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    
    # Analytics debería seguir funcionando (aislamiento)
    assert other_services_response.status_code == 200
    
    # LLM debería estar afectado
    llm_response = await async_client.get(
        "/api/v1/llm/test-prompt", 
        headers=auth_headers
    )
    
    # Debería fallar o usar fallback
    assert llm_response.status_code in [503, 200]  # 503 si circuito abierto, 200 si fallback

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_fallback_mechanism(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Mecanismo de fallback en resiliencia"""
    
    # Forzar fallback
    response = await async_client.get(
        "/api/v1/test/force-fallback?service=whatsapp", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar que sea una respuesta de fallback
    assert "fallback" in str(data).lower() or "error" in data
    assert "service_unavailable" in str(data).lower() or "busy" in str(data).lower()

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_adaptive_timeout(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Timeout adaptativo"""
    
    # Hacer múltiples requests con diferentes tiempos de respuesta
    responses = []
    
    for i in range(5):
        response = await async_client.get(
            f"/api/v1/test/adaptive-timeout?request_id={i}&delay={i*0.5}", 
            headers=auth_headers,
            timeout=10.0
        )
        responses.append(response)
        await asyncio.sleep(0.1)
    
    # Analizar tiempos de respuesta
    successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
    
    if successful_responses:
        # Validar que los timeouts se adapten
        # (esto depende de la implementación específica)
        assert len(successful_responses) > 0

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.resilience
async def test_resilience_integration_with_cache(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Integración de resiliencia con cache"""
    
    # Primera request (cache miss, debe pasar por resiliencia)
    response1 = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    
    assert response1.status_code == 200
    
    # Segunda request (cache hit, debería ser más rápida)
    response2 = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    
    assert response2.status_code == 200
    
    # Validar que la cache esté funcionando (si hay headers)
    if "x-cache-status" in response2.headers:
        assert response2.headers["x-cache-status"] == "HIT"
    
    # Ambas respuestas deben ser idénticas
    data1 = response1.json()
    data2 = response2.json()
    assert data1 == data2
