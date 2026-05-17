from typing import Dict, Any

class SalesAgent:
    def __init__(self, session_id: str, is_premium: bool = False):
        self.session_id = session_id
        self.is_premium = is_premium
        self.current_stage = "greeting"

    async def chat(self, user_message: str) -> Dict[str, Any]:
        try:
            output_text = f"Mock response for: {user_message}"
            customer_name = None
            
            if "me llamo" in user_message.lower():
                customer_name = user_message.split("me llamo")[-1].strip()
                
            return {
                "response": output_text,
                "stage": self.current_stage,
                "session_id": self.session_id,
                "is_premium": self.is_premium,
                "customer_name": customer_name
            }
        except Exception as e:
            return {
                "response": "Lo siento, tuve un error procesando tu solicitud.",
                "error": str(e),
                "stage": self.current_stage
            }
