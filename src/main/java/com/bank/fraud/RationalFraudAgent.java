package com.bank.fraud;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AI Unit 1: Rational Agent Decision Policy in Java.
 * Rationality: argmax_a EU(a | Percept).
 */
public class RationalFraudAgent {

    public enum Action {
        APPROVE, FLAG_MANUAL_REVIEW, FREEZE_ACCOUNT
    }

    private final PropositionalRuleEngine logicEngine;
    private final double reviewCost;

    public RationalFraudAgent(PropositionalRuleEngine logicEngine, double reviewCost) {
        this.logicEngine = logicEngine;
        this.reviewCost = reviewCost;
    }

    public Action decide(Transaction txn, Account sender, Account receiver, List<String> auditTrail) {
        // 1. Feature extraction (Sensors)
        Map<String, Boolean> assignment = new HashMap<>();
        assignment.put("P_HIGH_AMOUNT", txn.getAmount() > 3.0 * sender.getHistoricalAvgAmount());
        assignment.put("P_NEW_DEVICE", !sender.getDeviceFingerprint().isEmpty() && !txn.getDeviceId().equals(sender.getDeviceFingerprint()));
        assignment.put("P_FOREIGN_LOCATION", !txn.getLocation().equals("US"));

        // 2. Logic risk
        List<String> firedRules = new ArrayList<>();
        double logicRisk = logicEngine.evaluateAll(assignment, firedRules);
        for (String rule : firedRules) {
            auditTrail.add("[Java DMGT-U1] Fired: " + rule);
            txn.addFlagReason(rule);
        }

        // 3. Posterior calculation
        double pFraud = 0.02 + 0.55 * logicRisk;
        if (sender.isBlacklisted()) {
            pFraud = 0.95;
            auditTrail.add("[Java ADSA-U2] SENDER IS BLACKLISTED!");
            txn.addFlagReason("SENDER_IN_BLACKLIST");
        }
        txn.setRiskScore(pFraud);

        // 4. Expected Utility Payoffs
        double amount = txn.getAmount();
        double euApprove = pFraud * (-amount) + (1.0 - pFraud) * (0.01 * amount);
        double euReview = pFraud * (0.90 * amount - reviewCost) + (1.0 - pFraud) * (-reviewCost - 0.02 * amount);
        double euFreeze = pFraud * (amount) + (1.0 - pFraud) * (-0.25 * amount - 100.0);

        auditTrail.add(String.format("[Java AI-U1] EU(Approve)=$%.2f, EU(Review)=$%.2f, EU(Freeze)=$%.2f",
                euApprove, euReview, euFreeze));

        // 5. Rational Choice: argmax EU
        Action bestAction = Action.APPROVE;
        double maxEu = euApprove;

        if (euReview > maxEu) {
            bestAction = Action.FLAG_MANUAL_REVIEW;
            maxEu = euReview;
        }
        if (euFreeze > maxEu) {
            bestAction = Action.FREEZE_ACCOUNT;
            maxEu = euFreeze;
        }

        txn.setStatus(bestAction.name());
        auditTrail.add(String.format("[Java AI-U1 Decision] Optimal Action=%s (Max EU=$%.2f)", bestAction, maxEu));
        return bestAction;
    }
}
