"""Benchmark Simulation Scenarios for Bank Transaction Anomaly Flagger.

Instantiates accounts, default propositional rules, and creates simulated transaction streams
testing every curriculum requirement:
- DMGT U1: Propositional Logic Modus Ponens
- DMGT U2: Equivalence Relations & Identity Clusters
- ADSA U2: Circular Money-Laundering Cycles & Smurfing Fan-In
- AI U1: Rational Agent Utility-Optimizing Decisions
- OOPJ: Encapsulated Account/Transaction Object Graph
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from adsa.graph import TransactionGraph
from ai.agent import DecisionOutcome, RationalFraudScreeningAgent
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
from dmgt.relations import AccountIdentityRelationManager
from models.account import Account
from models.transaction import Transaction
from models.types import ChannelType, KYCStatus


def build_default_propositional_engine() -> PropositionalLogicEngine:
    """Configures DMGT Unit 1 Propositional Logic Rules."""
    engine = PropositionalLogicEngine()

    p_high = Prop("P_HIGH_AMOUNT", "Amount exceeds 3x baseline")
    p_dev = Prop("P_NEW_DEVICE", "Unrecognized device fingerprint")
    p_off = Prop("P_OFF_HOURS", "Transaction between 1 AM and 5 AM")
    p_foreign = Prop("P_FOREIGN_LOCATION", "Transaction originating from abroad")
    p_new_acc = Prop("P_NEW_ACCOUNT", "Account created within 14 days")
    p_unverified = Prop("P_UNVERIFIED_KYC", "Unverified Tier 1 KYC status")

    # Rule 1: Account Takeover (ATO)
    # (P_HIGH_AMOUNT ∧ P_NEW_DEVICE) -> FLAG_ACCOUNT_TAKEOVER
    rule_ato = PropositionalFraudRule(
        rule_id="RULE_ATO_01",
        name="Account Takeover Detection",
        condition=And(p_high, p_dev),
        flag_consequent="SUSPECT_ACCOUNT_TAKEOVER",
        base_risk_weight=0.60,
        description="High amount transferred from a completely new device.",
    )

    # Rule 2: High Risk Onboarding Fraud
    # (P_NEW_ACCOUNT ∧ P_UNVERIFIED_KYC ∧ P_HIGH_AMOUNT) -> FLAG_ONBOARDING_FRAUD
    rule_onboarding = PropositionalFraudRule(
        rule_id="RULE_ONB_02",
        name="High Risk New Account Burst",
        condition=And(p_new_acc, p_unverified, p_high),
        flag_consequent="SUSPECT_SYNTHETIC_ONBOARDING",
        base_risk_weight=0.75,
        description="Fresh unverified account immediately executing huge outflow.",
    )

    # Rule 3: Midnight High-Risk Flight
    # (P_OFF_HOURS ∧ (P_FOREIGN_LOCATION ∨ P_NEW_DEVICE)) -> FLAG_OFF_HOURS_ANOMALY
    rule_off_hours = PropositionalFraudRule(
        rule_id="RULE_OFF_03",
        name="Off-Hours Anomalous Location/Device",
        condition=And(p_off, Or(p_foreign, p_dev)),
        flag_consequent="SUSPECT_OFF_HOURS_EXFILTRATION",
        base_risk_weight=0.45,
        description="Transactions during sleep hours from foreign location or new device.",
    )

    engine.add_rule(rule_ato)
    engine.add_rule(rule_onboarding)
    engine.add_rule(rule_off_hours)

    return engine


class BankingSimulator:
    """Manages bank state and executes benchmark fraud screening scenarios."""

    def __init__(self) -> None:
        self.accounts: Dict[str, Account] = {}
        self.graph = TransactionGraph()
        self.relation_mgr = AccountIdentityRelationManager()
        self.logic_engine = build_default_propositional_engine()
        self.agent = RationalFraudScreeningAgent(
            logic_engine=self.logic_engine,
            graph=self.graph,
            relation_manager=self.relation_mgr,
        )
        self._setup_initial_state()

    def _setup_initial_state(self) -> None:
        """Seeds initial accounts, relations, and prior transaction history."""
        # 1. Benign accounts
        alice = Account(
            account_id="ACC_ALICE",
            holder_name="Alice Smith",
            initial_balance=5000.0,
            kyc_status=KYCStatus.TIER_2_VERIFIED,
            created_at=datetime.now() - timedelta(days=200),
            device_fingerprint="DEV_ALICE_PHONE",
            ip_address="192.168.1.10",
            national_id="SSN_1111",
            historical_avg_amount=60.0,
        )
        bob = Account(
            account_id="ACC_BOB",
            holder_name="Bob Jones",
            initial_balance=3000.0,
            kyc_status=KYCStatus.TIER_2_VERIFIED,
            created_at=datetime.now() - timedelta(days=150),
            device_fingerprint="DEV_BOB_LAPTOP",
            ip_address="192.168.1.20",
            national_id="SSN_2222",
            historical_avg_amount=100.0,
        )

        # 2. Account Takeover victim
        charlie = Account(
            account_id="ACC_CHARLIE",
            holder_name="Charlie Brown",
            initial_balance=12000.0,
            kyc_status=KYCStatus.TIER_2_VERIFIED,
            created_at=datetime.now() - timedelta(days=365),
            device_fingerprint="DEV_CHARLIE_TRUSTED",
            ip_address="10.0.0.5",
            national_id="SSN_3333",
            historical_avg_amount=75.0,
        )

        # 3. Known blacklisted fraudster and puppet linked account (DMGT U2 Equivalence Class)
        mallory = Account(
            account_id="ACC_MALLORY_FRAUD",
            holder_name="Mallory Dark",
            initial_balance=100.0,
            kyc_status=KYCStatus.TIER_1_UNVERIFIED,
            created_at=datetime.now() - timedelta(days=10),
            device_fingerprint="DEV_DARK_NET_01",
            ip_address="185.220.101.5",
            national_id="SSN_6666_FAKE",
            is_blacklisted=True,
        )
        puppet = Account(
            account_id="ACC_PUPPET_CLEAN",
            holder_name="Puppet Clean Name",
            initial_balance=3500.0,
            kyc_status=KYCStatus.TIER_2_VERIFIED,
            created_at=datetime.now() - timedelta(days=40),
            device_fingerprint="DEV_DARK_NET_01",  # Same device as blacklisted Mallory!
            ip_address="185.220.101.5",
            national_id="SSN_7777_CLEAN",
            historical_avg_amount=150.0,
        )

        # 4. Circular layering accounts (Cycle A -> B -> C -> A)
        layer_a = Account("ACC_LAYER_A", "Shell Corp Alpha", 20000.0, KYCStatus.TIER_2_VERIFIED)
        layer_b = Account("ACC_LAYER_B", "Shell Corp Beta", 20000.0, KYCStatus.TIER_2_VERIFIED)
        layer_c = Account("ACC_LAYER_C", "Shell Corp Gamma", 20000.0, KYCStatus.TIER_2_VERIFIED)

        # 5. Smurfing Mule Ring (Mules share same device => Equivalence Relation cluster)
        collector = Account("ACC_COLLECTOR_X", "Cartel Hub X", 50000.0, KYCStatus.TIER_1_UNVERIFIED)
        mule_1 = Account("ACC_MULE_1", "Mule One", 10000.0, KYCStatus.TIER_1_UNVERIFIED, device_fingerprint="DEV_FARM_X")
        mule_2 = Account("ACC_MULE_2", "Mule Two", 10000.0, KYCStatus.TIER_1_UNVERIFIED, device_fingerprint="DEV_FARM_X")
        mule_3 = Account("ACC_MULE_3", "Mule Three", 10000.0, KYCStatus.TIER_1_UNVERIFIED, device_fingerprint="DEV_FARM_X")

        # Register all accounts
        all_accs = [alice, bob, charlie, mallory, puppet, layer_a, layer_b, layer_c, collector, mule_1, mule_2, mule_3]
        for acc in all_accs:
            self.accounts[acc.account_id] = acc

        # Register DMGT U2 Equivalence Relations
        for acc in all_accs:
            self.relation_mgr.register_account_attributes(
                acc.account_id,
                acc.device_fingerprint,
                acc.ip_address,
                acc.national_id,
                self.accounts,
            )

        # Seed known blacklist to Rational Agent
        self.agent.add_to_blacklist("ACC_MALLORY_FRAUD")

        # Seed prior edges for layering cycle (A -> B, B -> C)
        t_base = datetime.now() - timedelta(minutes=45)
        self.graph.add_transaction_edge("TXN_PRE_01", "ACC_LAYER_A", "ACC_LAYER_B", 9500.0, t_base)
        self.graph.add_transaction_edge("TXN_PRE_02", "ACC_LAYER_B", "ACC_LAYER_C", 9400.0, t_base + timedelta(minutes=15))

    def run_benchmark_scenarios(self) -> List[Tuple[Transaction, DecisionOutcome]]:
        """Executes 5 benchmark scenarios showcasing DMGT U1/U2, ADSA U2, AI U1, and OOPJ."""
        results: List[Tuple[Transaction, DecisionOutcome]] = []
        now = datetime.now()

        # ==========================================
        # Scenario 1: Legitimate Routine Transfer
        # ==========================================
        txn1 = Transaction(
            txn_id="TXN_001_LEGIT",
            sender_id="ACC_ALICE",
            receiver_id="ACC_BOB",
            amount=45.0,
            timestamp=now.replace(hour=14, minute=20),
            channel=ChannelType.MOBILE_APP,
            location="US",
            device_id="DEV_ALICE_PHONE",  # Matches baseline
            ip_address="192.168.1.10",
        )
        res1 = self.agent.decide(txn1, self.accounts["ACC_ALICE"], self.accounts["ACC_BOB"])
        results.append((txn1, res1))

        # ==========================================
        # Scenario 2: Account Takeover (DMGT U1 Trigger)
        # ==========================================
        # Charlie historical avg: $75. Transaction: $4,500 (> 60x avg) from new device at 03:15 AM
        txn2 = Transaction(
            txn_id="TXN_002_ATO",
            sender_id="ACC_CHARLIE",
            receiver_id="ACC_BOB",
            amount=4500.0,
            timestamp=now.replace(hour=3, minute=15),
            channel=ChannelType.ONLINE_BANKING,
            location="FOREIGN_ISLANDS",
            device_id="DEV_UNKNOWN_ATTACKER",  # Unrecognized!
            ip_address="45.12.89.200",
        )
        res2 = self.agent.decide(txn2, self.accounts["ACC_CHARLIE"], self.accounts["ACC_BOB"])
        results.append((txn2, res2))

        # ==========================================
        # Scenario 3: Circular Layering Cycle (ADSA U2 Trigger)
        # ==========================================
        # Layer C now attempts to send funds BACK to Layer A, completing directed cycle:
        # A -> B -> C -> A
        txn3 = Transaction(
            txn_id="TXN_003_CYCLE",
            sender_id="ACC_LAYER_C",
            receiver_id="ACC_LAYER_A",
            amount=9300.0,
            timestamp=now.replace(hour=15, minute=0),
            channel=ChannelType.WIRE_TRANSFER,
            location="US",
            device_id="DEV_CORP_C",
        )
        res3 = self.agent.decide(txn3, self.accounts["ACC_LAYER_C"], self.accounts["ACC_LAYER_A"])
        results.append((txn3, res3))

        # ==========================================
        # Scenario 4: Smurfing / Structuring & Equivalence Class (ADSA U2 + DMGT U2)
        # ==========================================
        # Mules 1, 2, 3 rapidly deposit $9,200 to Collector X.
        # They share device DEV_FARM_X (Equivalence class [DEV_FARM_X])
        for idx, mule_id in enumerate(["ACC_MULE_1", "ACC_MULE_2", "ACC_MULE_3"], start=1):
            mule_txn = Transaction(
                txn_id=f"TXN_004_SMURF_{idx}",
                sender_id=mule_id,
                receiver_id="ACC_COLLECTOR_X",
                amount=9200.0,
                timestamp=now - timedelta(minutes=20 - idx * 5),
                channel=ChannelType.ONLINE_BANKING,
                device_id="DEV_FARM_X",
            )
            res_mule = self.agent.decide(mule_txn, self.accounts[mule_id], self.accounts["ACC_COLLECTOR_X"])
            results.append((mule_txn, res_mule))

        # ==========================================
        # Scenario 5: Direct Transfer to/from Blacklisted Account (ADSA BFS Proximity)
        # ==========================================
        txn5 = Transaction(
            txn_id="TXN_005_BLACKLIST_PROXIMITY",
            sender_id="ACC_MALLORY_FRAUD",
            receiver_id="ACC_BOB",
            amount=1200.0,
            timestamp=now.replace(hour=16, minute=10),
            channel=ChannelType.WIRE_TRANSFER,
        )
        res5 = self.agent.decide(txn5, self.accounts["ACC_MALLORY_FRAUD"], self.accounts["ACC_BOB"])
        results.append((txn5, res5))

        # ==========================================
        # Scenario 6: Seemingly Clean Account in Equivalence Class [Mallory] (DMGT U2)
        # ==========================================
        # ACC_PUPPET_CLEAN has normal amount, verified KYC, but shares device with blacklisted Mallory
        txn6 = Transaction(
            txn_id="TXN_006_EQUIV_CLASS_PUPPET",
            sender_id="ACC_PUPPET_CLEAN",
            receiver_id="ACC_ALICE",
            amount=200.0,
            timestamp=now.replace(hour=17, minute=5),
            channel=ChannelType.MOBILE_APP,
            device_id="DEV_DARK_NET_01",
        )
        res6 = self.agent.decide(txn6, self.accounts["ACC_PUPPET_CLEAN"], self.accounts["ACC_ALICE"])
        results.append((txn6, res6))

        return results
