"""Unit Tests for AI Components (Unit 1 Rational Agent & Decision Rules)."""

import unittest
from adsa.graph import TransactionGraph
from ai.agent import DecisionOutcome, RationalFraudScreeningAgent
from dmgt.propositional_engine import PropositionalLogicEngine
from dmgt.relations import AccountIdentityRelationManager
from models.account import Account
from models.transaction import Transaction
from models.types import ActionType, KYCStatus, RiskTier


class TestAIRationalAgent(unittest.TestCase):
    """Tests AI Unit 1 Rational Agent Architecture and Expected Utility Payoffs."""

    def setUp(self) -> None:
        self.logic = PropositionalLogicEngine()
        self.graph = TransactionGraph()
        self.rel = AccountIdentityRelationManager()
        self.agent = RationalFraudScreeningAgent(
            logic_engine=self.logic,
            graph=self.graph,
            relation_manager=self.rel,
            review_cost=25.0,
        )

        self.sender = Account("ACC1", "Sender", 1000.0, KYCStatus.TIER_2_VERIFIED)
        self.receiver = Account("ACC2", "Receiver", 1000.0, KYCStatus.TIER_2_VERIFIED)

    def test_expected_utility_low_risk(self) -> None:
        # For small amount and very low fraud probability (e.g. 0.01)
        utilities = self.agent.evaluate_expected_utility(p_fraud=0.01, amount=100.0)

        # APPROVE should have highest expected utility
        self.assertGreater(utilities[ActionType.APPROVE], utilities[ActionType.FLAG_MANUAL_REVIEW])
        self.assertGreater(utilities[ActionType.APPROVE], utilities[ActionType.FREEZE_ACCOUNT])

    def test_expected_utility_high_risk(self) -> None:
        # For substantial amount and high fraud probability (e.g. 0.90)
        utilities = self.agent.evaluate_expected_utility(p_fraud=0.90, amount=5000.0)

        # APPROVE should have severe negative utility (bank loses $5,000)
        self.assertLess(utilities[ActionType.APPROVE], 0.0)
        # FREEZE should be the highest utility
        self.assertGreater(utilities[ActionType.FREEZE_ACCOUNT], utilities[ActionType.APPROVE])

    def test_agent_decide_approval(self) -> None:
        txn = Transaction(
            txn_id="TX_LOW",
            sender_id="ACC1",
            receiver_id="ACC2",
            amount=50.0,
        )
        decision = self.agent.decide(txn, self.sender, self.receiver)
        self.assertEqual(decision.action, ActionType.APPROVE)
        self.assertEqual(decision.risk_tier, RiskTier.LOW)

    def test_agent_decide_blacklist_freeze(self) -> None:
        self.agent.add_to_blacklist("ACC1")
        txn = Transaction(
            txn_id="TX_FRAUD",
            sender_id="ACC1",
            receiver_id="ACC2",
            amount=3000.0,
        )
        decision = self.agent.decide(txn, self.sender, self.receiver)
        self.assertEqual(decision.action, ActionType.FREEZE_ACCOUNT)
        self.assertIn("SENDER_IN_FRAUD_BLACKLIST", decision.fired_rules)


if __name__ == "__main__":
    unittest.main()
