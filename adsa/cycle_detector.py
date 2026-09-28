"""ADSA Unit 2: Cycle Detection in Transaction Networks for Circular Fund Layering.

Detects money-laundering loops (e.g. A -> B -> C -> A) using Depth-First Search (DFS)
with 3-color node classification (WHITE, GRAY, BLACK) and back-edge detection.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from adsa.graph import Edge, TransactionGraph


class CycleDetector:
    """Algorithm to detect directed cycles in a transaction network (ADSA U2)."""

    def __init__(self, graph: TransactionGraph) -> None:
        self.graph = graph

    def check_if_edge_creates_cycle(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
        max_time_window_hours: Optional[float] = None,
    ) -> Tuple[bool, List[str]]:
        """Checks if adding an edge (source -> target) creates a circular flow.

        A cycle occurs if there is already a directed path from target -> source.
        Returns: (has_cycle, cycle_path_node_ids)
        """
        # If target == source (self-loop)
        if source == target:
            return True, [source, target]

        visited: Set[str] = set()
        path: List[str] = []

        # Run DFS from target searching for source
        def dfs_find_path(current: str, depth: int) -> bool:
            path.append(current)
            if current == source:
                return True
            if depth >= max_depth:
                path.pop()
                return False

            visited.add(current)
            for edge in self.graph.get_outgoing_edges(current):
                neighbor = edge.target
                if neighbor not in visited or neighbor == source:
                    if dfs_find_path(neighbor, depth + 1):
                        return True

            path.pop()
            return False

        found = dfs_find_path(target, depth=0)
        if found:
            # Full cycle path is: source -> target -> ... -> source
            full_cycle = [source] + path
            return True, full_cycle

        return False, []

    def find_all_cycles(
        self,
        max_depth: int = 5,
        since_time: Optional[datetime] = None,
    ) -> List[List[str]]:
        """Finds elementary directed cycles in the graph up to max_depth using 3-color DFS.

        Colors:
        0 (WHITE) = unvisited
        1 (GRAY)  = currently on recursion stack
        2 (BLACK) = visited & all descendants processed
        """
        color: Dict[str, int] = {v: 0 for v in self.graph.vertices}
        parent: Dict[str, Optional[str]] = {v: None for v in self.graph.vertices}
        cycles: List[List[str]] = []

        def dfs(u: str, current_path: List[str]) -> None:
            color[u] = 1  # GRAY
            current_path.append(u)

            if len(current_path) <= max_depth:
                for edge in self.graph.get_outgoing_edges(u):
                    if since_time and edge.timestamp < since_time:
                        continue

                    v = edge.target
                    if color.get(v, 0) == 1:
                        # Found back-edge u -> v where v is on the recursion stack!
                        try:
                            start_idx = current_path.index(v)
                            cycle = current_path[start_idx:] + [v]
                            # Avoid duplicates by canonical representation
                            cycles.append(cycle)
                        except ValueError:
                            pass
                    elif color.get(v, 0) == 0:
                        parent[v] = u
                        dfs(v, current_path)

            current_path.pop()
            color[u] = 2  # BLACK

        for vertex in list(self.graph.vertices):
            if color.get(vertex, 0) == 0:
                dfs(vertex, [])

        return cycles
