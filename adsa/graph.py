"""ADSA Unit 2: Transaction Network as a Directed Weighted Graph.

Represents accounts as vertices and transactions as directed edges with
weights (amount), timestamps, and transaction metadata.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set


@dataclass
class Edge:
    """Directed edge representing a transaction from sender to receiver."""
    edge_id: str
    source: str
    target: str
    amount: float
    timestamp: datetime
    metadata: Dict[str, any]

    def __repr__(self) -> str:
        return f"Edge({self.source} -> {self.target}, ${self.amount:.2f}, {self.timestamp.strftime('%H:%M:%S')})"


class TransactionGraph:
    """Directed Graph implementation using Adjacency Lists (ADSA U2).

    Supports dynamic insertion, degree queries, neighborhood extraction,
    and temporal edge filtering.
    """

    def __init__(self) -> None:
        # Adjacency list: node_id -> list of outgoing edges
        self._adj_out: Dict[str, List[Edge]] = defaultdict(list)
        # Reverse adjacency list: node_id -> list of incoming edges
        self._adj_in: Dict[str, List[Edge]] = defaultdict(list)
        # Set of all vertices
        self._vertices: Set[str] = set()

    def add_vertex(self, node_id: str) -> None:
        """Adds vertex to graph if not present."""
        self._vertices.add(node_id)
        if node_id not in self._adj_out:
            self._adj_out[node_id] = []
        if node_id not in self._adj_in:
            self._adj_in[node_id] = []

    def add_transaction_edge(
        self,
        edge_id: str,
        source: str,
        target: str,
        amount: float,
        timestamp: Optional[datetime] = None,
        **metadata,
    ) -> Edge:
        """Adds a directed transaction edge (source -> target)."""
        self.add_vertex(source)
        self.add_vertex(target)

        t_edge = Edge(
            edge_id=edge_id,
            source=source,
            target=target,
            amount=amount,
            timestamp=timestamp or datetime.now(),
            metadata=metadata,
        )

        self._adj_out[source].append(t_edge)
        self._adj_in[target].append(t_edge)
        return t_edge

    @property
    def vertices(self) -> Set[str]:
        return set(self._vertices)

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        return list(self._adj_out.get(node_id, []))

    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        return list(self._adj_in.get(node_id, []))

    def in_degree(self, node_id: str) -> int:
        """Number of incoming transactions."""
        return len(self._adj_in.get(node_id, []))

    def out_degree(self, node_id: str) -> int:
        """Number of outgoing transactions."""
        return len(self._adj_out.get(node_id, []))

    def get_total_inflow(self, node_id: str) -> float:
        """Sums total volume transferred into node."""
        return sum(e.amount for e in self._adj_in.get(node_id, []))

    def get_total_outflow(self, node_id: str) -> float:
        """Sums total volume transferred out of node."""
        return sum(e.amount for e in self._adj_out.get(node_id, []))

    def get_neighbors_out(self, node_id: str) -> Set[str]:
        """Set of target accounts directly receiving funds from node."""
        return {e.target for e in self._adj_out.get(node_id, [])}

    def get_neighbors_in(self, node_id: str) -> Set[str]:
        """Set of source accounts directly sending funds to node."""
        return {e.source for e in self._adj_in.get(node_id, [])}

    def __repr__(self) -> str:
        total_edges = sum(len(edges) for edges in self._adj_out.values())
        return f"TransactionGraph(|V|={len(self._vertices)}, |E|={total_edges})"
