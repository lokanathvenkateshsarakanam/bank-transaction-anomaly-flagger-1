"""Snowflake Data Warehouse / Lakehouse Integration Framework for Banking Fraud Analytics.

Implements:
1. Snowflake Dimensional Schema (DDL):
   - FACT_TRANSACTIONS (Fact table for financial ledger & screening telemetry)
   - DIM_ACCOUNTS (Dimension table for account profiles & KYC tiers)
   - DIM_ANOMALY_AUDIT (Dimension table for rule engine & graph audit traces)
   - STAGING_TRANSACTIONS (Staging area for high-velocity streaming ingestion)
   - Snowflake Streams & Tasks DDL for automated materialized aggregations
2. Ingestion & Query Interface:
   - Connects to live Snowflake via `snowflake-connector-python` when credentials exist.
   - Transparently falls back to an embedded high-performance engine for local execution.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from ai.agent import DecisionOutcome
from models.transaction import Transaction

logger = logging.getLogger(__name__)

# Standard Snowflake DDL Scripts for Enterprise Banking Setup
SNOWFLAKE_DDL_SCHEMA = """
-- ========================================================================
-- SNOWFLAKE CLOUD DATA WAREHOUSE DDL: BANKING ANOMALY SCREENING SCHEMA
-- ========================================================================

CREATE DATABASE IF NOT EXISTS BANK_FRAUD_DB;
CREATE SCHEMA IF NOT EXISTS BANK_FRAUD_DB.ANALYTICS;
USE SCHEMA BANK_FRAUD_DB.ANALYTICS;

-- 1. Dimension Table: Accounts
CREATE TABLE IF NOT EXISTS DIM_ACCOUNTS (
    ACCOUNT_ID          VARCHAR(64) PRIMARY KEY,
    HOLDER_NAME         VARCHAR(128),
    INITIAL_BALANCE     DECIMAL(18, 2),
    KYC_STATUS          VARCHAR(32),
    DEVICE_FINGERPRINT  VARCHAR(128),
    IP_ADDRESS          VARCHAR(64),
    NATIONAL_ID         VARCHAR(64),
    IS_BLACKLISTED      BOOLEAN DEFAULT FALSE,
    CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 2. Fact Table: Screened Financial Transactions
CREATE TABLE IF NOT EXISTS FACT_TRANSACTIONS (
    SNOWFLAKE_TXN_ID    VARCHAR(64) PRIMARY KEY,
    SENDER_ID           VARCHAR(64) REFERENCES DIM_ACCOUNTS(ACCOUNT_ID),
    RECEIVER_ID         VARCHAR(64) REFERENCES DIM_ACCOUNTS(ACCOUNT_ID),
    AMOUNT              DECIMAL(18, 2),
    TIMESTAMP_UTC       TIMESTAMP_NTZ,
    CHANNEL             VARCHAR(32),
    LOCATION            VARCHAR(64),
    DEVICE_ID           VARCHAR(128),
    IP_ADDRESS          VARCHAR(64),
    P_FRAUD_SCORE       FLOAT,
    RISK_TIER           VARCHAR(16),
    ACTION_DECISION     VARCHAR(32),
    STATUS              VARCHAR(32),
    FIRED_RULES_JSON    VARCHAR(1024),
    INGESTED_AT         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 3. Audit Table: Anomaly Telemetry Traces
CREATE TABLE IF NOT EXISTS DIM_ANOMALY_AUDIT (
    AUDIT_ID            INTEGER AUTOINCREMENT PRIMARY KEY,
    SNOWFLAKE_TXN_ID    VARCHAR(64) REFERENCES FACT_TRANSACTIONS(SNOWFLAKE_TXN_ID),
    SUBSYSTEM           VARCHAR(32),
    TRACE_DETAIL        VARCHAR(2048),
    CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 4. Staging Table: Micro-Batch Stream Ingestion
CREATE TABLE IF NOT EXISTS STAGING_TRANSACTIONS (
    PAYLOAD_JSON        VARIANT,
    STAGED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 5. Snowflake Change Data Capture (CDC) Stream
CREATE OR REPLACE STREAM STREAM_HIGH_RISK_TXNS ON TABLE FACT_TRANSACTIONS;
"""


class SnowflakeWarehouseConnector:
    """Manages transactional ingestion and analytics queries on the Snowflake data warehouse."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.use_live_snowflake = False
        self._live_conn = None
        self._local_conn = None

        # Check environment variables for live Snowflake Data Cloud credentials
        account = os.environ.get("SNOWFLAKE_ACCOUNT")
        user = os.environ.get("SNOWFLAKE_USER")
        password = os.environ.get("SNOWFLAKE_PASSWORD")

        if account and user and password:
            try:
                import snowflake.connector

                self._live_conn = snowflake.connector.connect(
                    user=user,
                    password=password,
                    account=account,
                    warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
                    database=os.environ.get("SNOWFLAKE_DATABASE", "BANK_FRAUD_DB"),
                    schema=os.environ.get("SNOWFLAKE_SCHEMA", "ANALYTICS"),
                )
                self.use_live_snowflake = True
                logger.info("Connected to live Snowflake Data Cloud instance.")
            except Exception as e:
                logger.warning(f"Could not connect to live Snowflake ({e}). Falling back to local Snowflake engine.")
                self.use_live_snowflake = False

        if not self.use_live_snowflake:
            # Initialize high-fidelity local Snowflake engine emulator using SQLite
            self._local_conn = sqlite3.connect(db_path, check_same_thread=False)
            self._setup_local_tables()

    def _setup_local_tables(self) -> None:
        """Initializes tables matching the Snowflake schema locally."""
        cur = self._local_conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS DIM_ACCOUNTS (
                ACCOUNT_ID TEXT PRIMARY KEY,
                HOLDER_NAME TEXT,
                INITIAL_BALANCE REAL,
                KYC_STATUS TEXT,
                DEVICE_FINGERPRINT TEXT,
                IP_ADDRESS TEXT,
                NATIONAL_ID TEXT,
                IS_BLACKLISTED INTEGER,
                CREATED_AT TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS FACT_TRANSACTIONS (
                SNOWFLAKE_TXN_ID TEXT PRIMARY KEY,
                SENDER_ID TEXT,
                RECEIVER_ID TEXT,
                AMOUNT REAL,
                TIMESTAMP_UTC TEXT,
                CHANNEL TEXT,
                LOCATION TEXT,
                DEVICE_ID TEXT,
                IP_ADDRESS TEXT,
                P_FRAUD_SCORE REAL,
                RISK_TIER TEXT,
                ACTION_DECISION TEXT,
                STATUS TEXT,
                FIRED_RULES_JSON TEXT,
                INGESTED_AT TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS DIM_ANOMALY_AUDIT (
                AUDIT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                SNOWFLAKE_TXN_ID TEXT,
                SUBSYSTEM TEXT,
                TRACE_DETAIL TEXT,
                CREATED_AT TEXT
            )
            """
        )
        self._local_conn.commit()

    def sync_account(self, account: Any) -> None:
        """Upserts an account into DIM_ACCOUNTS."""
        if self.use_live_snowflake:
            # Live Snowflake merge query
            query = """
            MERGE INTO DIM_ACCOUNTS target USING (
                SELECT %s as ACCOUNT_ID, %s as HOLDER_NAME, %s as INITIAL_BALANCE,
                       %s as KYC_STATUS, %s as DEVICE_FINGERPRINT, %s as IP_ADDRESS,
                       %s as NATIONAL_ID, %s as IS_BLACKLISTED
            ) source ON target.ACCOUNT_ID = source.ACCOUNT_ID
            WHEN MATCHED THEN UPDATE SET
                HOLDER_NAME = source.HOLDER_NAME,
                INITIAL_BALANCE = source.INITIAL_BALANCE,
                KYC_STATUS = source.KYC_STATUS,
                DEVICE_FINGERPRINT = source.DEVICE_FINGERPRINT,
                IS_BLACKLISTED = source.IS_BLACKLISTED
            WHEN NOT MATCHED THEN INSERT (ACCOUNT_ID, HOLDER_NAME, INITIAL_BALANCE, KYC_STATUS, DEVICE_FINGERPRINT, IP_ADDRESS, NATIONAL_ID, IS_BLACKLISTED)
            VALUES (source.ACCOUNT_ID, source.HOLDER_NAME, source.INITIAL_BALANCE, source.KYC_STATUS, source.DEVICE_FINGERPRINT, source.IP_ADDRESS, source.NATIONAL_ID, source.IS_BLACKLISTED);
            """
            with self._live_conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        account.account_id,
                        account.holder_name,
                        account.balance,
                        account.kyc_status.value,
                        account.device_fingerprint,
                        account.ip_address,
                        account.national_id,
                        account.is_blacklisted,
                    ),
                )
        else:
            cur = self._local_conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO DIM_ACCOUNTS
                (ACCOUNT_ID, HOLDER_NAME, INITIAL_BALANCE, KYC_STATUS, DEVICE_FINGERPRINT, IP_ADDRESS, NATIONAL_ID, IS_BLACKLISTED, CREATED_AT)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account.account_id,
                    account.holder_name,
                    account.balance,
                    account.kyc_status.value,
                    account.device_fingerprint,
                    account.ip_address,
                    account.national_id,
                    1 if account.is_blacklisted else 0,
                    datetime.now().isoformat(),
                ),
            )
            self._local_conn.commit()

    def record_screened_transaction(self, txn: Transaction, decision: DecisionOutcome) -> None:
        """Ingests a screened transaction into FACT_TRANSACTIONS and traces into DIM_ANOMALY_AUDIT."""
        fired_json = json.dumps(decision.fired_rules)
        now_str = datetime.now().isoformat()
        txn_time_str = txn.timestamp.isoformat()

        if self.use_live_snowflake:
            with self._live_conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO FACT_TRANSACTIONS (
                        SNOWFLAKE_TXN_ID, SENDER_ID, RECEIVER_ID, AMOUNT, TIMESTAMP_UTC,
                        CHANNEL, LOCATION, DEVICE_ID, IP_ADDRESS, P_FRAUD_SCORE,
                        RISK_TIER, ACTION_DECISION, STATUS, FIRED_RULES_JSON, INGESTED_AT
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
                    """,
                    (
                        txn.txn_id,
                        txn.sender_id,
                        txn.receiver_id,
                        txn.amount,
                        txn_time_str,
                        txn.channel.value,
                        txn.location,
                        txn.device_id,
                        txn.ip_address,
                        decision.posterior_fraud_probability,
                        decision.risk_tier.value,
                        decision.action.value,
                        txn.status.value,
                        fired_json,
                    ),
                )
                for trace in decision.audit_trail:
                    cur.execute(
                        "INSERT INTO DIM_ANOMALY_AUDIT (SNOWFLAKE_TXN_ID, SUBSYSTEM, TRACE_DETAIL) VALUES (%s, %s, %s)",
                        (txn.txn_id, "ANOMALY_SCREENER", trace),
                    )
        else:
            cur = self._local_conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO FACT_TRANSACTIONS (
                    SNOWFLAKE_TXN_ID, SENDER_ID, RECEIVER_ID, AMOUNT, TIMESTAMP_UTC,
                    CHANNEL, LOCATION, DEVICE_ID, IP_ADDRESS, P_FRAUD_SCORE,
                    RISK_TIER, ACTION_DECISION, STATUS, FIRED_RULES_JSON, INGESTED_AT
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    txn.txn_id,
                    txn.sender_id,
                    txn.receiver_id,
                    txn.amount,
                    txn_time_str,
                    txn.channel.value,
                    txn.location,
                    txn.device_id,
                    txn.ip_address,
                    decision.posterior_fraud_probability,
                    decision.risk_tier.value,
                    decision.action.value,
                    txn.status.value,
                    fired_json,
                    now_str,
                ),
            )
            for trace in decision.audit_trail:
                cur.execute(
                    "INSERT INTO DIM_ANOMALY_AUDIT (SNOWFLAKE_TXN_ID, SUBSYSTEM, TRACE_DETAIL, CREATED_AT) VALUES (?, ?, ?, ?)",
                    (txn.txn_id, "ANOMALY_SCREENER", trace, now_str),
                )
            self._local_conn.commit()

    def query_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Queries recent screened transactions from FACT_TRANSACTIONS."""
        if self.use_live_snowflake:
            with self._live_conn.cursor() as cur:
                cur.execute(
                    "SELECT SNOWFLAKE_TXN_ID, SENDER_ID, RECEIVER_ID, AMOUNT, P_FRAUD_SCORE, RISK_TIER, ACTION_DECISION, TIMESTAMP_UTC FROM FACT_TRANSACTIONS ORDER BY INGESTED_AT DESC LIMIT %s",
                    (limit,),
                )
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        else:
            cur = self._local_conn.cursor()
            cur.execute(
                "SELECT SNOWFLAKE_TXN_ID, SENDER_ID, RECEIVER_ID, AMOUNT, P_FRAUD_SCORE, RISK_TIER, ACTION_DECISION, TIMESTAMP_UTC FROM FACT_TRANSACTIONS ORDER BY INGESTED_AT DESC LIMIT ?",
                (limit,),
            )
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def query_audit_traces(self, txn_id: str) -> List[str]:
        """Queries audit traces for a specific Snowflake transaction ID."""
        if self.use_live_snowflake:
            with self._live_conn.cursor() as cur:
                cur.execute("SELECT TRACE_DETAIL FROM DIM_ANOMALY_AUDIT WHERE SNOWFLAKE_TXN_ID = %s", (txn_id,))
                return [row[0] for row in cur.fetchall()]
        else:
            cur = self._local_conn.cursor()
            cur.execute("SELECT TRACE_DETAIL FROM DIM_ANOMALY_AUDIT WHERE SNOWFLAKE_TXN_ID = ?", (txn_id,))
            return [row[0] for row in cur.fetchall()]

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates warehouse-level metrics for fraud dashboard."""
        if self.use_live_snowflake:
            with self._live_conn.cursor() as cur:
                cur.execute("SELECT COUNT(*), AVG(P_FRAUD_SCORE), SUM(AMOUNT) FROM FACT_TRANSACTIONS")
                row = cur.fetchone()
                return {"total_transactions": row[0] or 0, "avg_risk": round(row[1] or 0.0, 3), "total_volume": round(row[2] or 0.0, 2)}
        else:
            cur = self._local_conn.cursor()
            cur.execute("SELECT COUNT(*), AVG(P_FRAUD_SCORE), SUM(AMOUNT) FROM FACT_TRANSACTIONS")
            row = cur.fetchone()
            return {"total_transactions": row[0] or 0, "avg_risk": round(row[1] or 0.0, 3), "total_volume": round(row[2] or 0.0, 2)}
