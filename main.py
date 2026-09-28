"""Main entrypoint for Bank Transaction Anomaly Flagger.

Demonstrates end-to-end integration of:
- DMGT U1: Propositional Logic Rule Engine
- DMGT U2: Transaction Relations & Equivalence Classes
- AI U1: Rational Agent Expected Utility Optimization
- ADSA U2: Transaction Network Graph & Cycle Detection
- OOPJ: Object-Oriented Domain Architecture
"""

import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from simulator import BankingSimulator, build_default_propositional_engine
from snowflake_integration.snowflake_id import default_snowflake_generator
from snowflake_integration.snowflake_warehouse import SnowflakeWarehouseConnector


def print_header(title: str) -> None:
    width = 80
    print("\n" + "=" * width)
    print(f" {title.center(width - 2)} ")
    print("=" * width)


def print_subheader(title: str) -> None:
    print(f"\n--- {title} ---")


def display_curriculum_mapping() -> None:
    print_header("BANK TRANSACTION ANOMALY FLAGGER - CURRICULUM ARCHITECTURE")
    print(
        """
  1. DMGT (Discrete Mathematics & Graph Theory):
     - Unit 1: Propositional Logic Rule Engine (AST, Connectives ¬, ∧, ∨, →, Modus Ponens)
     - Unit 2: Transaction Relations (R ⊆ A × A, Reflexive/Symmetric/Transitive, Equivalence Classes [x], A/R)
  
  2. AI (Artificial Intelligence):
     - Unit 1: Rational Agent Decision Rules (PEAS Model, Belief State, Expected Utility Maximization)
  
  3. ADSA (Advanced Data Structures & Algorithms):
     - Unit 2: Transaction Network Graph (Directed Adjacency List, 3-Color DFS Cycle Detection, Smurfing Fan-In)
  
  4. OOPJ (Object-Oriented Programming):
     - Encapsulated Account/Transaction Domain Models, Polymorphic Rules, Clean Architecture

  5. Bottle Micro-Web Framework:
     - WSGI RESTful Web Service & Interactive Telemetry Dashboard (HTTP GET/POST routing)

  6. Snowflake Framework:
     - 64-bit Distributed Snowflake ID Generation (Twitter Snowflake specification)
     - Snowflake Cloud Data Warehouse / Lakehouse dimensional schema (FACT_TRANSACTIONS, DIM_ACCOUNTS)
    """
    )


def display_dmgt_formal_verification() -> None:
    print_header("DMGT FORMAL VERIFICATION & MATHEMATICAL FOUNDATIONS")

    # 1. DMGT U1: Truth Table Generation for Rule ATO
    print_subheader("DMGT Unit 1: Propositional Logic Truth Table (RULE_ATO_01)")
    engine = build_default_propositional_engine()
    rule_ato = engine.rules[0]
    print(f"Rule: {rule_ato.name}")
    print(f"Formal Implication: {rule_ato.condition.to_formal_string()} → {rule_ato.flag_consequent}")
    print("\nTruth Table:")
    truth_table = rule_ato.generate_truth_table()

    # Get header columns
    vars_keys = [k for k in truth_table[0].keys() if k != "EVALUATION"]
    header = " | ".join(f"{k:18}" for k in vars_keys) + " | " + "CONDITION EVAL".center(16)
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for row in truth_table:
        vals = " | ".join(f"{str(row[k]):18}" for k in vars_keys)
        eval_str = str(row["EVALUATION"]).center(16)
        print(f"{vals} | {eval_str}")
    print("-" * len(header))

    # 2. DMGT U2: Equivalence Relations & Quotient Set
    print_subheader("DMGT Unit 2: Equivalence Classes & Partition (Device Fingerprint Relation)")
    sim = BankingSimulator()
    rel = sim.relation_mgr.device_relation
    print(f"Relation Name: {rel.name}")
    print(f"Is Reflexive?: {rel.is_reflexive()}")
    print(f"Is Symmetric?: {rel.is_symmetric()}")
    print(f"Is Transitive?: {rel.is_transitive()}")
    print(f"Is Valid Equivalence Relation?: {rel.is_equivalence_relation()}")

    quotient_set = rel.get_quotient_set()
    print(f"\nQuotient Set A / R (Partition of accounts by shared device):")
    for i, eq_class in enumerate(quotient_set, 1):
        if len(eq_class) > 1:
            print(f"  Cluster {i} (Mule Syndicate detected!): {sorted(list(eq_class))}")
        else:
            print(f"  Cluster {i} (Isolated Single Device): {sorted(list(eq_class))}")


def run_simulation() -> None:
    print_header("REAL-TIME TRANSACTION STREAM SIMULATION & SNOWFLAKE INGESTION")
    simulator = BankingSimulator()
    warehouse = SnowflakeWarehouseConnector()

    # Sync accounts to Snowflake DIM_ACCOUNTS
    for acc in simulator.accounts.values():
        warehouse.sync_account(acc)

    results = simulator.run_benchmark_scenarios()

    for i, (txn, decision) in enumerate(results, 1):
        # Generate 64-bit Snowflake ID for transaction
        raw_snow_id = default_snowflake_generator.generate_id()
        decoded_snow = default_snowflake_generator.decode_id(raw_snow_id)
        snow_txn_id = f"TXN_SNOW_{raw_snow_id}"
        txn.txn_id = snow_txn_id

        # Ingest into Snowflake Cloud Data Warehouse (FACT_TRANSACTIONS & DIM_ANOMALY_AUDIT)
        warehouse.record_screened_transaction(txn, decision)

        print("\n" + "#" * 80)
        print(f"TRANSACTION #{i}: {txn.txn_id} | Amount: ${txn.amount:,.2f}")
        print(f"Route: {txn.sender_id} -> {txn.receiver_id} | Channel: {txn.channel.value}")
        print(f"[Snowflake ID Metadata] Raw ID: {raw_snow_id} | Worker: {decoded_snow.worker_id} | Datacenter: {decoded_snow.datacenter_id} | Seq: {decoded_snow.sequence}")
        print("#" * 80)

        print("\n[AI Agent Sensor Readings & Inferences]:")
        for trace in decision.audit_trail:
            print(f"  * {trace}")

        print("\n[AI Unit 1 Expected Utility Payoff Matrix EU(a)]:")
        for action, utility in decision.expected_utilities.items():
            chosen_mark = " <=== [OPTIMAL RATIONAL CHOICE]" if action == decision.action else ""
            print(f"  - Action: {action.value:20} => Expected Utility: ${utility:8.2f}{chosen_mark}")

        print("\n[Screening Outcome Summary]:")
        print(f"  - Risk Score (P(Fraud)) : {decision.posterior_fraud_probability:.3f}")
        print(f"  - Risk Tier             : {decision.risk_tier.value}")
        print(f"  - Final Action          : {decision.action.value}")
        print(f"  - Snowflake Status      : INGESTED INTO FACT_TRANSACTIONS")
        print(f"  - Fired Rule Flags      : {decision.fired_rules if decision.fired_rules else ['None (Clean)']}")

    print_header("SNOWFLAKE WAREHOUSE ANALYTICS & AUDIT SUMMARY")
    recent_records = warehouse.query_recent_transactions(limit=10)
    print(f"{'Snowflake Txn ID':<28} | {'Amount':<10} | {'Risk Tier':<10} | {'P(Fraud)':<9} | {'Action Decision':<18}")
    print("-" * 84)
    for r in recent_records:
        print(
            f"{r['SNOWFLAKE_TXN_ID']:<28} | ${r['AMOUNT']:>8.2f} | {r['RISK_TIER']:<10} | "
            f"{r['P_FRAUD_SCORE']:>8.3f} | {r['ACTION_DECISION']:<18}"
        )
    print("-" * 84)

    stats = warehouse.get_summary_statistics()
    print(f"\n[Snowflake Warehouse Aggregate Metrics]:")
    print(f"  - Total Transactions Ingested: {stats['total_transactions']}")
    print(f"  - Total Screened Volume      : ${stats['total_volume']:,.2f}")
    print(f"  - Mean Network Fraud Risk    : {stats['avg_risk']}")

    print("\n" + "=" * 80)
    print(" BOTTLE WEB APPLICATION READY")
    print(" To launch the interactive web dashboard & REST API server, run:")
    print("     python web_app.py")
    print(" Then open your browser at: http://localhost:3030/")
    print("=" * 80)


def main() -> None:
    display_curriculum_mapping()
    display_dmgt_formal_verification()
    run_simulation()


if __name__ == "__main__":
    main()
