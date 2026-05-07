# =============================================================================
# FLUXAGENT V2 — HELPERS SQL
# =============================================================================
# Utilidades reutilizables para consultas SQL seguras
# =============================================================================

from sqlalchemy import text
from typing import Union

def interval_days(days_param: str = "days") -> str:
    """Genera expresión SQL segura para INTERVAL con parámetros PostgreSQL
    
    Args:
        days_param: Nombre del parámetro en la consulta
        
    Returns:
        str: Expresión SQL segura para usar en consultas
        
    Example:
        # En consulta SQL:
        # AND fecha >= NOW() - {interval_days('days')}
    """
    return f"(:{days_param} || ' days')::INTERVAL"

def interval_hours(hours_param: str = "hours") -> str:
    """Genera expresión SQL segura para INTERVAL de horas"""
    return f"(:{hours_param} || ' hours')::INTERVAL"

def interval_minutes(minutes_param: str = "minutes") -> str:
    """Genera expresión SQL segura para INTERVAL de minutos"""
    return f"(:{minutes_param} || ' minutes')::INTERVAL"

def safe_interval(interval_type: str, param_name: str) -> str:
    """Genera expresión SQL segura para cualquier tipo de INTERVAL
    
    Args:
        interval_type: Tipo de intervalo ('days', 'hours', 'minutes', 'months')
        param_name: Nombre del parámetro
        
    Returns:
        str: Expresión SQL segura
    """
    valid_types = ['days', 'hours', 'minutes', 'months', 'years', 'seconds']
    if interval_type not in valid_types:
        raise ValueError(f"Tipo de intervalo inválido: {interval_type}")
    
    return f"(:{param_name} || ' {interval_type}')::INTERVAL"

def json_extract_path(path: str) -> str:
    """Genera expresión SQL para extraer de JSONB PostgreSQL
    
    Args:
        path: Path JSON (ej: 'ventas->>total')
        
    Returns:
        str: Expresión SQL segura
    """
    return f"data->'{path}'"

def format_timestamp_column(column_name: str, format_type: str = "date") -> str:
    """Formatea columna timestamp para PostgreSQL
    
    Args:
        column_name: Nombre de la columna
        format_type: 'date', 'datetime', 'time'
        
    Returns:
        str: Expresión SQL formateada
    """
    formats = {
        "date": f"DATE({column_name})",
        "datetime": column_name,
        "time": f"TIME({column_name})"
    }
    return formats.get(format_type, column_name)

# Ejemplos de uso:
"""
# Uso en queries SQL:
query = text(f"""
    SELECT COUNT(*) FROM conversaciones 
    WHERE tenant_id = :tid 
    AND iniciada_en >= NOW() - {interval_days('days')}
""")

# Uso con diferentes intervalos:
query = text(f"""
    SELECT COUNT(*) FROM mensajes 
    WHERE creado_en >= NOW() - {interval_hours('hours')}
    AND tenant_id = :tid
""")

# Uso con JSONB:
query = text(f"""
    SELECT {json_extract_path('ventas')} FROM agents 
    WHERE id = :agent_id
""")
"""
