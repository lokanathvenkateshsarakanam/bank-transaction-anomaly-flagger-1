package com.bank.fraud;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * DMGT Unit 1: Propositional Logic Rule Engine implemented in Java.
 */
public class PropositionalRuleEngine {

    public interface Expr {
        boolean evaluate(Map<String, Boolean> assignment);
    }

    public static class Prop implements Expr {
        private final String name;
        public Prop(String name) { this.name = name; }
        @Override
        public boolean evaluate(Map<String, Boolean> assignment) {
            return assignment.getOrDefault(name, false);
        }
    }

    public static class Not implements Expr {
        private final Expr child;
        public Not(Expr child) { this.child = child; }
        @Override
        public boolean evaluate(Map<String, Boolean> assignment) {
            return !child.evaluate(assignment);
        }
    }

    public static class And implements Expr {
        private final Expr[] children;
        public And(Expr... children) { this.children = children; }
        @Override
        public boolean evaluate(Map<String, Boolean> assignment) {
            for (Expr c : children) {
                if (!c.evaluate(assignment)) return false;
            }
            return true;
        }
    }

    public static class Or implements Expr {
        private final Expr[] children;
        public Or(Expr... children) { this.children = children; }
        @Override
        public boolean evaluate(Map<String, Boolean> assignment) {
            for (Expr c : children) {
                if (c.evaluate(assignment)) return true;
            }
            return false;
        }
    }

    public static class FraudRule {
        private final String ruleId;
        private final Expr condition;
        private final String flagConsequent;
        private final double weight;

        public FraudRule(String ruleId, Expr condition, String flagConsequent, double weight) {
            this.ruleId = ruleId;
            this.condition = condition;
            this.flagConsequent = flagConsequent;
            this.weight = weight;
        }

        public String getRuleId() { return ruleId; }
        public String getFlagConsequent() { return flagConsequent; }
        public double getWeight() { return weight; }
        public boolean fires(Map<String, Boolean> assignment) { return condition.evaluate(assignment); }
    }

    private final List<FraudRule> rules = new ArrayList<>();

    public void addRule(FraudRule rule) { rules.add(rule); }
    public List<FraudRule> getRules() { return rules; }

    public double evaluateAll(Map<String, Boolean> assignment, List<String> firedFlags) {
        double totalRisk = 0.0;
        for (FraudRule rule : rules) {
            if (rule.fires(assignment)) {
                firedFlags.add(rule.getFlagConsequent());
                totalRisk += rule.getWeight();
            }
        }
        return Math.min(1.0, totalRisk);
    }
}
