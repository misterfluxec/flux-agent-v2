#!/usr/bin/env python3
"""
Script de Cleanup para Caché TTS
=================================
Elimina archivos de caché TTS antiguos y aplica política LRU.
Puede ejecutarse via cron o manualmente.

Uso:
    python scripts/cleanup_tts_cache.py [--dry-run] [--max-age-hours=48] [--max-size-gb=2]

Cron suggested (cada 6 horas):
    0 */6 * * * cd /home/mister/flux-agent-v2 && python3 scripts/cleanup_tts_cache.py >> /var/log/tts_cleanup.log 2>&1
"""

import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = "/app/data/media/tts_cache"
DEFAULT_MAX_AGE_HOURS = 48
DEFAULT_MAX_SIZE_GB = 2.0


def get_directory_size(path: str) -> int:
    """Calcular tamaño total del directorio en bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_directory_size(entry.path)
    except Exception as e:
        logger.warning(f"Error calculando tamaño de {path}: {e}")
    return total


def cleanup_by_age(cache_dir: str, max_age_hours: int, dry_run: bool = False) -> tuple:
    """Eliminar archivos mayores a max_age_hours."""
    import time
    deleted_count = 0
    deleted_size = 0
    max_age_seconds = max_age_hours * 3600
    current_time = time.time()
    
    try:
        for filename in os.listdir(cache_dir):
            if not filename.endswith('.mp3'):
                continue
                
            file_path = os.path.join(cache_dir, filename)
            try:
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    if dry_run:
                        logger.info(f"DRY-RUN: Eliminando {filename} (edad: {file_age/3600:.1f}h)")
                    else:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        deleted_size += file_size
                        logger.info(f"Eliminado {filename} (edad: {file_age/3600:.1f}h)")
            except Exception as e:
                logger.error(f"Error procesando {filename}: {e}")
    
    except Exception as e:
        logger.error(f"Error en cleanup_by_age: {e}")
    
    return deleted_count, deleted_size


def cleanup_by_size(cache_dir: str, max_size_gb: float, dry_run: bool = False) -> tuple:
    """Aplicar política LRU: eliminar archivos más antiguos hasta alcanzar el 80% del máximo."""
    deleted_count = 0
    deleted_size = 0
    target_size = int(max_size_gb * 0.8 * 1024 * 1024 * 1024)  # 80% del máximo
    
    # Obtener archivos ordenados por fecha de modificación
    files = []
    try:
        for filename in os.listdir(cache_dir):
            if not filename.endswith('.mp3'):
                continue
            file_path = os.path.join(cache_dir, filename)
            stat = os.stat(file_path)
            files.append((file_path, stat.st_mtime, stat.st_size))
    except Exception as e:
        logger.error(f"Error listando archivos: {e}")
        return 0, 0
    
    # Calcular tamaño actual
    current_size = sum(f[2] for f in files)
    
    if current_size <= target_size:
        logger.info(f"Tamaño actual ({current_size / 1024 / 1024:.1f}MB) dentro del límite")
        return 0, 0
    
    # Ordenar por fecha (más antiguos primero)
    files.sort(key=lambda x: x[1])
    
    # Eliminar hasta llegar al 80%
    for file_path, _, file_size in files:
        if current_size <= target_size:
            break
            
        try:
            if dry_run:
                logger.info(f"DRY-RUN: Eliminando {os.path.basename(file_path)} para liberar espacio")
            else:
                os.remove(file_path)
                current_size -= file_size
                deleted_count += 1
                deleted_size += file_size
                logger.info(f"Eliminado {os.path.basename(file_path)} (liberado {file_size / 1024 / 1024:.1f}MB)")
        except Exception as e:
            logger.error(f"Error eliminando {file_path}: {e}")
    
    return deleted_count, deleted_size


def main():
    parser = argparse.ArgumentParser(description="Cleanup TTS Cache")
    parser.add_argument('--cache-dir', default=DEFAULT_CACHE_DIR, help='Directorio de caché')
    parser.add_argument('--max-age-hours', type=int, default=DEFAULT_MAX_AGE_HOURS, help='Máximo edad en horas')
    parser.add_argument('--max-size-gb', type=float, default=DEFAULT_MAX_SIZE_GB, help='Tamaño máximo en GB')
    parser.add_argument('--dry-run', action='store_true', help='Simular sin eliminar')
    args = parser.parse_args()
    
    logger.info(f"Iniciando cleanup de caché TTS")
    logger.info(f"  Directorio: {args.cache_dir}")
    logger.info(f"  Max edad: {args.max_age_hours}h")
    logger.info(f"  Max tamaño: {args.max_size_gb}GB")
    
    if args.dry_run:
        logger.info("  MODO: DRY-RUN (sin eliminar)")
    
    if not os.path.exists(args.cache_dir):
        logger.error(f"Directorio no existe: {args.cache_dir}")
        sys.exit(1)
    
    # Cleanup por edad
    logger.info("--- Limpieza por edad ---")
    deleted_age, size_age = cleanup_by_age(args.cache_dir, args.max_age_hours, args.dry_run)
    logger.info(f"Eliminados {deleted_age} archivos ({size_age / 1024 / 1024:.1f}MB)")
    
    # Cleanup por tamaño (LRU)
    logger.info("--- Limpieza por tamaño (LRU) ---")
    deleted_size, size_cleaned = cleanup_by_size(args.cache_dir, args.max_size_gb, args.dry_run)
    logger.info(f"Eliminados {deleted_size} archivos ({size_cleaned / 1024 / 1024:.1f}MB)")
    
    # Resumen
    total_deleted = deleted_age + deleted_size
    total_size = size_age + size_cleaned
    
    current_size = get_directory_size(args.cache_dir)
    logger.info(f"--- RESUMEN ---")
    logger.info(f"Total eliminados: {total_deleted} archivos ({total_size / 1024 / 1024:.1f}MB)")
    logger.info(f"Tamaño actual: {current_size / 1024 / 1024:.1f}MB")
    
    if args.dry_run:
        logger.info("DRY-RUN completado - ningún archivo eliminado")


if __name__ == "__main__":
    main()