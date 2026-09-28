package com.bank.fraud;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Account Domain Model (OOPJ in Java).
 * Embodying Encapsulation, Invariant Protection, and Thread-Safe Balance Updates.
 */
public class Account {
    private final String accountId;
    private final String holderName;
    private final AtomicReference<Double> balance;
    private final String kycStatus;
    private final Instant createdAt;
    private final String deviceFingerprint;
    private final String ipAddress;
    private final String nationalId;
    private volatile double historicalAvgAmount;
    private volatile boolean isBlacklisted;

    public Account(String accountId, String holderName, double initialBalance, String kycStatus,
                   String deviceFingerprint, String ipAddress, String nationalId, double historicalAvgAmount, boolean isBlacklisted) {
        this.accountId = accountId;
        this.holderName = holderName;
        this.balance = new AtomicReference<>(Math.max(0.0, initialBalance));
        this.kycStatus = kycStatus;
        this.createdAt = Instant.now();
        this.deviceFingerprint = deviceFingerprint;
        this.ipAddress = ipAddress;
        this.nationalId = nationalId;
        this.historicalAvgAmount = Math.max(1.0, historicalAvgAmount);
        this.isBlacklisted = isBlacklisted;
    }

    public String getAccountId() { return accountId; }
    public String getHolderName() { return holderName; }
    public double getBalance() { return balance.get(); }
    public String getKycStatus() { return kycStatus; }
    public Instant getCreatedAt() { return createdAt; }
    public String getDeviceFingerprint() { return deviceFingerprint; }
    public String getIpAddress() { return ipAddress; }
    public String getNationalId() { return nationalId; }
    public double getHistoricalAvgAmount() { return historicalAvgAmount; }
    public boolean isBlacklisted() { return isBlacklisted; }
    public void setBlacklisted(boolean blacklisted) { isBlacklisted = blacklisted; }

    public synchronized void recordTransaction(double amount) {
        double alpha = 0.1;
        this.historicalAvgAmount = (1 - alpha) * this.historicalAvgAmount + alpha * amount;
    }

    @Override
    public String toString() {
        return String.format("Account[id=%s, holder='%s', balance=$%.2f, avg=$%.2f, blacklisted=%b]",
                accountId, holderName, balance.get(), historicalAvgAmount, isBlacklisted);
    }
}
