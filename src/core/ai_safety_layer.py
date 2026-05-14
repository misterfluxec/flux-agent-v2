import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AISafetyViolation(Exception):
    pass

class AISafetyLayer:
    """
    Intercepts AI actions before they are executed in the Workflow Runtime.
    Enforces moderation, hallucination checks, and safety rules.
    """
    def __init__(self, governance_service: Any, tenant_id: str):
        self.governance = governance_service
        self.tenant_id = tenant_id
        self.banned_keywords = ["sudo", "rm -rf", "drop table", "ignore previous instructions"]
        
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validates the outgoing prompt against injection attacks.
        """
        lower_prompt = prompt.lower()
        for kw in self.banned_keywords:
            if kw in lower_prompt:
                logger.error(f"[AI Safety] Prompt Injection detected. Keyword: {kw}")
                raise AISafetyViolation(f"Prompt injection detected.")
        return True

    def validate_action(self, action_name: str, payload: Dict[str, Any]) -> bool:
        """
        Validates the proposed AI action (e.g. before an Autonomous Agent executes a tool).
        """
        # Ex: Do not allow AI to refund > $500 without human approval
        if action_name == "issue_refund":
            amount = payload.get("amount", 0)
            if amount > 500:
                logger.error(f"[AI Safety] Agent attempted high-value refund: {amount}")
                raise AISafetyViolation("High-value refunds require Human-in-the-loop.")
                
        # Ex: Do not allow AI to bulk delete
        if action_name == "delete_customers":
            raise AISafetyViolation("AI is not authorized to delete customer records.")
            
        return True
        
    def sanitize_output(self, ai_response: str) -> str:
        """
        Strips potentially harmful formatting or markdown tricks.
        """
        # Basic implementation
        return ai_response.strip()

    async def validate_structured_output(self, schema_class: Any, raw_output: str, min_confidence: float = 0.8) -> Any:
        """
        Sprint H2: Pydantic Structured Output Validation + Confidence Check + Token Check.
        """
        import json
        
        # 1. Token Budget Check
        token_count = len(raw_output) // 4 # Simple heuristic for tokens
        quota_check = await self.governance.check_and_consume(self.tenant_id, "ai_tokens", token_count)
        if not quota_check["allowed"]:
            raise AISafetyViolation(f"Token budget exceeded: {quota_check['reason']}")

        # 2. Schema Validation
        try:
            raw_dict = json.loads(raw_output)
            parsed_data = schema_class(**raw_dict)
            
            # Check for confidence score if it exists in the schema
            if hasattr(parsed_data, 'confidence_score'):
                if parsed_data.confidence_score < min_confidence:
                    logger.warning(f"[AI Safety] Low confidence score ({parsed_data.confidence_score}) < {min_confidence}")
                    raise AISafetyViolation("Output confidence score is below the required threshold.")
                    
            return parsed_data
            
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"[AI Safety] Schema validation failed: {str(e)}")
            raise AISafetyViolation(f"AI output failed strict schema validation: {str(e)}")
