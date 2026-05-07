# =============================================================================
# FLUXAGENT V2 — E2E TESTS FOR AGENTS
# =============================================================================
# Tests end-to-end para el flujo completo de agentes
# Usa Pytest + TestContainers para aislamiento completo
# =============================================================================

import pytest
import json
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_create_agent_success(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Creación exitosa de agente"""
    payload = {
        "nombre": "Agente Test E2E",
        "area": "Ventas",
        "descripcion": "Agente de ventas para testing automatizado",
        "genero": "neutro",
        "humor": "profesional",
        "personalidad": "Amigable pero servicial",
        "idioma": "español",
        "tono": "profesional",
        "canales": ["web_chat"],
        "tipo_negocio": "Ventas online",
        "objetivo": "Asistir clientes en compras",
        "instrucciones": "Sé amable pero profesional",
        "modelo": "qwen2.5:3b",
        "temperatura": 0.7,
        "max_tokens": 1000,
        "agent_type": "sales",
        "especialidad": "Ventas de productos",
        "system_prompt": "Eres un asistente de ventas experto",
        "script_ventas": "¡Hola! Bienvenido a nuestra tienda. ¿En qué puedo ayudarte hoy?",
        "estado": "activo"
    }
    
    response = await async_client.post(
        "/api/v1/agents/", 
        json=payload, 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar respuesta
    assert data["nombre"] == payload["nombre"]
    assert data["area"] == payload["area"]
    assert data["agent_type"] == payload["agent_type"]
    assert "id" in data
    assert data["estado"] == "activo"
    
    # Validar timestamp
    assert "creado_en" in data
    assert "actualizado_en" in data

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_create_agent_validation_error(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Validación de errores en creación de agente"""
    # Payload inválido (nombre muy corto)
    payload = {
        "nombre": "AB",  # Muy corto
        "area": "Ventas",
        "modelo": "qwen2.5:3b",
        "agent_type": "sales"
    }
    
    response = await async_client.post(
        "/api/v1/agents/", 
        json=payload, 
        headers=auth_headers
    )
    
    assert response.status_code == 422
    data = response.json()
    
    # Validar mensaje de error
    assert "detail" in data
    assert any("nombre" in str(error).lower() for error in data["detail"])

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_get_agents_list(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Obtener lista de agentes"""
    # Primero crear un agente
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    
    # Obtener lista
    response = await async_client.get(
        "/api/v1/agents/", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar respuesta
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1
    
    # Validar que nuestro agente esté en la lista
    agent_names = [agent["nombre"] for agent in data["items"]]
    assert sample_agent_data["nombre"] in agent_names

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_get_agent_details(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Obtener detalles de un agente específico"""
    # Crear agente
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    agent_id = create_response.json()["id"]
    
    # Obtener detalles
    response = await async_client.get(
        f"/api/v1/agents/{agent_id}", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar todos los campos
    assert data["id"] == agent_id
    assert data["nombre"] == sample_agent_data["nombre"]
    assert data["area"] == sample_agent_data["area"]
    assert data["agent_type"] == sample_agent_data["agent_type"]
    assert data["estado"] == "activo"

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_update_agent(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Actualizar agente existente"""
    # Crear agente
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    agent_id = create_response.json()["id"]
    
    # Actualizar
    update_payload = {
        "nombre": "Agente Actualizado E2E",
        "descripcion": "Descripción actualizada para testing",
        "temperatura": 0.8
    }
    
    response = await async_client.put(
        f"/api/v1/agents/{agent_id}", 
        json=update_payload, 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar actualización
    assert data["nombre"] == update_payload["nombre"]
    assert data["descripcion"] == update_payload["descripcion"]
    assert data["temperatura"] == update_payload["temperatura"]
    assert data["actualizado_en"] is not None

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_delete_agent(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Eliminar agente"""
    # Crear agente
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    agent_id = create_response.json()["id"]
    
    # Eliminar
    response = await async_client.delete(
        f"/api/v1/agents/{agent_id}", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Verificar que no exista
    get_response = await async_client.get(
        f"/api/v1/agents/{agent_id}", 
        headers=auth_headers
    )
    
    assert get_response.status_code == 404

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_chat_interaction(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Interacción de chat con agente"""
    # Crear agente
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    agent_id = create_response.json()["id"]
    
    # Iniciar conversación
    conversation_payload = {
        "agente_id": agent_id,
        "canal": "web_chat",
        "cliente_id": "test-client-e2e"
    }
    
    conv_response = await async_client.post(
        "/api/v1/conversations/", 
        json=conversation_payload, 
        headers=auth_headers
    )
    
    assert conv_response.status_code == 200
    conversation_id = conv_response.json()["id"]
    
    # Enviar mensaje
    message_payload = {
        "conversacion_id": conversation_id,
        "contenido": "Hola, quiero comprar un producto",
        "direccion": "outbound"
    }
    
    msg_response = await async_client.post(
        "/api/v1/messages/", 
        json=message_payload, 
        headers=auth_headers
    )
    
    assert msg_response.status_code == 200
    message_data = msg_response.json()
    
    # Validar mensaje
    assert message_data["contenido"] == message_payload["contenido"]
    assert message_data["direccion"] == message_payload["direccion"]
    assert message_data["conversacion_id"] == conversation_id

@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
async def test_agent_analytics_integration(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Integración con analytics después de crear agente"""
    # Crear agente
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    agent_id = create_response.json()["id"]
    
    # Esperar un momento para que se procesen las analytics
    import asyncio
    await asyncio.sleep(0.1)
    
    # Obtener analytics
    response = await async_client.get(
        "/api/v1/analytics/overview?days=7", 
        headers=auth_headers
    )
    
    assert response.status_code == 200
    analytics_data = response.json()
    
    # Validar estructura de analytics
    assert "total_conversations" in analytics_data
    assert "total_messages" in analytics_data
    assert "total_sales" in analytics_data
    assert "conversion_rate" in analytics_data
    assert isinstance(analytics_data["total_conversations"], int)
    assert isinstance(analytics_data["total_messages"], int)

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_unauthorized_access(async_client: AsyncClient):
    """Test E2E: Acceso no autorizado a endpoints de agentes"""
    payload = {
        "nombre": "Agente No Autorizado",
        "area": "Ventas",
        "agent_type": "sales"
    }
    
    # Intentar crear sin headers
    response = await async_client.post("/api/v1/agents/", json=payload)
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_cross_tenant_isolation(async_client: AsyncClient, auth_headers: dict, sample_agent_data: dict):
    """Test E2E: Aislamiento entre tenants"""
    # Crear agente en tenant 1
    create_response = await async_client.post(
        "/api/v1/agents/", 
        json=sample_agent_data, 
        headers=auth_headers
    )
    assert create_response.status_code == 200
    agent_id = create_response.json()["id"]
    
    # Crear headers para tenant 2 (simulado)
    tenant2_headers = {
        "Authorization": auth_headers["Authorization"],
        "X-Tenant-ID": "different-tenant-id"
    }
    
    # Intentar acceder al agente desde tenant 2
    response = await async_client.get(
        f"/api/v1/agents/{agent_id}", 
        headers=tenant2_headers
    )
    
    # Debería fallar por aislamiento de tenant
    assert response.status_code in [404, 403]

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agent_bulk_operations(async_client: AsyncClient, auth_headers: dict):
    """Test E2E: Operaciones bulk con múltiples agentes"""
    agents_data = [
        {
            "nombre": f"Agente Bulk {i}",
            "area": "Ventas",
            "agent_type": "sales",
            "modelo": "qwen2.5:3b"
        }
        for i in range(3)
    ]
    
    # Crear múltiples agentes
    created_agents = []
    for agent_data in agents_data:
        response = await async_client.post(
            "/api/v1/agents/", 
            json=agent_data, 
            headers=auth_headers
        )
        assert response.status_code == 200
        created_agents.append(response.json())
    
    # Verificar que todos estén en la lista
    list_response = await async_client.get(
        "/api/v1/agents/", 
        headers=auth_headers
    )
    
    assert list_response.status_code == 200
    list_data = list_response.json()
    
    created_names = [agent["nombre"] for agent in created_agents]
    listed_names = [agent["nombre"] for agent in list_data["items"]]
    
    for name in created_names:
        assert name in listed_names
