"""Unit Tests for Snowflake Framework Integration (Snowflake ID & Snowflake Warehouse)."""

from datetime import datetime
import unittest
from ai.agent import DecisionOutcome
from models.account import Account
from models.transaction import Transaction
from models.types import ActionType, KYCStatus, RiskTier
from snowflake_integration.snowflake_id import DecodedSnowflake, SnowflakeIdGenerator
from snowflake_integration.snowflake_warehouse import SnowflakeWarehouseConnector


class TestSnowflakeFramework(unittest.TestCase):
    """Tests Twitter Snowflake Distributed 64-bit ID generation and Snowflake Warehouse DDL/Ingestion."""

    def test_snowflake_id_generation_properties(self) -> None:
        generator = SnowflakeIdGenerator(datacenter_id=3, worker_id=7)
        raw_id = generator.generate_id()

        # 64-bit positive integer
        self.assertIsInstance(raw_id, int)
        self.assertGreater(raw_id, 0)

        # Decode ID into constituent components
        decoded: DecodedSnowflake = generator.decode_id(raw_id)
        self.assertEqual(decoded.datacenter_id, 3)
        self.assertEqual(decoded.worker_id, 7)
        self.assertGreater(decoded.timestamp_ms, 0)
        self.assertIsInstance(decoded.datetime_utc, datetime)

    def test_snowflake_uniqueness_and_monotonicity(self) -> None:
        generator = SnowflakeIdGenerator(datacenter_id=1, worker_id=1)
        generated_ids = [generator.generate_id() for _ in range(500)]

        # All 500 IDs must be strictly unique (collision-free)
        self.assertEqual(len(set(generated_ids)), 500)

        # IDs must be strictly monotonically increasing (k-sorted)
        for i in range(len(generated_ids) - 1):
            self.assertLess(generated_ids[i], generated_ids[i + 1])

    def test_snowflake_warehouse_ingestion_and_query(self) -> None:
        warehouse = SnowflakeWarehouseConnector(db_path=":memory:")

        # 1. Sync Account dimension
        acc = Account("ACC_TEST_SNOW", "Snow Tester", 10000.0, KYCStatus.TIER_2_VERIFIED)
        warehouse.sync_account(acc)

        # 2. Record Screened Transaction into FACT_TRANSACTIONS
        txn = Transaction(
            txn_id="TXN_SNOW_TEST_001",
            sender_id="ACC_TEST_SNOW",
            receiver_id="ACC_BOB",
            amount=500.0,
        )
        decision = DecisionOutcome(
            action=ActionType.APPROVE,
            risk_tier=RiskTier.LOW,
            posterior_fraud_probability=0.02,
            expected_utilities={ActionType.APPROVE: 5.0, ActionType.FLAG_MANUAL_REVIEW: -20.0},
            fired_rules=[],
            audit_trail=["[Test Trace] Everything clean."],
        )
        warehouse.record_screened_transaction(txn, decision)

        # 3. Query transactions
        records = warehouse.query_recent_transactions(limit=10)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["SNOWFLAKE_TXN_ID"], "TXN_SNOW_TEST_001")
        self.assertEqual(records[0]["ACTION_DECISION"], "APPROVE")

        # 4. Query audit traces
        traces = warehouse.query_audit_traces("TXN_SNOW_TEST_001")
        self.assertEqual(len(traces), 1)
        self.assertIn("[Test Trace]", traces[0])

        # 5. Query aggregate metrics
        stats = warehouse.get_summary_statistics()
        self.assertEqual(stats["total_transactions"], 1)
        self.assertEqual(stats["total_volume"], 500.0)


if __name__ == "__main__":
    unittest.main()
