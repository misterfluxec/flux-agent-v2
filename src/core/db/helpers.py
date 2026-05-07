# =============================================================================
# FLUXAGENT V2 — UTILIDADES DE BASE DE DATOS
# =============================================================================
# Funciones helper para consultas SQL comunes y formateo de datos
# =============================================================================

from sqlalchemy import text
from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timedelta

# =============================================================================
# FUNCIONES DE INTERVALO DE TIEMPO
# =============================================================================

def interval_days(days: int) -> str:
    """Genera intervalo de días para PostgreSQL"""
    return f"INTERVAL '{days} days'"

def interval_hours(hours: int) -> str:
    """Genera intervalo de horas para PostgreSQL"""
    return f"INTERVAL '{hours} hours'"

def interval_minutes(minutes: int) -> str:
    """Genera intervalo de minutos para PostgreSQL"""
    return f"INTERVAL '{minutes} minutes'"

# =============================================================================
# FUNCIONES DE JSONB
# =============================================================================

def json_extract_path(path: str) -> str:
    """Genera extractor de path JSONB para PostgreSQL"""
    return f"script_ventas#>'{{{path}}}'"

def json_query_path(path: str) -> str:
    """Genera query de path JSONB para PostgreSQL"""
    return f"script_ventas#>'{{{path}}}'"

# =============================================================================
# FUNCIONES DE FORMATEO
# =============================================================================

def format_timestamp(column_name: str, format_type: str = 'default') -> str:
    """Formatea timestamp según tipo especificado"""
    formats = {
        'default': f"TO_CHAR({column_name}, 'DD/MM/YYYY HH24:MI')",
        'date_only': f"TO_CHAR({column_name}, 'DD/MM/YYYY')",
        'time_only': f"TO_CHAR({column_name}, 'HH24:MI')",
        'iso': f"TO_CHAR({column_name}, 'YYYY-MM-DD HH24:MI:SS')"
    }
    return formats.get(format_type, column_name)
