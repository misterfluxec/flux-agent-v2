import logging
from typing import Dict, Any, Callable, Awaitable, List
from runtime.graph_node import GraphNode
from runtime.graph_edge import GraphEdge
from runtime.state_machine import AgentExecutionState

logger = logging.getLogger(__name__)

class ExecutionGraph:
    """
    Motor de ejecución del grafo (Graph Runtime).
    Controla el avance por los nodos de ejecución basados en los estados de AgentExecutionState.
    """
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[str]]] = {}
        self.compensators: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {}

    def add_node(self, node: GraphNode, handler: Callable):
        self.nodes[node.id] = node
        self.handlers[node.handler_name] = handler

    def add_edge(self, edge: GraphEdge, compensator: Callable = None):
        self.edges.append(edge)
        # Sort edges by priority descending to evaluate highest priority first
        self.edges.sort(key=lambda e: e.priority, reverse=True)
        if compensator and edge.compensation_handler:
            self.compensators[edge.compensation_handler] = compensator
            
        self.validate_no_cycles()

    def validate_no_cycles(self):
        """
        Validación en build-time para prevenir deadlocks o loops infinitos (Sprint D.2F).
        Utiliza DFS para encontrar ciclos.
        """
        adj = {node.id: [] for node in self.nodes.values()}
        for edge in self.edges:
            if edge.source in adj:
                adj[edge.source].append(edge.target)

        visited = set()
        rec_stack = set()

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    raise ValueError(f"[DeadlockDetector] Se ha detectado un ciclo en el grafo en el nodo: {node_id}")

    async def execute(self, start_node_id: str, context: Dict[str, Any]) -> str:
        """
        Ejecuta el grafo desde el start_node_id.
        El contexto debe inyectarse externamente (status de Redis, por ejemplo).
        """
        current_node_id = start_node_id
        path_taken = []
        edges_taken = []
        
        while current_node_id:
            node = self.nodes.get(current_node_id)
            if not node:
                logger.error(f"[Graph] Nodo no encontrado: {current_node_id}")
                break
                
            handler = self.handlers.get(node.handler_name)
            if not handler:
                logger.error(f"[Graph] Handler no registrado: {node.handler_name}")
                break
                
            logger.info(f"[Graph] Ejecutando nodo: {current_node_id}")
            path_taken.append(current_node_id)
            
            try:
                # El handler debe devolver un "resultado" (str) que coincida con la condición del edge
                # o None si se asume ejecución secuencial simple
                result = await handler(context)
                
                # Pausa por Agent State (Ejemplo: WAITING_APPROVAL)
                state = context.get("state")
                if state == AgentExecutionState.WAITING_APPROVAL:
                    logger.info(f"[Graph] Ejecución pausada en el nodo {current_node_id} (WAITING_APPROVAL).")
                    break

                # Evaluar bordes salientes
                next_node_id = None
                for edge in self.edges:
                    if edge.source == current_node_id:
                        if edge.condition is None or edge.condition == result:
                            next_node_id = edge.target
                            edges_taken.append(edge)
                            break
                            
                current_node_id = next_node_id
                    
            except Exception as e:
                logger.error(f"[Graph] Error en nodo {current_node_id}: {e}")
                # Lanzar compensación sobre los bordes recorridos
                await self.compensate(edges_taken, context)
                raise e
                
        return current_node_id

    async def compensate(self, edges_taken: List[GraphEdge], context: Dict[str, Any]):
        """Ejecuta lógicas de compensación en reversa (Saga Rollback) basándose en los bordes transitados"""
        logger.warning(f"[Graph] Iniciando compensación para bordes: {[e.source + '->' + e.target for e in edges_taken]}")
        for edge in reversed(edges_taken):
            if edge.compensation_handler:
                compensator = self.compensators.get(edge.compensation_handler)
                if compensator:
                    logger.info(f"[Graph] Ejecutando compensador {edge.compensation_handler} del borde {edge.source}->{edge.target}")
                    try:
                        await compensator(context)
                    except Exception as ce:
                        logger.error(f"[Graph] Fallo en compensador de {edge.source}->{edge.target}: {ce}")
