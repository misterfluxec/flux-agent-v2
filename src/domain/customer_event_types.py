from enum import Enum

class CustomerEventCategory(str, Enum):
    COMMERCE = "commerce"
    COMMUNICATION = "communication"
    SUPPORT = "support"
    SYSTEM = "system"

class CustomerEventType(str, Enum):
    # Commerce
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_PAID = "order.paid"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"
    ORDER_CANCELLED = "order.cancelled"
    
    # Financial
    PAYMENT_CREATED = "payment.created"
    PAYMENT_CONFIRMED = "payment.confirmed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # CRM / Sales
    LEAD_CREATED = "lead.created"
    LEAD_STAGE_CHANGED = "lead.stage.changed"
    LEAD_WON = "lead.won"
    LEAD_LOST = "lead.lost"
    
    # Operations
    APPOINTMENT_BOOKED = "appointment.booked"
    APPOINTMENT_CANCELLED = "appointment.cancelled"
    APPOINTMENT_COMPLETED = "appointment.completed"
    
    # Interactions
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    CALL_LOGGED = "call.logged"
    EMAIL_SENT = "email.sent"
    
    # Intelligence / Automated (future)
    CHURN_RISK_INCREASED = "intelligence.churn_risk_increased"
    UPSELL_OPPORTUNITY_DETECTED = "intelligence.upsell_opportunity"
    
class VisibilityLevel(str, Enum):
    LOW = "low"             # Solo útil para auditoría técnica o debugging profundo
    STANDARD = "standard"   # Interacciones normales, creación de registros
    HIGH = "high"           # Conversiones importantes, pagos exitosos, envíos
    CRITICAL = "critical"   # Reclamos, pagos fallidos, churn
