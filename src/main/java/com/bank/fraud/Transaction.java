package com.bank.fraud;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Transaction Domain Model (Java OOPJ).
 * Encapsulates immutable transaction payload and security audit tags.
 */
public class Transaction {
    private final String txnId;
    private final String senderId;
    private final String receiverId;
    private final double amount;
    private final Instant timestamp;
    private final String channel;
    private final String location;
    private final String deviceId;
    private final String ipAddress;
    private String status;
    private double riskScore;
    private final List<String> flagReasons;

    public Transaction(String txnId, String senderId, String receiverId, double amount,
                       String channel, String location, String deviceId, String ipAddress) {
        this.txnId = txnId;
        this.senderId = senderId;
        this.receiverId = receiverId;
        this.amount = amount;
        this.timestamp = Instant.now();
        this.channel = channel;
        this.location = location;
        this.deviceId = deviceId;
        this.ipAddress = ipAddress;
        this.status = "PENDING";
        this.riskScore = 0.0;
        this.flagReasons = new ArrayList<>();
    }

    public String getTxnId() { return txnId; }
    public String getSenderId() { return senderId; }
    public String getReceiverId() { return receiverId; }
    public double getAmount() { return amount; }
    public Instant getTimestamp() { return timestamp; }
    public String getChannel() { return channel; }
    public String getLocation() { return location; }
    public String getDeviceId() { return deviceId; }
    public String getIpAddress() { return ipAddress; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public double getRiskScore() { return riskScore; }
    public void setRiskScore(double riskScore) { this.riskScore = riskScore; }
    public List<String> getFlagReasons() { return Collections.unmodifiableList(flagReasons); }
    public void addFlagReason(String reason) { if (!flagReasons.contains(reason)) flagReasons.add(reason); }

    @Override
    public String toString() {
        return String.format("Transaction[%s: %s -> %s, $%.2f, status=%s, risk=%.3f]",
                txnId, senderId, receiverId, amount, status, riskScore);
    }
}
