from typing import Callable, Any
import redis
import uuid
from functools import wraps
import os
import json

class TaskRunner:
    """
    Wrapper que permite usar BackgroundTasks ahora 
    y migrar a Celery después SIN cambiar el código de negocio
    """
    def __init__(self, use_celery: bool = False):
        self.use_celery = use_celery
        # Conectar a Redis para state management. Ajustado a la config usual.
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_password = os.getenv("REDIS_PASSWORD", "redisflux2026")
        self.redis = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)
        
        if use_celery:
            from celery import Celery
            self.celery = Celery('tasks', broker=f'redis://:{redis_password}@{redis_host}:{redis_port}/1')
    
    def run_async(self, task_func: Callable):
        """Decorador para ejecutar tareas en background"""
        @wraps(task_func)
        async def wrapper(*args, task_id: str = None, **kwargs):
            task_id = task_id or str(uuid.uuid4())
            
            if self.use_celery:
                # Ruta Celery (futuro)
                celery_task = self.celery.task(task_func)
                return await celery_task.delay(*args, task_id=task_id, **kwargs)
            else:
                # Ruta BackgroundTasks (MVP)
                # Guardar estado inicial en Redis
                self.update_progress(task_id, 0, "pending", "Iniciando tarea...", "pending")
                # Ejecutar en background nativo
                return await task_func(*args, task_id=task_id, **kwargs)
        return wrapper
    
    def update_progress(self, task_id: str, percentage: int, step: str, message: str, status: str = "processing", tenant_id: str = None):
        """Actualizar progreso en Redis (compatible con ambos enfoques)"""
        data = {
            "percentage": percentage,
            "step": step,
            "message": message,
            "status": status,
            "item_id": task_id
        }
        json_data = json.dumps(data)
        self.redis.setex(
            f"task:{task_id}:progress", 
            3600, 
            json_data
        )
        if tenant_id:
            self.redis.publish(f"tenant:{tenant_id}:ingest_progress", json_data)
    
    def get_progress(self, task_id: str) -> dict:
        """Obtener progreso (frontend agnóstico al backend)"""
        data = self.redis.get(f"task:{task_id}:progress")
        if not data:
            return {"percentage": 0, "step": "pending", "message": "Esperando...", "status": "pending"}
        return json.loads(data.decode('utf-8'))

# Instancia global configurada por variable de entorno
task_runner = TaskRunner(use_celery=os.getenv("USE_CELERY", "false").lower() == "true")
