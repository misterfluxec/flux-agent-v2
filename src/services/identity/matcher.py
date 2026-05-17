# =============================================================================
# FLUXAGENT V2 — UNIFIED IDENTITY MATCHER (FORTRESS PATH)
# =============================================================================
# Motor de resolución de identidades multi-factor.
# Consolida algoritmos fonéticos, distancia de edición y scoring ponderado.
# =============================================================================

import re
from core.telemetry.logger import get_logger
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import jellyfish
except ImportError:
    jellyfish = None

logger = get_logger(__name__)

@dataclass
class MatchResult:
    customer_id: str
    score: float
    matched_factors: List[str]

class IdentityMatcher:
    """
    Motor de Scoring Multi-Factor para Consolidación de Identidades.
    Diseñado para mercados LATAM (manejo de tildes, ñ, y variaciones comunes).
    """
    
    WEIGHTS = {
        "exact_national_id": 0.90,
        "exact_phone": 0.60,
        "exact_email": 0.50,
        "phonetic_name": 0.15,
        "levenshtein_name": 0.08
    }

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text: return ""
        text = text.upper().strip()
        # Normalización básica de tildes
        text = re.sub(r'[ÁÀÄ]', 'A', text)
        text = re.sub(r'[ÉÈË]', 'E', text)
        text = re.sub(r'[ÍÌÏ]', 'I', text)
        text = re.sub(r'[ÓÒÖ]', 'O', text)
        text = re.sub(r'[ÚÙÜ]', 'U', text)
        return text

    @classmethod
    def calculate_score(cls, target: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        score = 0.0
        factors = []

        # 1. Identificación Nacional (DNI/CEDULA) - Máxima priority
        if target.get("national_id") and target["national_id"] == candidate.get("national_id"):
            score += cls.WEIGHTS["exact_national_id"]
            factors.append("national_id")

        # 2. Teléfono
        if target.get("phone") and target["phone"] == candidate.get("phone"):
            score += cls.WEIGHTS["exact_phone"]
            factors.append("phone")

        # 3. Email
        if target.get("email") and target["email"].lower() == candidate.get("email", "").lower():
            score += cls.WEIGHTS["exact_email"]
            factors.append("email")

        # 4. Matching Fonético de Nombre
        if target.get("name") and candidate.get("name"):
            t_name = cls._clean_text(target["name"])
            c_name = cls._clean_text(candidate["name"])
            
            match_found = False
            if jellyfish:
                if jellyfish.metaphone(t_name) == jellyfish.metaphone(c_name):
                    score += cls.WEIGHTS["phonetic_name"]
                    factors.append("metaphone_name")
                    match_found = True
            
            if not match_found:
                # Distancia de edición (Levenshtein)
                if jellyfish:
                    dist = jellyfish.levenshtein_distance(t_name, c_name)
                else:
                    # Fallback si no hay jellyfish (simulado simple)
                    dist = 0 if t_name == c_name else 10
                
                if dist <= 2:
                    score += cls.WEIGHTS["levenshtein_name"]
                    factors.append("levenshtein_name")

        return min(score, 1.0)

    @classmethod
    def find_best_match(
        cls, 
        target: Dict[str, Any], 
        candidates: List[Dict[str, Any]], 
        threshold: float = 0.60
    ) -> Optional[MatchResult]:
        best_score = 0.0
        best_cand = None
        
        for cand in candidates:
            score = cls.calculate_score(target, cand)
            if score > best_score:
                best_score = score
                best_cand = cand
                
        if best_score >= threshold and best_cand:
            return MatchResult(
                customer_id=str(best_cand.get("id")),
                score=best_score,
                matched_factors=[] # Podría expandirse
            )
        return None
