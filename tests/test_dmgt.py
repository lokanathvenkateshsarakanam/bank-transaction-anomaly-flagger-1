"""Unit Tests for DMGT Components (U1 Propositional Logic, U2 Transaction Relations)."""

import unittest
from dmgt.propositional_engine import (
    And,
    BiConditional,
    Implies,
    Not,
    Or,
    Prop,
    PropositionalFraudRule,
    PropositionalLogicEngine,
)
from dmgt.relations import BinaryRelation, EquivalenceRelation


class TestDMGTPropositionalLogic(unittest.TestCase):
    """Tests DMGT Unit 1 Propositional Logic AST and Rule Engine."""

    def setUp(self) -> None:
        self.p = Prop("P")
        self.q = Prop("Q")
        self.r = Prop("R")

    def test_connectives_basic(self) -> None:
        # Not
        not_p = Not(self.p)
        self.assertFalse(not_p.evaluate({"P": True}))
        self.assertTrue(not_p.evaluate({"P": False}))

        # And
        and_expr = And(self.p, self.q)
        self.assertTrue(and_expr.evaluate({"P": True, "Q": True}))
        self.assertFalse(and_expr.evaluate({"P": True, "Q": False}))

        # Or
        or_expr = Or(self.p, self.q)
        self.assertTrue(or_expr.evaluate({"P": False, "Q": True}))
        self.assertFalse(or_expr.evaluate({"P": False, "Q": False}))

        # Implies (P -> Q)
        imp_expr = Implies(self.p, self.q)
        self.assertTrue(imp_expr.evaluate({"P": False, "Q": False}))  # F -> F is T
        self.assertTrue(imp_expr.evaluate({"P": False, "Q": True}))   # F -> T is T
        self.assertFalse(imp_expr.evaluate({"P": True, "Q": False}))  # T -> F is F
        self.assertTrue(imp_expr.evaluate({"P": True, "Q": True}))    # T -> T is T

        # BiConditional (P <-> Q)
        bicond = BiConditional(self.p, self.q)
        self.assertTrue(bicond.evaluate({"P": True, "Q": True}))
        self.assertTrue(bicond.evaluate({"P": False, "Q": False}))
        self.assertFalse(bicond.evaluate({"P": True, "Q": False}))

    def test_truth_table_generation(self) -> None:
        rule = PropositionalFraudRule(
            rule_id="R_TEST",
            name="Test Rule",
            condition=And(self.p, self.q),
            flag_consequent="FLAG_TEST",
        )
        tt = rule.generate_truth_table()
        # 2 variables => 4 rows
        self.assertEqual(len(tt), 4)
        # Check that only row where P=True and Q=True evaluates to True
        true_rows = [row for row in tt if row["EVALUATION"] is True]
        self.assertEqual(len(true_rows), 1)
        self.assertTrue(true_rows[0]["P"] and true_rows[0]["Q"])

    def test_rule_engine_inference(self) -> None:
        engine = PropositionalLogicEngine()
        rule = PropositionalFraudRule(
            rule_id="R_SUSPICIOUS",
            name="High Amount New Device",
            condition=And(self.p, self.q),
            flag_consequent="SUSPECT_FRAUD",
            base_risk_weight=0.5,
        )
        engine.add_rule(rule)

        # Antecedent is False
        flags, risk, _ = engine.evaluate_all({"P": True, "Q": False})
        self.assertEqual(len(flags), 0)
        self.assertEqual(risk, 0.0)

        # Antecedent is True (Modus Ponens)
        flags, risk, _ = engine.evaluate_all({"P": True, "Q": True})
        self.assertIn("SUSPECT_FRAUD", flags)
        self.assertEqual(risk, 0.5)


class TestDMGTTransactionRelations(unittest.TestCase):
    """Tests DMGT Unit 2 Binary Relations and Equivalence Classes."""

    def test_relation_properties(self) -> None:
        universe = {"acc1", "acc2", "acc3"}
        rel = BinaryRelation[str]("R_test", universe)

        # Add reflexive pairs
        for x in universe:
            rel.add_pair(x, x)

        self.assertTrue(rel.is_reflexive())
        self.assertTrue(rel.is_symmetric())
        self.assertTrue(rel.is_transitive())
        self.assertTrue(rel.is_equivalence_relation())

        # Break symmetry: add (acc1, acc2) without (acc2, acc1)
        rel.add_pair("acc1", "acc2")
        self.assertFalse(rel.is_symmetric())
        self.assertFalse(rel.is_equivalence_relation())

        # Restore symmetry
        rel.add_pair("acc2", "acc1")
        self.assertTrue(rel.is_symmetric())

    def test_equivalence_classes_and_quotient_set(self) -> None:
        accounts = {"A1", "A2", "B1", "B2", "C1"}
        eq_rel = EquivalenceRelation[str]("R_device", accounts)

        # A1 and A2 share device 1
        eq_rel.add_equivalence_link("A1", "A2")
        # B1 and B2 share device 2
        eq_rel.add_equivalence_link("B1", "B2")

        # Equivalence class of A1 should be {A1, A2}
        self.assertEqual(eq_rel.get_equivalence_class("A1"), {"A1", "A2"})
        self.assertEqual(eq_rel.get_equivalence_class("B1"), {"B1", "B2"})
        self.assertEqual(eq_rel.get_equivalence_class("C1"), {"C1"})

        quotient_set = eq_rel.get_quotient_set()
        self.assertEqual(len(quotient_set), 3)

    def test_relation_composition(self) -> None:
        # R: transfers from stage 1 to stage 2
        r = BinaryRelation[str]("R", {"A", "B", "C"})
        r.add_pair("A", "B")

        # S: transfers from stage 2 to stage 3
        s = BinaryRelation[str]("S", {"A", "B", "C"})
        s.add_pair("B", "C")

        # Composition R o S represents 2-hop fund flow from A to C
        comp = r.compose(s)
        self.assertTrue(comp.contains("A", "C"))
        self.assertFalse(comp.contains("A", "B"))

    def test_transitive_closure(self) -> None:
        rel = BinaryRelation[str]("Flow", {"1", "2", "3", "4"})
        rel.add_pair("1", "2")
        rel.add_pair("2", "3")
        rel.add_pair("3", "4")

        closure = rel.compute_transitive_closure()
        self.assertTrue(closure.contains("1", "4"))
        self.assertTrue(closure.contains("1", "3"))


if __name__ == "__main__":
    unittest.main()
