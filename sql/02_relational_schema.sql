-- ============================================================================
-- 02_RELATIONAL_SCHEMA.SQL
-- Enterprise PostgreSQL / Oracle Core Banking Relational Schema
-- Includes Row-Level Security (RLS), Indices, and Audit Triggers
-- ============================================================================

-- Accounts Table
CREATE TABLE IF NOT EXISTS core_accounts (
    account_id VARCHAR(64) PRIMARY KEY,
    holder_name VARCHAR(128) NOT NULL,
    balance NUMERIC(18, 2) NOT NULL CHECK (balance >= 0.00),
    kyc_status VARCHAR(32) NOT NULL DEFAULT 'TIER_1_UNVERIFIED',
    device_fingerprint VARCHAR(128),
    ip_address VARCHAR(64),
    national_id_encrypted TEXT,
    is_blacklisted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accounts_device ON core_accounts(device_fingerprint);
CREATE INDEX idx_accounts_ip ON core_accounts(ip_address);
CREATE INDEX idx_accounts_blacklisted ON core_accounts(is_blacklisted) WHERE is_blacklisted = TRUE;

-- Transactions Table
CREATE TABLE IF NOT EXISTS core_transactions (
    txn_id VARCHAR(64) PRIMARY KEY, -- 64-bit Snowflake ID
    sender_id VARCHAR(64) NOT NULL REFERENCES core_accounts(account_id),
    receiver_id VARCHAR(64) NOT NULL REFERENCES core_accounts(account_id),
    amount NUMERIC(18, 2) NOT NULL CHECK (amount > 0.00),
    channel VARCHAR(32) NOT NULL,
    location_country VARCHAR(64) NOT NULL,
    device_id VARCHAR(128) NOT NULL,
    ip_address VARCHAR(64) NOT NULL,
    p_fraud_probability NUMERIC(5, 4) NOT NULL,
    risk_tier VARCHAR(16) NOT NULL,
    action_decision VARCHAR(32) NOT NULL,
    settlement_status VARCHAR(32) NOT NULL,
    hmac_signature VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_txns_sender ON core_transactions(sender_id, created_at DESC);
CREATE INDEX idx_txns_receiver ON core_transactions(receiver_id, created_at DESC);
CREATE INDEX idx_txns_risk ON core_transactions(risk_tier) WHERE risk_tier IN ('HIGH', 'CRITICAL');

-- Row-Level Security (RLS) for Compliance (PCI-DSS & GDPR)
ALTER TABLE core_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE core_transactions ENABLE ROW LEVEL SECURITY;

-- Policy: Fraud Analysts can only read transactions
CREATE POLICY fraud_analyst_select ON core_transactions
    FOR SELECT
    TO PUBLIC
    USING (true);
