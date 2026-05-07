# =============================================================================
# FLUXAGENT V2 — DRAMATIQ WORKER CONFIG
# =============================================================================
# Configuración y ejecución de workers Dramatiq
# Manejo de múltiples colas y procesos
# =============================================================================

import os
import sys
import logging
import signal
import multiprocessing
from typing import List, Optional

from core.queue.broker import redis_broker, WORKER_CONFIG, QUEUES

logger = logging.getLogger(__name__)

class DramatiqWorker:
    """Wrapper para workers Dramatiq con configuración avanzada"""
    
    def __init__(self, queues: Optional[List[str]] = None, processes: Optional[int] = None):
        self.queues = queues or WORKER_CONFIG["queues"]
        self.processes = processes or WORKER_CONFIG["processes"]
        self.threads = WORKER_CONFIG["threads"]
        self.poll_interval = WORKER_CONFIG["poll_interval"]
        self.prefetch = WORKER_CONFIG["prefetch"]
        
        # Configurar logging
        self._setup_logging()
        
        # Cargar tareas automáticamente
        self._load_tasks()
    
    def _setup_logging(self):
        """Configura logging para workers"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        
        # Reducir logging de dependencias
        logging.getLogger("dramatiq").setLevel(logging.WARNING)
        logging.getLogger("redis").setLevel(logging.WARNING)
    
    def _load_tasks(self):
        """Importa todos los módulos de tareas para registrarlas"""
        try:
            # Importar tareas para que se registren con @dramatiq.actor
            from tasks.async_tasks import (
                enviar_whatsapp_task,
                procesar_webhook_whatsapp_task,
                procesar_audio_task,
                generar_respuesta_voz_task,
                actualizar_analytics_task,
                limpiar_cache_task,
                generar_reporte_diario_task,
                sincronizar_oauth_task
            )
            
            logger.info(f"✅ Tareas cargadas: {len(self.queues)} colas")
            
        except ImportError as e:
            logger.error(f"❌ Error importando tareas: {e}")
            raise
    
    def start(self):
        """Inicia el worker con configuración"""
        logger.info(f"🚀 Iniciando Dramatiq Worker")
        logger.info(f"📊 Configuración:")
        logger.info(f"   - Procesos: {self.processes}")
        logger.info(f"   - Threads/proceso: {self.threads}")
        logger.info(f"   - Colas: {', '.join(self.queues)}")
        logger.info(f"   - Poll interval: {self.poll_interval}ms")
        logger.info(f"   - Prefetch: {self.prefetch}")
        
        # Configurar handlers para señales
        self._setup_signal_handlers()
        
        try:
            # Importar y ejecutar worker de Dramatiq
            from dramatiq import Worker
            
            worker = Worker(
                broker=redis_broker,
                queues=self.queues,
                worker_threads=self.threads,
                worker_timeout=30,
                worker_sleep_time=self.poll_interval / 1000,
                prefetch_count=self.prefetch
            )
            
            logger.info("✅ Worker iniciado correctamente")
            worker.run()
            
        except KeyboardInterrupt:
            logger.info("🛑 Worker detenido por usuario")
        except Exception as e:
            logger.error(f"❌ Error en worker: {e}", exc_info=True)
            raise
    
    def _setup_signal_handlers(self):
        """Configura handlers para señales del sistema"""
        def signal_handler(signum, frame):
            logger.info(f"📡 Señal recibida: {signum}")
            logger.info("🛑 Deteniendo worker graceful...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def start_worker(queues: Optional[List[str]] = None, processes: Optional[int] = None):
    """Función helper para iniciar worker"""
    worker = DramatiqWorker(queues=queues, processes=processes)
    worker.start()

def start_multi_process_workers():
    """Inicia múltiples workers en procesos separados"""
    logger.info(f"🚀 Iniciando {WORKER_CONFIG['processes']} workers multiproceso")
    
    processes = []
    
    try:
        for i in range(WORKER_CONFIG["processes"]):
            p = multiprocessing.Process(
                target=start_worker,
                kwargs={
                    "queues": WORKER_CONFIG["queues"],
                    "processes": 1  # Cada proceso es un worker
                }
            )
            p.start()
            processes.append(p)
            logger.info(f"📡 Worker {i+1} iniciado (PID: {p.pid})")
        
        # Esperar a que todos terminen
        for p in processes:
            p.join()
            
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo todos los workers...")
        for p in processes:
            p.terminate()
            p.join()
    
    logger.info("✅ Todos los workers detenidos")

# =============================================================================
# COMANDOS DE EJECUCIÓN
# =============================================================================

def main():
    """Punto de entrada para ejecución desde CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dramatiq Worker para FluxAgent V2")
    parser.add_argument(
        "--queues", 
        nargs="+", 
        default=WORKER_CONFIG["queues"],
        help=f"Colas a procesar (default: {', '.join(WORKER_CONFIG['queues'])})"
    )
    parser.add_argument(
        "--processes", 
        type=int, 
        default=WORKER_CONFIG["processes"],
        help=f"Número de procesos (default: {WORKER_CONFIG['processes']})"
    )
    parser.add_argument(
        "--multi-process",
        action="store_true",
        help="Iniciar múltiples workers en procesos separados"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Modo watch para desarrollo (auto-reload)"
    )
    
    args = parser.parse_args()
    
    if args.watch:
        logger.info("👀 Modo watch activado")
        # TODO: Implementar auto-reload con watchdog
        logger.warning("⚠️ Modo watch no implementado aún")
    
    if args.multi_process:
        start_multi_process_workers()
    else:
        start_worker(queues=args.queues, processes=args.processes)

if __name__ == "__main__":
    main()
