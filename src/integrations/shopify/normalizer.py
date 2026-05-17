from datetime import datetime
from typing import Dict, Any
from integrations.canonical import CanonicalOrder

class ShopifyNormalizer:
    """
    Pure translator for Shopify Order Webhooks.
    """
    
    @staticmethod
    def to_canonical_order(raw_payload: Dict[str, Any]) -> CanonicalOrder:
        try:
            return CanonicalOrder(
                external_id=str(raw_payload.get("id")),
                provider="shopify",
                customer_id=str(raw_payload.get("customer", {}).get("id")),
                total_amount=float(raw_payload.get("total_price", 0.0)),
                currency=raw_payload.get("currency", "USD"),
                items=[
                    {
                        "product_id": str(item.get("product_id")),
                        "variant_id": str(item.get("variant_id")),
                        "quantity": item.get("quantity"),
                        "price": float(item.get("price"))
                    } for item in raw_payload.get("line_items", [])
                ],
                status=raw_payload.get("financial_status", "pending")
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid Shopify Order payload: {e}")
