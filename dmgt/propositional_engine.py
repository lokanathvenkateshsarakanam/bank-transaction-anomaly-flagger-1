"""DMGT Unit 1: Propositional-Logic Rule Engine.

Implements:
1. Formal Propositional Logic AST (Atomic Propositions, Connectives: NOT, AND, OR, IMPLIES, BICONDITIONAL).
2. Well-Formed Formula (WFF) Evaluation over Boolean Truth Assignments.
3. Modus Ponens Inference Engine for Fraud Detection Rules.
4. Truth Table Generation for Formal Rule Verification.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Set, Tuple


class Expression(ABC):
    """Abstract Base Class for a Propositional Logic Well-Formed Formula (WFF)."""

    @abstractmethod
    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        """Evaluates formula truth value under a given variable assignment."""
        pass

    @abstractmethod
    def get_variables(self) -> Set[str]:
        """Returns set of all atomic proposition identifiers in formula."""
        pass

    @abstractmethod
    def to_formal_string(self) -> str:
        """Returns mathematical notation using standard logic symbols (¬, ∧, ∨, →, ↔)."""
        pass

    def __repr__(self) -> str:
        return self.to_formal_string()


class Prop(Expression):
    """Atomic Proposition (Variable): Represents a binary predicate test on a transaction."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        if self.name not in assignment:
            raise KeyError(f"Proposition '{self.name}' not bound in truth assignment.")
        return bool(assignment[self.name])

    def get_variables(self) -> Set[str]:
        return {self.name}

    def to_formal_string(self) -> str:
        return self.name


class Not(Expression):
    """Unary Negation Connective: ¬P."""

    def __init__(self, child: Expression) -> None:
        self.child = child

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        return not self.child.evaluate(assignment)

    def get_variables(self) -> Set[str]:
        return self.child.get_variables()

    def to_formal_string(self) -> str:
        return f"¬({self.child.to_formal_string()})"


class And(Expression):
    """N-ary Conjunction Connective: P ∧ Q ∧ ..."""

    def __init__(self, *children: Expression) -> None:
        if len(children) < 1:
            raise ValueError("And operator requires at least 1 operand.")
        self.children = list(children)

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        return all(c.evaluate(assignment) for c in self.children)

    def get_variables(self) -> Set[str]:
        vars_set: Set[str] = set()
        for c in self.children:
            vars_set.update(c.get_variables())
        return vars_set

    def to_formal_string(self) -> str:
        return "(" + " ∧ ".join(c.to_formal_string() for c in self.children) + ")"


class Or(Expression):
    """N-ary Disjunction Connective: P ∨ Q ∨ ..."""

    def __init__(self, *children: Expression) -> None:
        if len(children) < 1:
            raise ValueError("Or operator requires at least 1 operand.")
        self.children = list(children)

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        return any(c.evaluate(assignment) for c in self.children)

    def get_variables(self) -> Set[str]:
        vars_set: Set[str] = set()
        for c in self.children:
            vars_set.update(c.get_variables())
        return vars_set

    def to_formal_string(self) -> str:
        return "(" + " ∨ ".join(c.to_formal_string() for c in self.children) + ")"


class Implies(Expression):
    """Conditional / Implication Connective: P → Q (Equivalent to ¬P ∨ Q)."""

    def __init__(self, antecedent: Expression, consequent: Expression) -> None:
        self.antecedent = antecedent
        self.consequent = consequent

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        # P -> Q is false only if P is True and Q is False
        p = self.antecedent.evaluate(assignment)
        q = self.consequent.evaluate(assignment)
        return (not p) or q

    def get_variables(self) -> Set[str]:
        return self.antecedent.get_variables().union(self.consequent.get_variables())

    def to_formal_string(self) -> str:
        return f"({self.antecedent.to_formal_string()} → {self.consequent.to_formal_string()})"


class BiConditional(Expression):
    """Biconditional Connective: P ↔ Q."""

    def __init__(self, left: Expression, right: Expression) -> None:
        self.left = left
        self.right = right

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        return self.left.evaluate(assignment) == self.right.evaluate(assignment)

    def get_variables(self) -> Set[str]:
        return self.left.get_variables().union(self.right.get_variables())

    def to_formal_string(self) -> str:
        return f"({self.left.to_formal_string()} ↔ {self.right.to_formal_string()})"


class PropositionalFraudRule:
    """Represents a bank fraud rule expressed as a formal implication: Condition -> Flag."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        condition: Expression,
        flag_consequent: str,
        base_risk_weight: float = 0.5,
        description: str = "",
    ) -> None:
        self.rule_id = rule_id
        self.name = name
        self.condition = condition
        self.flag_consequent = flag_consequent
        self.base_risk_weight = base_risk_weight
        self.description = description

    def evaluate_rule(self, assignment: Dict[str, bool]) -> Tuple[bool, str]:
        """Applies Modus Ponens:

        If condition evaluates to True, the rule fires and yields the consequent flag.
        Returns: (fired, reasoning_trace)
        """
        is_triggered = self.condition.evaluate(assignment)
        formula_str = self.condition.to_formal_string()
        if is_triggered:
            trace = f"[{self.rule_id}] FIRED: Condition {formula_str} evaluated to TRUE => Flag: '{self.flag_consequent}'"
        else:
            trace = f"[{self.rule_id}] PASS: Condition {formula_str} evaluated to FALSE."
        return is_triggered, trace

    def generate_truth_table(self) -> List[Dict[str, any]]:
        """Generates formal truth table rows across all combinations of atomic propositions."""
        variables = sorted(list(self.condition.get_variables()))
        n = len(variables)
        table = []
        for i in range(1 << n):
            assignment = {}
            for j, var in enumerate(variables):
                # Using bit manipulation to generate truth assignments
                assignment[var] = bool((i >> (n - 1 - j)) & 1)
            result = self.condition.evaluate(assignment)
            row = dict(assignment)
            row["EVALUATION"] = result
            table.append(row)
        return table


class PropositionalLogicEngine:
    """DMGT Unit 1 Rule Engine managing rule definitions and transaction truth evaluation."""

    def __init__(self) -> None:
        self.rules: List[PropositionalFraudRule] = []

    def add_rule(self, rule: PropositionalFraudRule) -> None:
        self.rules.append(rule)

    def evaluate_all(self, assignment: Dict[str, bool]) -> Tuple[List[str], float, List[str]]:
        """Evaluates all rules against current atomic proposition assignment.

        Returns:
            - List of fired flag consequences
            - Aggregated rule risk score increment
            - Audit trail of logical deduction
        """
        fired_flags: List[str] = []
        total_risk = 0.0
        traces: List[str] = []

        for rule in self.rules:
            fired, trace = rule.evaluate_rule(assignment)
            traces.append(trace)
            if fired:
                fired_flags.append(rule.flag_consequent)
                total_risk += rule.base_risk_weight

        # Normalize or cap risk increment to [0.0, 1.0]
        bounded_risk = min(1.0, total_risk)
        return fired_flags, bounded_risk, traces
