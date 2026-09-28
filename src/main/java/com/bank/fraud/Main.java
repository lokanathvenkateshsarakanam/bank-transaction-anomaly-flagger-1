package com.bank.fraud;

import java.util.ArrayList;
import java.util.List;

/**
 * Main Executable for Java Enterprise Banking Core.
 */
public class Main {
    public static void main(String[] args) {
        System.out.println("================================================================================");
        System.out.println("         ENTERPRISE JAVA CORE BANKING TRANSACTION ANOMALY FLAGGER              ");
        System.out.println("================================================================================");

        // 1. Configure DMGT U1 Logic Engine in Java
        PropositionalRuleEngine logicEngine = new PropositionalRuleEngine();
        logicEngine.addRule(new PropositionalRuleEngine.FraudRule(
                "RULE_JAVA_ATO",
                new PropositionalRuleEngine.And(
                        new PropositionalRuleEngine.Prop("P_HIGH_AMOUNT"),
                        new PropositionalRuleEngine.Prop("P_NEW_DEVICE")
                ),
                "SUSPECT_ACCOUNT_TAKEOVER",
                0.65
        ));

        // 2. Configure AI U1 Rational Agent in Java
        RationalFraudAgent agent = new RationalFraudAgent(logicEngine, 25.0);

        // 3. Instantiate OOPJ Accounts
        Account alice = new Account("ACC_ALICE", "Alice Smith", 5000.0, "TIER_2", "DEV_ALICE_PHONE", "192.168.1.10", "SSN_111", 60.0, false);
        Account charlie = new Account("ACC_CHARLIE", "Charlie Brown", 12000.0, "TIER_2", "DEV_CHARLIE_TRUSTED", "10.0.0.5", "SSN_333", 75.0, false);
        Account bob = new Account("ACC_BOB", "Bob Jones", 3000.0, "TIER_2", "DEV_BOB_LAPTOP", "192.168.1.20", "SSN_222", 100.0, false);

        // Scenario 1: Benign Payment
        Transaction t1 = new Transaction("TX_JAVA_001", "ACC_ALICE", "ACC_BOB", 45.0, "MOBILE", "US", "DEV_ALICE_PHONE", "192.168.1.10");
        List<String> audit1 = new ArrayList<>();
        RationalFraudAgent.Action d1 = agent.decide(t1, alice, bob, audit1);
        System.out.println("\n[SCENARIO 1 - BENIGN GROCERY]: " + t1);
        System.out.println("Decision: " + d1 + " | Risk: " + t1.getRiskScore());
        audit1.forEach(a -> System.out.println("  " + a));

        // Scenario 2: Account Takeover
        Transaction t2 = new Transaction("TX_JAVA_002", "ACC_CHARLIE", "ACC_BOB", 4500.0, "ONLINE", "FOREIGN", "DEV_UNKNOWN", "45.12.89.200");
        List<String> audit2 = new ArrayList<>();
        RationalFraudAgent.Action d2 = agent.decide(t2, charlie, bob, audit2);
        System.out.println("\n[SCENARIO 2 - ACCOUNT TAKEOVER]: " + t2);
        System.out.println("Decision: " + d2 + " | Risk: " + t2.getRiskScore());
        audit2.forEach(a -> System.out.println("  " + a));

        System.out.println("\nJava Core Banking Anomaly Flagger Executed Successfully.");
    }
}
