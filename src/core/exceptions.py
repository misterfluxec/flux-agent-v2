class BusinessRuleError(Exception):
    """Excepción base para reglas de negocio comerciales."""
    pass

class InsufficientStockError(BusinessRuleError):
    """Lanzada cuando no hay stock suficiente para un producto físico."""
    pass

class SlotUnavailableError(BusinessRuleError):
    """Lanzada cuando un horario no está disponible."""
    pass
