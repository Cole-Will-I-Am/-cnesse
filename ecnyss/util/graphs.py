"""Graph utilities for dependency analysis."""

from typing import Dict, Set, List, Any


def has_cycle(graph: Dict[Any, Set[Any]]) -> bool:
    """
    Detect if a directed graph has a cycle.
    
    Args:
        graph: Dict mapping nodes to their successor sets
        
    Returns:
        True if the graph contains a cycle, False otherwise
    """
    # States: 0 = unvisited, 1 = visiting (in current path), 2 = visited
    state = {}
    
    def dfs(node: Any) -> bool:
        """Returns True if a cycle is found."""
        if node not in state:
            state[node] = 1  # Mark as visiting
            for successor in graph.get(node, set()):
                if state.get(successor, 0) == 1:  # Found back edge
                    return True
                if state.get(successor, 0) == 0:  # Unvisited
                    if dfs(successor):
                        return True
            state[node] = 2  # Mark as visited
        return False
    
    # Check all nodes (including those only appearing as successors)
    all_nodes = set(graph.keys())
    for successors in graph.values():
        all_nodes.update(successors)
    
    for node in all_nodes:
        if state.get(node, 0) == 0:
            if dfs(node):
                return True
    return False


def topological_sort(graph: Dict[Any, Set[Any]]) -> List[Any]:
    """
    Return nodes in topological order.
    
    Args:
        graph: Dict mapping nodes to their successor sets
        
    Returns:
        List of nodes in topological order
        
    Raises:
        ValueError: If the graph contains a cycle
    """
    if has_cycle(graph):
        raise ValueError("Graph contains a cycle")
    
    # Collect all nodes (including those only appearing as successors)
    all_nodes = set(graph.keys())
    for successors in graph.values():
        all_nodes.update(successors)
    
    # Calculate in-degrees
    in_degree = {node: 0 for node in all_nodes}
    for node, successors in graph.items():
        for successor in successors:
            in_degree[successor] += 1
    
    # Kahn's algorithm with deterministic ordering
    # Sort initial zero-in-degree nodes for determinism
    queue = sorted([node for node in all_nodes if in_degree[node] == 0])
    result = []
    
    while queue:
        node = queue.pop(0)
        result.append(node)
        for successor in sorted(graph.get(node, set())):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                # Insert in sorted position for determinism
                queue.append(successor)
                queue.sort()
    
    return result
