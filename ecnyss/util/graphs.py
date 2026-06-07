"""Graph utility functions for dependency analysis and topological sorting."""

from typing import Any, Dict, Set, List


def has_cycle(graph: Dict[Any, Set[Any]]) -> bool:
    """
    Detect if a directed graph contains a cycle.
    
    Uses DFS with three-color marking:
    - WHITE (0): Not visited
    - GRAY (1): Currently in recursion stack
    - BLACK (2): Fully processed
    
    Args:
        graph: Adjacency list representation where keys are nodes and
               values are sets of successor nodes.
    
    Returns:
        True if the graph contains a cycle, False otherwise.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[Any, int] = {}
    
    # Initialize all nodes as WHITE
    all_nodes = set(graph.keys())
    for successors in graph.values():
        all_nodes.update(successors)
    
    for node in all_nodes:
        color[node] = WHITE
    
    def dfs(node: Any) -> bool:
        """Returns True if a cycle is found from this node."""
        color[node] = GRAY
        
        for successor in graph.get(node, set()):
            if color.get(successor, WHITE) == GRAY:
                # Found a back edge - cycle detected
                return True
            if color.get(successor, WHITE) == WHITE:
                if dfs(successor):
                    return True
        
        color[node] = BLACK
        return False
    
    for node in all_nodes:
        if color[node] == WHITE:
            if dfs(node):
                return True
    
    return False


def topological_sort(graph: Dict[Any, Set[Any]]) -> List[Any]:
    """
    Perform topological sort on a directed acyclic graph (DAG).
    
    Uses Kahn's algorithm for deterministic ordering.
    
    Args:
        graph: Adjacency list representation where keys are nodes and
               values are sets of successor nodes.
    
    Returns:
        A list of nodes in topologically sorted order.
    
    Raises:
        ValueError: If the graph contains a cycle.
    """
    # Collect all nodes (including those only appearing as successors)
    all_nodes = set(graph.keys())
    for successors in graph.values():
        all_nodes.update(successors)
    
    # Calculate in-degree for each node
    in_degree: Dict[Any, int] = {node: 0 for node in all_nodes}
    for node in graph:
        for successor in graph[node]:
            in_degree[successor] += 1
    
    # Start with nodes that have no incoming edges
    # Sort for deterministic ordering
    queue = sorted([node for node in all_nodes if in_degree[node] == 0])
    result: List[Any] = []
    
    while queue:
        # Take the first node (deterministic due to sorting)
        node = queue.pop(0)
        result.append(node)
        
        # Reduce in-degree for all successors
        for successor in sorted(graph.get(node, set())):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                # Insert in sorted position for determinism
                queue.append(successor)
                queue.sort()
    
    # If not all nodes are in result, there's a cycle
    if len(result) != len(all_nodes):
        raise ValueError("Graph contains a cycle, cannot perform topological sort")
    
    return result
