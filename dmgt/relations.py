"""DMGT Unit 2: Transaction Relations & Equivalence Classes.

Implements:
1. BinaryRelation (Mathematical Set of Ordered Pairs (a, b) in A x A).
2. Formal property verifiers: Reflexivity, Symmetry, Anti-Symmetry, Transitivity.
3. EquivalenceRelation and Equivalence Class Partitioning (A / R)
   (e.g., Accounts sharing Device / IP / National ID for synthetic identity detection).
4. Composition of Relations (R o S) for multi-hop fund flow analysis.
5. Transitive Closure (Warshall / Reachability).
"""

from collections import defaultdict
from typing import Dict, Generic, List, Set, Tuple, TypeVar

T = TypeVar("T")


class BinaryRelation(Generic[T]):
    """Represents a mathematical binary relation R subseteq A x A over a universe set A."""

    def __init__(self, name: str, domain: Set[T]) -> None:
        self.name = name
        self.domain: Set[T] = set(domain)
        self.pairs: Set[Tuple[T, T]] = set()

    def add_pair(self, a: T, b: T) -> None:
        """Adds ordered pair (a, b) to relation R."""
        self.domain.add(a)
        self.domain.add(b)
        self.pairs.add((a, b))

    def contains(self, a: T, b: T) -> bool:
        """Checks if (a, b) in R."""
        return (a, b) in self.pairs

    def is_reflexive(self) -> bool:
        """Tests reflexivity: forall x in A, (x, x) in R."""
        return all((x, x) in self.pairs for x in self.domain)

    def is_symmetric(self) -> bool:
        """Tests symmetry: forall x, y in A, (x, y) in R => (y, x) in R."""
        return all((y, x) in self.pairs for (x, y) in self.pairs)

    def is_antisymmetric(self) -> bool:
        """Tests antisymmetry: forall x, y in A, (x, y) in R and (y, x) in R => x == y."""
        for (x, y) in self.pairs:
            if (y, x) in self.pairs and x != y:
                return False
        return True

    def is_transitive(self) -> bool:
        """Tests transitivity: forall x, y, z in A, (x, y) in R and (y, z) in R => (x, z) in R."""
        for (x, y1) in self.pairs:
            for (y2, z) in self.pairs:
                if y1 == y2 and (x, z) not in self.pairs:
                    return False
        return True

    def is_equivalence_relation(self) -> bool:
        """Returns True iff R is Reflexive, Symmetric, and Transitive."""
        return self.is_reflexive() and self.is_symmetric() and self.is_transitive()

    def compose(self, other: "BinaryRelation[T]", result_name: str = "") -> "BinaryRelation[T]":
        """Computes relational composition (R o S):

        (x, z) in R o S <=> exists y such that (x, y) in R and (y, z) in S.
        """
        combined_domain = self.domain.union(other.domain)
        res = BinaryRelation[T](result_name or f"({self.name} ∘ {other.name})", combined_domain)

        # Build lookup table for other relation: y -> set of z
        y_to_z = defaultdict(set)
        for (y, z) in other.pairs:
            y_to_z[y].add(z)

        for (x, y) in self.pairs:
            if y in y_to_z:
                for z in y_to_z[y]:
                    res.add_pair(x, z)

        return res

    def compute_transitive_closure(self) -> "BinaryRelation[T]":
        """Computes transitive closure R+ using Warshall's algorithm."""
        elements = list(self.domain)
        n = len(elements)
        elem_to_idx = {elem: i for i, elem in enumerate(elements)}

        # Adjacency matrix
        adj = [[False] * n for _ in range(n)]
        for (u, v) in self.pairs:
            if u in elem_to_idx and v in elem_to_idx:
                adj[elem_to_idx[u]][elem_to_idx[v]] = True

        # Warshall's algorithm
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    adj[i][j] = adj[i][j] or (adj[i][k] and adj[k][j])

        closure = BinaryRelation[T](f"{self.name}^+", self.domain)
        for i in range(n):
            for j in range(n):
                if adj[i][j]:
                    closure.add_pair(elements[i], elements[j])

        return closure

    def __repr__(self) -> str:
        return f"Relation({self.name}, |Domain|={len(self.domain)}, |Pairs|={len(self.pairs)})"


class EquivalenceRelation(BinaryRelation[T]):
    """Specialized Equivalence Relation supporting Quotient Set & Equivalence Class extraction."""

    def __init__(self, name: str, domain: Set[T]) -> None:
        super().__init__(name, domain)
        # Automatically ensure reflexivity for all elements in domain
        for x in domain:
            self.pairs.add((x, x))

    def add_equivalence_link(self, a: T, b: T) -> None:
        """Adds equivalence between a and b, maintaining reflexivity and symmetry."""
        self.domain.add(a)
        self.domain.add(b)
        self.pairs.add((a, a))
        self.pairs.add((b, b))
        self.pairs.add((a, b))
        self.pairs.add((b, a))

    def get_equivalence_class(self, element: T) -> Set[T]:
        """Returns the equivalence class [x] = { y in A | (x, y) in R }."""
        # Using Disjoint Set / Connected Component search over symmetric pairs
        eq_class: Set[T] = set()
        visited: Set[T] = set()
        queue = [element]

        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            eq_class.add(curr)
            for (u, v) in self.pairs:
                if u == curr and v not in visited:
                    queue.append(v)
                elif v == curr and u not in visited:
                    queue.append(u)

        return eq_class

    def get_quotient_set(self) -> List[Set[T]]:
        """Returns the quotient set A / R, which is the partition of A into disjoint equivalence classes."""
        partition: List[Set[T]] = []
        covered: Set[T] = set()

        for item in self.domain:
            if item not in covered:
                eq_cls = self.get_equivalence_class(item)
                partition.append(eq_cls)
                covered.update(eq_cls)

        return partition


class AccountIdentityRelationManager:
    """Manages bank account equivalence relations over shared identifiers (Device, IP, SSN).

    DMGT Unit 2 Application:
    Partition accounts into equivalence classes. If any account in an equivalence class
    is compromised or fraudulent, all related accounts inherit high scrutiny.
    """

    def __init__(self) -> None:
        self.device_relation = EquivalenceRelation[str]("R_device", set())
        self.ip_relation = EquivalenceRelation[str]("R_ip", set())
        self.national_id_relation = EquivalenceRelation[str]("R_national_id", set())

    def register_account_attributes(
        self,
        account_id: str,
        device_id: str,
        ip_address: str,
        national_id: str,
        existing_accounts_map: Dict[str, any],
    ) -> None:
        """Updates equivalence relations between accounts based on shared markers."""
        # Link accounts that share the same device
        if device_id:
            for acc_id, acc in existing_accounts_map.items():
                if acc.device_fingerprint == device_id and acc_id != account_id:
                    self.device_relation.add_equivalence_link(account_id, acc_id)

        # Link accounts sharing same IP
        if ip_address:
            for acc_id, acc in existing_accounts_map.items():
                if acc.ip_address == ip_address and acc_id != account_id:
                    self.ip_relation.add_equivalence_link(account_id, acc_id)

        # Link accounts sharing national ID (synthetic identities or multi-account fraud)
        if national_id:
            for acc_id, acc in existing_accounts_map.items():
                if acc.national_id == national_id and acc_id != account_id:
                    self.national_id_relation.add_equivalence_link(account_id, acc_id)

    def get_linked_accounts(self, account_id: str) -> Set[str]:
        """Returns all accounts related to this account via Device, IP, or National ID."""
        linked = set()
        linked.update(self.device_relation.get_equivalence_class(account_id))
        linked.update(self.ip_relation.get_equivalence_class(account_id))
        linked.update(self.national_id_relation.get_equivalence_class(account_id))
        linked.discard(account_id)
        return linked
