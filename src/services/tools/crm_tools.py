from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.tool_registry import ToolDefinition, ToolCategory

class UpdateLeadStatusInput(BaseModel):
    lead_id: str = Field(..., description="UUID del lead")
    new_status: str = Field(..., description="Nuevo estado a aplicar (ej: won, lost, negotiating)")
    notes: str = Field(default="", description="Notas adicionales justificando el cambio")

async def update_lead_status(input_data: UpdateLeadStatusInput, tenant_id: str, db_session: AsyncSession = None):
    """
    Ejemplo de implementación real:
    Actualiza el estado de un lead en PostgreSQL y gatilla workflows secundarios.
    """
    # Aquí iría: await db_session.execute(update(Lead)...)
    
    return {
        "success": True, 
        "lead_id": input_data.lead_id, 
        "status": input_data.new_status,
        "action": "Status updated successfully in CRM"
    }

TOOL_UPDATE_LEAD = ToolDefinition(
    name="update_lead_status",
    category=ToolCategory.CRM,
    description="Actualiza el estado comercial de un lead en el CRM interno",
    input_schema=UpdateLeadStatusInput,
    handler=update_lead_status,
    is_dangerous=False
)
