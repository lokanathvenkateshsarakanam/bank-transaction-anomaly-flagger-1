"""Unit Tests for OOPJ Concepts (Encapsulation, Invariants, State Transitions)."""

import unittest
from models.account import Account
from models.transaction import Transaction
from models.types import KYCStatus, TransactionStatus


class TestOOPJConcepts(unittest.TestCase):
    """Tests Object-Oriented Programming (OOPJ) Principles in Domain Models."""

    def test_account_encapsulation_and_invariants(self) -> None:
        acc = Account(
            account_id="ACC_OOP",
            holder_name="Grace Hopper",
            initial_balance=500.0,
            kyc_status=KYCStatus.TIER_2_VERIFIED,
        )

        # Encapsulation test: reading properties
        self.assertEqual(acc.account_id, "ACC_OOP")
        self.assertEqual(acc.balance, 500.0)

        # Deposit method
        acc.deposit(250.0)
        self.assertEqual(acc.balance, 750.0)

        with self.assertRaises(ValueError):
            acc.deposit(-50.0)

        # Withdrawal method & invariant
        success = acc.withdraw(300.0)
        self.assertTrue(success)
        self.assertEqual(acc.balance, 450.0)

        # Overdraw should fail cleanly
        failed = acc.withdraw(1000.0)
        self.assertFalse(failed)
        self.assertEqual(acc.balance, 450.0)

    def test_transaction_lifecycle_transitions(self) -> None:
        txn = Transaction(
            txn_id="TXN_LIFECYCLE",
            sender_id="A1",
            receiver_id="A2",
            amount=150.0,
        )
        self.assertEqual(txn.status, TransactionStatus.PENDING)

        txn.mark_flagged()
        self.assertEqual(txn.status, TransactionStatus.FLAGGED_FOR_REVIEW)

        txn.mark_blocked()
        self.assertEqual(txn.status, TransactionStatus.BLOCKED)

        txn.mark_approved()
        self.assertEqual(txn.status, TransactionStatus.APPROVED)

    def test_account_statistics_update(self) -> None:
        acc = Account("A_STATS", "Alan Turing", initial_balance=100.0, historical_avg_amount=100.0)
        acc.record_transaction(200.0)
        self.assertEqual(acc.transaction_count, 1)
        # Moving average should have shifted upwards
        self.assertGreater(acc.historical_avg_amount, 100.0)


if __name__ == "__main__":
    unittest.main()
