"""ADSA Unit 2: Flow & Centrality Anomaly Analyzer.

Detects:
1. Smurfing / Structuring patterns (Fan-In / Fan-Out velocity anomalies).
2. Money Mule Pass-Through (rapid turnover where inflow ≈ outflow).
3. Graph Proximity / Shortest Path to Blacklisted Entities via Breadth-First Search (BFS).
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from adsa.graph import Edge, TransactionGraph


class GraphFlowAnalyzer:
    """Analyzes graph topology, flow dynamics, and proximity risks (ADSA U2)."""

    def __init__(self, graph: TransactionGraph) -> None:
        self.graph = graph

    def detect_fan_in_anomaly(
        self,
        node_id: str,
        in_degree_threshold: int = 3,
        window_minutes: float = 60.0,
        current_time: Optional[datetime] = None,
    ) -> Tuple[bool, int, float]:
        """Detects structuring / smurfing fan-in pattern:

        Many different source accounts depositing into a single collector account within a short window.
        Returns: (is_anomaly, distinct_senders_count, total_amount)
        """
        now = current_time or datetime.now()
        threshold_time = now - timedelta(minutes=window_minutes)

        incoming = self.graph.get_incoming_edges(node_id)
        recent_incoming = [e for e in incoming if e.timestamp >= threshold_time]

        unique_senders = {e.source for e in recent_incoming}
        total_amount = sum(e.amount for e in recent_incoming)

        is_anomaly = len(unique_senders) >= in_degree_threshold
        return is_anomaly, len(unique_senders), total_amount

    def detect_mule_pass_through(
        self,
        node_id: str,
        balance_tolerance_ratio: float = 0.2,
        window_hours: float = 24.0,
        current_time: Optional[datetime] = None,
    ) -> Tuple[bool, float, float]:
        """Detects Money Mule behavior:

        An account receives funds and immediately disperses almost the entire amount (low retention).
        Returns: (is_mule_suspect, inflow, outflow)
        """
        now = current_time or datetime.now()
        threshold_time = now - timedelta(hours=window_hours)

        incoming = [e for e in self.graph.get_incoming_edges(node_id) if e.timestamp >= threshold_time]
        outgoing = [e for e in self.graph.get_outgoing_edges(node_id) if e.timestamp >= threshold_time]

        inflow = sum(e.amount for e in incoming)
        outflow = sum(e.amount for e in outgoing)

        if inflow < 500.0 or outflow < 500.0:
            return False, inflow, outflow

        # If outflow is very close to inflow: abs(inflow - outflow) / inflow <= tolerance
        diff_ratio = abs(inflow - outflow) / max(inflow, outflow)
        is_mule = diff_ratio <= balance_tolerance_ratio and len(incoming) >= 1 and len(outgoing) >= 1

        return is_mule, inflow, outflow

    def shortest_path_to_blacklisted(
        self,
        start_node: str,
        blacklisted_nodes: Set[str],
        max_hops: int = 3,
    ) -> Tuple[Optional[int], List[str]]:
        """Computes shortest directed/undirected path to any blacklisted node via BFS.

        Returns: (hop_distance, path_nodes) or (None, [])
        """
        if start_node in blacklisted_nodes:
            return 0, [start_node]

        visited: Set[str] = {start_node}
        queue: deque[Tuple[str, List[str], int]] = deque([(start_node, [start_node], 0)])

        while queue:
            curr, path, hops = queue.popleft()

            if hops >= max_hops:
                continue

            # Check neighbors both forward and backward in transaction network
            neighbors = self.graph.get_neighbors_out(curr).union(self.graph.get_neighbors_in(curr))
            for nbr in neighbors:
                if nbr in blacklisted_nodes:
                    return hops + 1, path + [nbr]

                if nbr not in visited:
                    visited.add(nbr)
                    queue.append((nbr, path + [nbr], hops + 1))

        return None, []
