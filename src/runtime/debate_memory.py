import hashlib
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

class DebateArgument:
    def __init__(self, agent_id: str, round_num: int, content: str):
        self.agent_id = agent_id
        self.round_num = round_num
        self.content = content
        self.semantic_hash = self._compute_semantic_hash(content)
        
    def _compute_semantic_hash(self, text: str) -> str:
        """
        Calcula un hash semántico básico normalizando el texto.
        En producción avanzada se usaría un embedding pequeño (ej. all-MiniLM-L6-v2) 
        y LSH (Locality Sensitive Hashing). Aquí usamos tokenización simple para atrapar repeticiones obvias.
        """
        import re
        # Normalizar: lowercase, remover puntuación extra y stopwords básicas
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        words = sorted(set(text.split())) # Set normalizado ordenado
        normalized_str = " ".join(words)
        return hashlib.sha256(normalized_str.encode('utf-8')).hexdigest()

class DebateMemory:
    """
    Rastrea argumentos durante un debate CAMEL o multi-agente para
    detectar y abortar loops infinitos (ej. Agente A y B se repiten).
    """
    
    def __init__(self):
        self.arguments: List[DebateArgument] = []
        self._hashes_seen: Set[str] = set()

    def record_argument(self, agent_id: str, round_num: int, content: str) -> bool:
        """
        Registra un argumento. Retorna True si detecta que es un loop (repetición).
        """
        arg = DebateArgument(agent_id, round_num, content)
        
        if arg.semantic_hash in self._hashes_seen:
            logger.warning(f"[DebateMemory] LOOP DETECTED! Agent {agent_id} repeated an argument in round {round_num}.")
            return True
            
        self.arguments.append(arg)
        self._hashes_seen.add(arg.semantic_hash)
        
        logger.debug(f"[DebateMemory] Recorded argument from {agent_id} (Round {round_num})")
        return False

    def is_looping(self, content: str) -> bool:
        """Verifica si el contenido ya fue dicho sin registrarlo."""
        dummy_arg = DebateArgument("temp", 0, content)
        return dummy_arg.semantic_hash in self._hashes_seen
