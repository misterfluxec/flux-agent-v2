import re
from typing import List, Tuple

def simplified_soundex_es(name: str) -> str:
    """
    Versión simplificada de Soundex adaptada para nombres en español.
    Ayuda a detectar variaciones como 'Juan Pérez' vs 'Juan Perez'.
    """
    if not name: return ""
    name = name.upper().strip()
    
    # Eliminar acentos
    name = re.sub(r'[ÁÀÄ]', 'A', name)
    name = re.sub(r'[ÉÈË]', 'E', name)
    name = re.sub(r'[ÍÌÏ]', 'I', name)
    name = re.sub(r'[ÓÒÖ]', 'O', name)
    name = re.sub(r'[ÚÙÜ]', 'U', name)
    
    # Simplificar consonantes problemáticas
    name = name.replace('PH', 'F')
    name = name.replace('V', 'B')
    name = name.replace('Z', 'S')
    name = name.replace('K', 'C')
    name = name.replace('CH', 'X') # Sonido similar en matching
    
    return name

class IdentityMatcher:
    @staticmethod
    def fuzzy_match(name1: str, name2: str) -> float:
        """Retorna un score de 0 a 1 basado en coincidencia fonética simplificada."""
        s1 = simplified_soundex_es(name1)
        s2 = simplified_soundex_es(name2)
        
        if s1 == s2: return 1.0
        
        # Levenshtein básico o coincidencia parcial
        if s1 in s2 or s2 in s1: return 0.85
        
        return 0.0
