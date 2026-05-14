import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TransformEngine:
    """
    Ejecuta reglas declarativas (JSON) de transformación de datos.
    Cero código arbitrario (cero eval/exec). Completamente determinista.
    """

    @classmethod
    def apply_rule(cls, rule: Dict[str, Any], raw_data: Dict[str, Any]) -> Any:
        rule_type = rule.get("type")
        
        if rule_type == "extract":
            # Simple field extraction
            return raw_data.get(rule.get("field"))
            
        elif rule_type == "currency_to_float":
            # "$1,200.50" -> 1200.50
            val = str(raw_data.get(rule.get("field"), "0"))
            clean_val = val.replace("$", "").replace(",", "").strip()
            try:
                return float(clean_val)
            except ValueError:
                return 0.0
                
        elif rule_type == "concat":
            # "fields": ["Nombre", "Marca"], "separator": " - "
            fields: List[str] = rule.get("fields", [])
            sep: str = rule.get("separator", " ")
            values = [str(raw_data.get(f, "")) for f in fields if raw_data.get(f)]
            return sep.join(values)

        elif rule_type == "default_if_empty":
            val = raw_data.get(rule.get("field"))
            return val if val else rule.get("default")

        else:
            logger.warning(f"Regla de transformación desconocida: {rule_type}")
            return raw_data.get(rule.get("field"))

    @classmethod
    def transform(cls, mapping_rules: Dict[str, Dict[str, Any]], raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies a dictionary of mapping rules to a raw data row.
        mapping_rules: {"price": {"type": "currency_to_float", "field": "Precio Final"}, "name": {"type": "extract", "field": "Nombre"}}
        """
        payload = {}
        for canonical_key, rule in mapping_rules.items():
            payload[canonical_key] = cls.apply_rule(rule, raw_data)
        return payload
