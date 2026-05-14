from pydantic import BaseModel, Field

class ExecutionBudget(BaseModel):
    """
    Presupuesto de ejecución para prevenir loops infinitos por operación individual.
    """
    max_tokens: int = Field(default=8000, description="Máximo número de tokens permitidos por ejecución")
    max_cost: float = Field(default=0.5, description="Costo máximo en USD para esta operación (si aplica)")
    max_runtime_ms: int = Field(default=30000, description="Tiempo máximo total de ejecución (ms)")
    max_turns: int = Field(default=5, description="Número máximo de turnos (ej. llamadas a herramienta)")
    max_debates: int = Field(default=3, description="Límite estricto de rondas de debate CAMEL permitidas")
    
    def check_turns(self, current_turns: int) -> bool:
        return current_turns < self.max_turns
        
    def check_debates(self, current_debates: int) -> bool:
        return current_debates < self.max_debates

class TenantBudget(BaseModel):
    """
    Gobernanza agregada a nivel de tenant o usuario para prevenir abuso de la API subyacente (Ollama, OpenAI, etc).
    """
    tenant_id: str
    token_quota: int = Field(default=1000000, description="Cuota total de tokens permitidos")
    daily_token_limit: int = Field(default=50000, description="Límite de tokens por día")
    daily_cost_limit: float = Field(default=5.0, description="Límite de gasto diario en USD")
    max_parallel_agents: int = Field(default=10, description="Máximo número de agentes corriendo a la vez")
    max_debates_per_day: int = Field(default=100, description="Límite máximo de debates por día por tenant para evitar spam de LLM")
    
    def check_runtime(self, current_parallel: int) -> bool:
        return current_parallel < self.max_parallel_agents
        
    def check_cost(self, current_cost: float) -> bool:
        return current_cost < self.daily_cost_limit
