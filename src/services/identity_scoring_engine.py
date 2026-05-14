from typing import List, Dict, Any, Optional
import jellyfish # Para algoritmos fonéticos y de distancia
import logging
from dataclasses import dataclass
from uuid import UUID

logger = logging.getLogger(__name__)

@dataclass
class IdentityCandidate:
    customer_id: str
    match_score: float
    matched_by: List[str] # ["phone", "email", "phonetic_name"]

class IdentityScoringEngine:
    """
    Motor de Scoring Multi-Factor para Consolidación de Identidades (Fortress Path v2.6).
    Usa pesos ponderados y algoritmos fonéticos para identificar clientes en mercados LATAM.
    """
    
    # Pesos configurables por canal
    WEIGHTS = {
        "exact_phone": 0.50,
        "exact_email": 0.40,
        "exact_national_id": 0.90, # Máxima confianza
        "phonetic_name": 0.10,     # Apoyo para desempate
        "partial_email": 0.05
    }

    @classmethod
    def calculate_match_score(
        cls, 
        target_data: Dict[str, Any], 
        candidate_data: Dict[str, Any]
    ) -> float:
        """
        Calcula la probabilidad de que dos conjuntos de datos pertenezcan al mismo cliente.
        """
        score = 0.0
        matches = []

        # 1. Exact National ID (Cédula/DNI)
        if target_data.get("national_id") and target_data["national_id"] == candidate_data.get("national_id"):
            score += cls.WEIGHTS["exact_national_id"]
            matches.append("national_id")

        # 2. Exact Phone
        if target_data.get("phone") and target_data["phone"] == candidate_data.get("phone"):
            score += cls.WEIGHTS["exact_phone"]
            matches.append("phone")

        # 3. Exact Email
        if target_data.get("email") and target_data["email"].lower() == candidate_data.get("email", "").lower():
            score += cls.WEIGHTS["exact_email"]
            matches.append("email")

        # 4. Phonetic Name Match (Soundex/Metaphone)
        # Útil para: "Muñoz" vs "Munoz", "González" vs "Gonzales"
        if target_data.get("name") and candidate_data.get("name"):
            t_name = target_data["name"].lower()
            c_name = candidate_data["name"].lower()
            
            # Usamos Metaphone para mayor precisión en español
            t_meta = jellyfish.metaphone(t_name)
            c_meta = jellyfish.metaphone(c_name)
            
            if t_meta == c_meta:
                score += cls.WEIGHTS["phonetic_name"]
                matches.append("phonetic_name")
            else:
                # Distancia de Levenshtein para errores tipográficos leves
                dist = jellyfish.levenshtein_distance(t_name, c_name)
                if dist <= 2: # Max 2 caracteres de diferencia
                    score += cls.WEIGHTS["phonetic_name"] * 0.5
                    matches.append("levenshtein_name")

        return min(score, 1.0) # Cap at 100%

    @classmethod
    def find_best_match(
        cls, 
        target_data: Dict[str, Any], 
        candidates: List[Dict[str, Any]], 
        threshold: float = 0.60
    ) -> Optional[IdentityCandidate]:
        """
        Busca el mejor match entre una lista de candidatos.
        """
        best_score = 0.0
        best_candidate = None

        for cand in candidates:
            score = cls.calculate_match_score(target_data, cand)
            if score > best_score:
                best_score = score
                best_candidate = cand

        if best_score >= threshold:
            return IdentityCandidate(
                customer_id=best_candidate["id"],
                match_score=best_score,
                matched_by=[] # Se puede enriquecer
            )
        
        return None
