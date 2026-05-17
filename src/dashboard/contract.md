# Contrato de Telemetría (FluxAgent V2)

Este documento especifica el contrato de comunicación entre el Backend y el Frontend para el consumo de telemetría de tareas en tiempo real.

## 1. Conexión WebSocket

El flujo principal de datos de telemetría ocurre a través de WebSockets.

**Endpoint:** `ws://<api-host>/api/v1/telemetry/ws/tasks/{task_id}?token={jwt}`

### Autenticación
El token JWT debe pasarse como query parameter debido a las limitaciones de los WebSockets nativos en el navegador para enviar headers personalizados.

## 2. Tipos de Eventos (`event_type`)

El servidor empujará payloads en formato JSON. El contrato garantiza que el campo `event_type` estará siempre presente en la raíz del evento.

| Evento | Descripción |
|---|---|
| `task_started` | La tarea en segundo plano ha comenzado. |
| `step_started` | Un nuevo paso lógico de la tarea ha iniciado. |
| `step_completed` | El paso lógico actual se ha completado. |
| `step_failed` | El paso lógico actual ha fallado. |
| `task_completed` | La tarea en su totalidad ha terminado exitosamente. |
| `task_failed` | La tarea ha fallado (timeout, excepción no controlada). |

## 3. Payload Estándar (ProgressEvent)

Cada mensaje WebSocket tendrá la siguiente estructura base:

```json
{
  "event_type": "step_completed",
  "task_id": "uuid-v4",
  "timestamp": "2024-03-15T10:30:00Z",
  "data": {
    "label": "Indexando fragmentos RAG",
    "weight": 0.5,
    "duration_ms": 1420,
    "tenant_id": "uuid-v4",
    "human_message": "Paso completado: Indexando fragmentos RAG (en 1420ms)."
  }
}
```

### El campo `human_message`
Este campo está garantizado por el backend para contener una cadena legible y "business-friendly" que puede ser renderizada directamente en la UI del Audit Trail, sin requerir traducción en el cliente.

## 4. REST Fallback (Polling)

Si la conexión WebSocket no es posible, se puede recurrir al endpoint REST:

**Endpoint:** `GET /api/v1/telemetry/tasks/{task_id}`

Devuelve el estado consolidado de la tarea:

```json
{
  "task_id": "uuid",
  "tenant_id": "uuid",
  "status": "running",
  "progress": 45.5,
  "current_step": "Procesando vectorización",
  "steps": [
    {
      "label": "Extrayendo metadata",
      "status": "completed",
      "duration_ms": 800
    },
    {
      "label": "Procesando vectorización",
      "status": "running"
    }
  ],
  "logs": [
    {
      "timestamp": "2024-03-15T10:30:00Z",
      "level": "info",
      "message": "Paso completado: Extrayendo metadata"
    }
  ]
}
```
