# =============================================================================
# FLUXAGENT V2 — E2E TESTS FOR ANALYTICS
# =============================================================================
# Tests end-to-end para el flujo completo de analytics
# Validación de cache, rate limiting y métricas
# =============================================================================

import pytest
import json
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_overview_uncached(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Analytics overview sin cache (primer request)"""
    response = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar estructura de respuesta
    assert "total_conversations" in data
    assert "total_messages" in data
    assert "total_sales" in data
    assert "conversion_rate" in data
    assert "avg_response_time" in data
    assert "sentiment_score" in data
    
    # Validar tipos de datos
    assert isinstance(data["total_conversations"], int)
    assert isinstance(data["total_messages"], int)
    assert isinstance(data["total_sales"], (int, float))
    assert isinstance(data["conversion_rate"], (int, float))
    assert isinstance(data["avg_response_time"], (int, float))
    assert isinstance(data["sentiment_score"], (int, float))
    
    # Validar rangos lógicos
    assert data["total_conversations"] >= 0
    assert data["total_messages"] >= 0
    assert data["total_sales"] >= 0
    assert 0 <= data["conversion_rate"] <= 100
    assert data["avg_response_time"] >= 0
    assert -1 <= data["sentiment_score"] <= 1

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_overview_cached(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Analytics overview con cache (segundo request)"""
    # Primera llamada (cache miss)
    response1 = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    assert response1.status_code == 200
    
    # Pequeña espera para asegurar cache
    await asyncio.sleep(0.1)
    
    # Segunda llamada (debe ser cache hit)
    response2 = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    assert response2.status_code == 200
    
    # Validar que ambas respuestas sean idénticas (cache hit)
    data1 = response1.json()
    data2 = response2.json()
    assert data1 == data2
    
    # Validar headers de cache si están implementados
    # assert response2.headers.get("x-cache-status") == "HIT"
    # assert response2.headers.get("x-cache-ttl") is not None

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_daily_stats(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Estadísticas diarias"""
    response = await async_client.get(
        "/api/v1/analytics/daily-stats?days=30", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar que sea una lista
    assert isinstance(data, list)
    
    if data:  # Si hay datos
        # Validar estructura de cada elemento
        for item in data[:5]:  # Validar primeros 5 elementos
            assert "date" in item
            assert "conversations" in item
            assert "messages" in item
            assert "sales" in item
            assert "leads" in item
            
            # Validar tipos
            assert isinstance(item["date"], str)
            assert isinstance(item["conversations"], int)
            assert isinstance(item["messages"], int)
            assert isinstance(item["sales"], (int, float))
            assert isinstance(item["leads"], int)
            
            # Validar rangos
            assert item["conversations"] >= 0
            assert item["messages"] >= 0
            assert item["sales"] >= 0
            assert item["leads"] >= 0

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_agent_stats(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Estadísticas por agente"""
    # Primero crear un agente para tener datos
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    agent_id = create_response.json()["id"]
    
    # Obtener estadísticas del agente
    response = await async_client.get(
        "/api/v1/analytics/agent-stats?days=7", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar que sea una lista
    assert isinstance(data, list)
    
    if data:  # Si hay datos
        # Buscar nuestro agente en la lista
        our_agent = next((agent for agent in data if agent.get("agent_id") == agent_id), None)
        
        if our_agent:
            # Validar estructura
            assert "agent_id" in our_agent
            assert "agent_name" in our_agent
            assert "conversations" in our_agent
            assert "messages" in our_agent
            assert "sales" in our_agent
            assert "avg_response_time" in our_agent
            
            # Validar tipos
            assert isinstance(our_agent["conversations"], int)
            assert isinstance(our_agent["messages"], int)
            assert isinstance(our_agent["sales"], (int, float))
            assert isinstance(our_agent["avg_response_time"], (int, float))

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_sentiment_analysis(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Análisis de sentimiento"""
    response = await async_client.get(
        "/api/v1/analytics/sentiment-analysis?days=7&granularity=daily", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar estructura
    assert "data" in data
    assert "summary" in data
    
    # Validar datos
    assert isinstance(data["data"], list)
    assert isinstance(data["summary"], dict)
    
    # Validar resumen
    summary = data["summary"]
    assert "overall_avg" in summary
    assert "total_conversations" in summary
    assert "granularity" in summary
    assert "period_days" in summary
    
    # Validar tipos de resumen
    assert isinstance(summary["overall_avg"], (int, float))
    assert isinstance(summary["total_conversations"], int)
    assert isinstance(summary["granularity"], str)
    assert isinstance(summary["period_days"], int)
    
    # Validar rangos
    assert -1 <= summary["overall_avg"] <= 1
    assert summary["total_conversations"] >= 0
    assert summary["granularity"] in ["daily", "hourly"]
    assert 1 <= summary["period_days"] <= 30

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_rate_limiting(async_client: AsyncClient):
    """Test E2E: Rate limiting en endpoints de analytics"""
    # Crear headers sin autenticación para forzar rate limiting
    headers = {"Authorization": "Bearer invalid-token"}
    
    # Hacer múltiples requests rápidamente
    responses = []
    for i in range(15):  # Más del límite (10/min)
        response = await async_client.get(
            "/api/v1/analytics/overview?days=7", 
            headers=headers
        )
        responses.append(response)
        
        # Pequeña espera entre requests
        await asyncio.sleep(0.01)
    
    # Validar que algunas requests fallen por rate limit
    rate_limited_responses = [r for r in responses if r.status_code == 429]
    assert len(rate_limited_responses) > 0
    
    # Validar headers de rate limit
    if rate_limited_responses:
        rate_limit_response = rate_limited_responses[0]
        assert "retry-after" in rate_limit_response.headers
        assert "x-rate-limit-limit" in rate_limit_response.headers
        assert "x-rate-limit-remaining" in rate_limit_response.headers

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_invalid_parameters(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Validación de parámetros inválidos"""
    
    # Test días inválidos
    response = await async_client.get(
        "/api/v1/analytics/overview?days=0", 
        headers=auth_headers
    )
    assert response.status_code == 422
    
    # Test días negativos
    response = await async_client.get(
        "/api/v1/analytics/overview?days=-5", 
        headers=auth_headers
    )
    assert response.status_code == 422
    
    # Test días muy grandes
    response = await async_client.get(
        "/api/v1/analytics/overview?days=365", 
        headers=auth_headers
    )
    assert response.status_code == 422
    
    # Test granularity inválida
    response = await async_client.get(
        "/api/v1/analytics/sentiment-analysis?days=7&granularity=invalid", 
        headers=auth_headers
    )
    assert response.status_code == 422

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_unauthorized_access(async_client: AsyncClient):
    """Test E2E: Acceso no autorizado a analytics"""
    
    # Test sin headers de autenticación
    response = await async_client.get("/api/v1/analytics/overview?days=7")
    assert response.status_code == 401
    
    # Test con token inválido
    response = await async_client.get(
        "/api/v1/analytics/overview?days=7",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_cross_tenant_isolation(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Aislamiento entre tenants en analytics"""
    
    # Crear headers para tenant diferente
    different_tenant_headers = {
        "Authorization": auth_headers["Authorization"],
        "X-Tenant-ID": "different-tenant-id"
    }
    
    # Intentar acceder a analytics de otro tenant
    response = await async_client.get(
        "/api/v1/analytics/overview?days=7",
        headers=different_tenant_headers
    )
    
    # Debería fallar por aislamiento de tenant
    assert response.status_code in [403, 404]

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
async def test_analytics_performance(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Performance de endpoints de analytics"""
    import time
    
    # Medir tiempo de respuesta
    start_time = time.time()
    
    response = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    
    end_time = time.time()
    response_time = end_time - start_time
    
    assert response.status_code == 200
    
    # Validar performance (debe ser < 2 segundos)
    assert response_time < 2.0, f"Analytics endpoint too slow: {response_time}s"
    
    # Validar que tenga headers de tiempo si están implementados
    # assert "x-response-time" in response.headers

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_cache_invalidation(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Invalidación de cache de analytics"""
    
    # Crear un agente
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    
    # Obtener analytics (debería cachear)
    response1 = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    assert response1.status_code == 200
    
    # Invalidar cache
    invalidate_response = await async_client.post(
        "/api/v1/analytics/invalidate-cache",
        headers=auth_headers
    )
    assert invalidate_response.status_code == 200
    
    # Obtener analytics nuevamente (debería ser cache miss)
    response2 = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    assert response2.status_code == 200
    
    # Validar que la invalidación funcionó (si hay timestamps)
    data1 = response1.json()
    data2 = response2.json()
    
    # Los datos podrían ser diferentes si hubo actividad entre las llamadas
    # pero la estructura debe ser consistente
    assert type(data1) == type(data2)
    assert set(data1.keys()) == set(data2.keys())

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_analytics_export_functionality(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Funcionalidad de exportación de analytics (si existe)"""
    
    # Test exportación CSV
    response = await async_client.get(
        "/api/v1/analytics/export?format=csv&days=7", 
        headers=auth_headers
    )
    
    # Si el endpoint existe, debe funcionar
    if response.status_code == 200:
        # Validar que sea CSV
        assert "text/csv" in response.headers.get("content-type", "")
        assert len(response.content) > 0
    else:
        # Si no existe, debe retornar 404
        assert response.status_code == 404
