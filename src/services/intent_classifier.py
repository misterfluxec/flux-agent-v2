# src/services/intent_classifier.py
import re

def classify_intent(text: str) -> str:
    """
    Determina la intención del mensaje basado en palabras clave.
    Retorna: 'sales', 'support', 'bookings', o 'general'
    """
    if not text:
        return 'general'
    
    text = text.lower()
    
    # 1. Detección de Soporte
    support_keywords = ['ayuda', 'problema', 'error', 'no funciona', 'soporte', 'reclamo', 'devolución']
    if any(kw in text for kw in support_keywords):
        return 'support'
    
    # 2. Detección de Reservas
    booking_keywords = ['cita', 'reserva', 'agendar', 'turno', 'horario', 'disponible', 'calendario']
    if any(kw in text for kw in booking_keywords):
        return 'bookings'
    
    # 3. Detección de Ventas (es el defecto para productos/precios)
    sales_keywords = ['price', 'comprar', 'costo', 'venta', 'stock', 'descuento', 'envío']
    if any(kw in text for kw in sales_keywords):
        return 'sales'
        
    # 4. Defecto
    return 'general'
