"""Unit Tests for ADSA Components (Graph, Cycle Detection, Flow Analyzer)."""

from datetime import datetime, timedelta
import unittest
from adsa.cycle_detector import CycleDetector
from adsa.flow_analyzer import GraphFlowAnalyzer
from adsa.graph import TransactionGraph


class TestADSAGraphAlgorithms(unittest.TestCase):
    """Tests ADSA Unit 2 Transaction Network Directed Graph and Graph Algorithms."""

    def setUp(self) -> None:
        self.graph = TransactionGraph()
        self.detector = CycleDetector(self.graph)
        self.analyzer = GraphFlowAnalyzer(self.graph)

    def test_graph_construction_and_degrees(self) -> None:
        self.graph.add_transaction_edge("TX1", "NodeA", "NodeB", 100.0)
        self.graph.add_transaction_edge("TX2", "NodeA", "NodeC", 200.0)

        self.assertEqual(self.graph.out_degree("NodeA"), 2)
        self.assertEqual(self.graph.in_degree("NodeA"), 0)
        self.assertEqual(self.graph.in_degree("NodeB"), 1)
        self.assertEqual(self.graph.get_total_outflow("NodeA"), 300.0)
        self.assertEqual(self.graph.get_total_inflow("NodeB"), 100.0)

    def test_cycle_detection(self) -> None:
        # Build DAG: A -> B -> C
        self.graph.add_transaction_edge("TX1", "A", "B", 500.0)
        self.graph.add_transaction_edge("TX2", "B", "C", 500.0)

        # Checking edge C -> D should NOT create a cycle
        has_cycle, _ = self.detector.check_if_edge_creates_cycle("C", "D")
        self.assertFalse(has_cycle)

        # Adding edge C -> A SHOULD complete directed cycle A -> B -> C -> A
        has_cycle, path = self.detector.check_if_edge_creates_cycle("C", "A")
        self.assertTrue(has_cycle)
        self.assertIn("A", path)
        self.assertIn("B", path)
        self.assertIn("C", path)

    def test_smurfing_fan_in_detection(self) -> None:
        now = datetime.now()
        # 3 distinct mules deposit into Collector within 10 minutes
        self.graph.add_transaction_edge("T1", "Mule1", "Collector", 9500.0, now - timedelta(minutes=5))
        self.graph.add_transaction_edge("T2", "Mule2", "Collector", 9500.0, now - timedelta(minutes=4))
        self.graph.add_transaction_edge("T3", "Mule3", "Collector", 9500.0, now - timedelta(minutes=2))

        is_anom, count, total = self.analyzer.detect_fan_in_anomaly("Collector", in_degree_threshold=3, window_minutes=60.0, current_time=now)
        self.assertTrue(is_anom)
        self.assertEqual(count, 3)
        self.assertEqual(total, 28500.0)

    def test_bfs_shortest_path_to_blacklisted(self) -> None:
        # A -> B -> C -> Blacklisted
        self.graph.add_transaction_edge("T1", "A", "B", 100.0)
        self.graph.add_transaction_edge("T2", "B", "C", 100.0)
        self.graph.add_transaction_edge("T3", "C", "FRAUD_HUB", 100.0)

        blacklisted = {"FRAUD_HUB"}
        hops, path = self.analyzer.shortest_path_to_blacklisted("A", blacklisted, max_hops=3)
        self.assertEqual(hops, 3)
        self.assertEqual(path, ["A", "B", "C", "FRAUD_HUB"])

        hops_b, _ = self.analyzer.shortest_path_to_blacklisted("B", blacklisted, max_hops=3)
        self.assertEqual(hops_b, 2)


if __name__ == "__main__":
    unittest.main()
