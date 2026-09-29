"""Bottle Micro-Web Framework Application for Bank Transaction Anomaly Flagger.

Provides:
1. RESTful JSON API for Transaction Screening, Graph Querying, and Snowflake Analytics.
2. Interactive Web Dashboard for live testing, risk telemetry, and audit trail exploration.
3. Native integration with Snowflake ID Generator and Snowflake Data Warehouse.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict
import bottle
from bottle import Bottle, HTTPResponse, request, response, static_file
from adsa.graph import TransactionGraph
from ai.agent import DecisionOutcome, RationalFraudScreeningAgent
from models.account import Account
from models.transaction import Transaction
from models.types import ActionType, ChannelType, KYCStatus, RiskTier
from cobol.cobol_bridge import CobolMainframeEngine, CobolScreeningRecord
from fortran.fortran_bridge import FortranRiskEngine
from security import (
    SecuritySanitizer,
    audit_ledger,
    crypto_manager,
    rate_limiter,
)
from simulator import BankingSimulator, build_default_propositional_engine
from snowflake_integration.snowflake_id import default_snowflake_generator
from snowflake_integration.snowflake_warehouse import (
    SNOWFLAKE_DDL_SCHEMA,
    SnowflakeWarehouseConnector,
)

# Initialize Bottle application
app = Bottle()

# Core Domain Systems
simulator = BankingSimulator()
warehouse = SnowflakeWarehouseConnector()

# Sync all simulator accounts to Snowflake Dimension Table
for acc in simulator.accounts.values():
    warehouse.sync_account(acc)


# Helper for JSON responses with OWASP Security Headers
def json_response(data: Any, status: int = 200) -> HTTPResponse:
    res = HTTPResponse(body=json.dumps(data, default=str), status=status)
    res.set_header("Content-Type", "application/json")
    res.set_header("Access-Control-Allow-Origin", "*")
    SecuritySanitizer.apply_security_headers(res.headers)
    return res


# ============================================================================
# RESTful API Endpoints (Bottle Framework)
# ============================================================================


@app.route("/api/v1/status", method="GET")
def get_system_status() -> HTTPResponse:
    """Returns health and status of all integrated frameworks."""
    metrics = warehouse.get_summary_statistics()
    status_data = {
        "status": "HEALTHY",
        "service": "Bank Transaction Anomaly Flagger",
        "frameworks": {
            "web_framework": "Bottle (Python Micro-Web)",
            "data_warehouse": "Snowflake Data Cloud / Lakehouse",
            "id_generator": "Twitter Snowflake 64-bit Distributed Generator",
            "subjects": ["DMGT U1/U2", "AI U1", "ADSA U2", "OOPJ"],
        },
        "warehouse_metrics": metrics,
        "accounts_count": len(simulator.accounts),
        "graph_node_count": len(simulator.graph.vertices),
    }
    return json_response(status_data)


@app.route("/api/v1/accounts", method="GET")
def list_accounts() -> HTTPResponse:
    """Returns list of registered bank accounts."""
    acc_list = []
    for acc in simulator.accounts.values():
        acc_list.append(
            {
                "account_id": acc.account_id,
                "holder_name": acc.holder_name,
                "balance": acc.balance,
                "kyc_status": acc.kyc_status.value,
                "device_fingerprint": acc.device_fingerprint,
                "ip_address": acc.ip_address,
                "is_blacklisted": acc.is_blacklisted,
                "avg_amount": acc.historical_avg_amount,
            }
        )
    return json_response({"accounts": acc_list})


@app.route("/api/v1/screen", method="POST")
def screen_transaction() -> HTTPResponse:
    """Primary screening endpoint: evaluates transaction and persists to Snowflake."""
    # 1. Enterprise Security: Rate Limiting
    client_ip = request.environ.get("REMOTE_ADDR", "127.0.0.1")
    allowed, _ = rate_limiter.allow_request(client_ip)
    if not allowed:
        return json_response(
            {"error": "429 Too Many Requests: Rate limit exceeded for client."},
            status=429,
        )

    try:
        data = request.json or {}
    except Exception:
        return json_response({"error": "Invalid JSON payload"}, status=400)

    sender_id = data.get("sender_id", "")
    receiver_id = data.get("receiver_id", "")
    try:
        amount = float(data.get("amount", 0.0))
    except (ValueError, TypeError):
        return json_response({"error": "Amount must be a numeric value."}, status=400)

    # 2. Enterprise Security: OWASP Input Sanitization & Threat Inspection
    combined_input = f"{sender_id} {receiver_id} {data.get('location', '')} {data.get('device_id', '')}"
    is_malicious, detected_threats = SecuritySanitizer.inspect_input(combined_input)
    if is_malicious:
        return json_response(
            {
                "error": "Security Threat Blocked (OWASP Injection Protection)",
                "details": detected_threats,
            },
            status=400,
        )

    if not sender_id or not receiver_id or amount <= 0:
        return json_response(
            {"error": "sender_id, receiver_id, and positive amount are required."},
            status=400,
        )

    # 3. Generate 64-bit Distributed Snowflake Transaction ID
    snowflake_raw_id = default_snowflake_generator.generate_id()
    snowflake_id_str = f"TXN_SNOW_{snowflake_raw_id}"
    decoded_snowflake = default_snowflake_generator.decode_id(snowflake_raw_id)

    # 4. Retrieve accounts or create on the fly
    sender = simulator.accounts.get(sender_id)
    if not sender:
        sender = Account(
            account_id=sender_id,
            holder_name=f"User {sender_id}",
            initial_balance=5000.0,
            kyc_status=KYCStatus.TIER_2_VERIFIED,
            historical_avg_amount=100.0,
        )
        simulator.accounts[sender_id] = sender
        warehouse.sync_account(sender)

    receiver = simulator.accounts.get(receiver_id)
    if not receiver:
        receiver = Account(
            account_id=receiver_id,
            holder_name=f"User {receiver_id}",
            initial_balance=5000.0,
            kyc_status=KYCStatus.TIER_2_VERIFIED,
        )
        simulator.accounts[receiver_id] = receiver
        warehouse.sync_account(receiver)

    # 5. Build Transaction entity (OOPJ)
    channel_str = data.get("channel", "ONLINE_BANKING")
    try:
        channel_enum = ChannelType(channel_str)
    except ValueError:
        channel_enum = ChannelType.ONLINE_BANKING

    txn = Transaction(
        txn_id=snowflake_id_str,
        sender_id=sender_id,
        receiver_id=receiver_id,
        amount=amount,
        timestamp=datetime.now(),
        channel=channel_enum,
        location=data.get("location", "US"),
        device_id=data.get("device_id", sender.device_fingerprint or "dev_default"),
        ip_address=data.get("ip_address", sender.ip_address or "127.0.0.1"),
    )

    # 6. Rational Agent Decision (AI U1 + DMGT U1/U2 + ADSA U2)
    decision = simulator.agent.decide(txn, sender, receiver)

    # 7. Enterprise Security: HMAC-SHA256 Digital Signature
    hmac_sig = crypto_manager.sign_transaction(
        snowflake_id_str,
        sender_id,
        receiver_id,
        amount,
        txn.timestamp.isoformat(),
    )

    # 8. Enterprise Security: Tamper-Proof Cryptographic Hash Chaining
    block_hash = audit_ledger.append_audit_entry(
        txn_id=snowflake_id_str,
        decision=decision.action.value,
        risk_score=decision.posterior_fraud_probability,
        audit_trace=" | ".join(decision.audit_trail),
    )

    # 9. Persist to Snowflake Cloud Data Warehouse
    warehouse.record_screened_transaction(txn, decision)

    # 10. Build response
    response_payload = {
        "snowflake_txn_id": snowflake_id_str,
        "snowflake_metadata": {
            "raw_id": snowflake_raw_id,
            "generated_timestamp_utc": decoded_snowflake.datetime_utc.isoformat(),
            "datacenter_id": decoded_snowflake.datacenter_id,
            "worker_id": decoded_snowflake.worker_id,
            "sequence": decoded_snowflake.sequence,
        },
        "amount": amount,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "security": {
            "hmac_sha256_signature": hmac_sig,
            "tamper_proof_block_hash": block_hash,
            "cipher": "AES-256-GCM + HMAC-SHA256",
        },
        "screening_decision": {
            "action": decision.action.value,
            "risk_tier": decision.risk_tier.value,
            "p_fraud_probability": decision.posterior_fraud_probability,
            "expected_utilities": {
                k.value: v for k, v in decision.expected_utilities.items()
            },
            "fired_rules": decision.fired_rules,
        },
        "audit_trail": decision.audit_trail,
        "snowflake_warehouse_status": "COMMITTED_TO_FACT_TRANSACTIONS",
    }

    return json_response(response_payload, status=200)


@app.route("/api/v1/cobol/screen", method="POST")
def cobol_screen_endpoint() -> HTTPResponse:
    """Invokes ANSI COBOL-85 Mainframe Procedure Division logic."""
    data = request.json or {}
    rec = CobolScreeningRecord(
        txn_id=data.get("txn_id", "TX_COBOL_001"),
        sender_id=data.get("sender_id", "ACC_SENDER"),
        receiver_id=data.get("receiver_id", "ACC_RECV"),
        amount=float(data.get("amount", 100.0)),
        historical_avg=float(data.get("historical_avg", 50.0)),
        is_new_device=bool(data.get("is_new_device", False)),
        is_blacklisted=bool(data.get("is_blacklisted", False)),
    )
    card_80 = CobolMainframeEngine.format_80_col_card(rec)
    decision, risk, reason = CobolMainframeEngine.execute_mainframe_batch(rec)
    return json_response(
        {
            "engine": "ANSI COBOL-85 (cobol/FRAUDSCR.cbl)",
            "mainframe_80_col_card": card_80,
            "ws_decision": decision,
            "ws_risk_score": risk,
            "ws_flag_reason": reason,
        }
    )


@app.route("/api/v1/fortran/var", method="POST")
def fortran_var_endpoint() -> HTTPResponse:
    """Executes Fortran Monte Carlo Value-at-Risk (VaR 99%) & CVaR engine."""
    data = request.json or {}
    base_amt = float(data.get("amount", 1000.0))
    p_fraud = float(data.get("p_fraud", 0.15))
    n_sims = int(data.get("simulations", 5000))
    res = FortranRiskEngine.simulate_var_cvar(base_amt, p_fraud, n_simulations=n_sims)
    res["engine"] = "Fortran 90/2003 (fortran/risk_monte_carlo.f90)"
    return json_response(res)


@app.route("/api/v1/security/audit_ledger", method="GET")
def get_audit_ledger() -> HTTPResponse:
    """Returns the cryptographic hash-chained audit ledger and verifies integrity."""
    is_valid, bad_block = audit_ledger.verify_chain_integrity()
    return json_response(
        {
            "chain_length": len(audit_ledger.chain),
            "is_cryptographically_valid": is_valid,
            "corrupted_block": bad_block,
            "latest_block_hash": audit_ledger.latest_hash,
            "chain": audit_ledger.chain[-20:],
        }
    )


@app.route("/api/v1/transactions", method="GET")
def get_transactions() -> HTTPResponse:
    """Queries screened transactions stored in Snowflake."""
    limit = int(request.query.get("limit", 20))
    records = warehouse.query_recent_transactions(limit=limit)
    return json_response({"records": records, "count": len(records)})


@app.route("/api/v1/snowflake/schema", method="GET")
def get_snowflake_schema() -> HTTPResponse:
    """Returns Snowflake DDL schema."""
    return json_response({"snowflake_ddl": SNOWFLAKE_DDL_SCHEMA})


@app.route("/api/v1/rules", method="GET")
def list_rules() -> HTTPResponse:
    """Returns DMGT Propositional Rules and Truth Tables."""
    rules_data = []
    for r in simulator.logic_engine.rules:
        rules_data.append(
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "formula": r.condition.to_formal_string(),
                "flag": r.flag_consequent,
                "weight": r.base_risk_weight,
                "truth_table": r.generate_truth_table(),
            }
        )
    return json_response({"rules": rules_data})


@app.route("/api/v1/run_benchmark", method="POST")
def run_benchmark() -> HTTPResponse:
    """Executes the benchmark suite and commits results to Snowflake."""
    benchmark_results = simulator.run_benchmark_scenarios()
    for txn, decision in benchmark_results:
        warehouse.record_screened_transaction(txn, decision)
    return json_response(
        {
            "message": "Benchmark scenarios executed and committed to Snowflake.",
            "transactions_processed": len(benchmark_results),
        }
    )


# ============================================================================
# Interactive Web Dashboard (Bottle Framework HTML/CSS/JS)
# ============================================================================

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Bank Transaction Anomaly Flagger</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #151d2e;
      --border: #23324d;
      --text: #e2e8f0;
      --text-dim: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.2);
      --green: #22c55e;
      --yellow: #eab308;
      --red: #ef4444;
      --purple: #a855f7;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; margin-bottom: 24px; }
    h1 { font-size: 22px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; }
    .badge { background: var(--border); color: var(--accent); font-size: 11px; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; font-weight: 600; }
    .framework-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
    .ftag { background: #1e293b; color: var(--text-dim); font-size: 11px; padding: 2px 8px; border-radius: 12px; border: 1px solid var(--border); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 24px; }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .card h2 { font-size: 16px; margin-bottom: 16px; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
    .stat-val { font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 4px; }
    .stat-sub { font-size: 12px; color: var(--text-dim); }
    
    label { display: block; font-size: 12px; font-weight: 600; color: var(--text-dim); margin-bottom: 6px; }
    input, select { width: 100%; padding: 10px; background: #0f172a; border: 1px solid var(--border); border-radius: 6px; color: #fff; font-size: 13px; margin-bottom: 14px; }
    input:focus, select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }
    button { background: #0284c7; color: #fff; border: none; padding: 10px 18px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 13px; transition: all 0.2s; }
    button:hover { background: #0369a1; }
    button.secondary { background: #334155; }
    button.secondary:hover { background: #475569; }
    
    table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
    th { background: #1e293b; color: var(--text-dim); padding: 10px 12px; font-weight: 600; border-bottom: 1px solid var(--border); }
    td { padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text); }
    tr:hover { background: #1e293b55; }
    
    .status-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    .status-APPROVE { background: #14532d; color: #4ade80; border: 1px solid #166534; }
    .status-FLAG_MANUAL_REVIEW { background: #713f12; color: #fde047; border: 1px solid #854d0e; }
    .status-FREEZE_ACCOUNT { background: #7f1d1d; color: #f87171; border: 1px solid #991b1b; }
    
    .console-box { background: #030712; border: 1px solid var(--border); border-radius: 6px; padding: 14px; font-family: monospace; font-size: 12px; line-height: 1.5; color: #38bdf8; max-height: 240px; overflow-y: auto; white-space: pre-wrap; }
    .flex-row { display: flex; gap: 12px; }
  </style>
</head>
<body>

  <header>
    <div>
      <h1>Bank Transaction Anomaly Flagger <span class="badge">First-Pass Screen</span></h1>
      <div class="framework-tags">
        <span class="ftag">Bottle WSGI Micro-Framework</span>
        <span class="ftag">Snowflake 64-bit Distributed ID</span>
        <span class="ftag">Snowflake Data Warehouse DDL</span>
        <span class="ftag">DMGT U1/U2</span>
        <span class="ftag">AI U1 Rational Agent</span>
        <span class="ftag">ADSA U2 Graphs</span>
        <span class="ftag">OOPJ</span>
      </div>
    </div>
    <div>
      <button class="secondary" onclick="runBenchmark()">Run Full Benchmark</button>
      <button onclick="refreshData()">Refresh Warehouse</button>
    </div>
  </header>

  <!-- Metric Overview Cards -->
  <div class="grid">
    <div class="card">
      <h2>Snowflake Ledger Transactions</h2>
      <div class="stat-val" id="stat-count">-</div>
      <div class="stat-sub">Persisted in FACT_TRANSACTIONS</div>
    </div>
    <div class="card">
      <h2>Average Network Risk</h2>
      <div class="stat-val" id="stat-risk">-</div>
      <div class="stat-sub">Mean posterior fraud probability</div>
    </div>
    <div class="card">
      <h2>Total Volume Processed</h2>
      <div class="stat-val" id="stat-vol">-</div>
      <div class="stat-sub">Screened financial capital</div>
    </div>
  </div>

  <!-- Interactive Screening and Live Trace -->
  <div class="grid" style="grid-template-columns: 1fr 1.2fr;">
    <!-- Form Card -->
    <div class="card">
      <h2>Submit Transaction for Screening</h2>
      <form id="screen-form" onsubmit="handleScreen(event)">
        <div class="flex-row">
          <div style="flex:1;">
            <label>Sender Account ID</label>
            <input type="text" id="sender_id" value="ACC_CHARLIE" required>
          </div>
          <div style="flex:1;">
            <label>Receiver Account ID</label>
            <input type="text" id="receiver_id" value="ACC_BOB" required>
          </div>
        </div>
        <div class="flex-row">
          <div style="flex:1;">
            <label>Amount ($)</label>
            <input type="number" step="0.01" id="amount" value="4500.00" required>
          </div>
          <div style="flex:1;">
            <label>Payment Channel</label>
            <select id="channel">
              <option value="ONLINE_BANKING">ONLINE_BANKING</option>
              <option value="MOBILE_APP">MOBILE_APP</option>
              <option value="WIRE_TRANSFER">WIRE_TRANSFER</option>
              <option value="ATM">ATM</option>
            </select>
          </div>
        </div>
        <div class="flex-row">
          <div style="flex:1;">
            <label>Device ID</label>
            <input type="text" id="device_id" value="DEV_UNKNOWN_ATTACKER">
          </div>
          <div style="flex:1;">
            <label>Location</label>
            <input type="text" id="location" value="FOREIGN_ISLANDS">
          </div>
        </div>
        <button type="submit" style="width: 100%;">Screen Transaction with AI Rational Agent</button>
      </form>
    </div>

    <!-- Live Telemetry Trace -->
    <div class="card">
      <h2>Screening Telemetry & Logic Trace</h2>
      <div class="console-box" id="audit-console">Ready. Submit a transaction or run benchmark to see multi-disciplinary audit trace...</div>
    </div>
  </div>

  <!-- Screened Transactions Table -->
  <div class="card">
    <h2>Snowflake FACT_TRANSACTIONS Real-Time Ledger</h2>
    <div style="overflow-x: auto;">
      <table>
        <thead>
          <tr>
            <th>Snowflake Txn ID</th>
            <th>Sender</th>
            <th>Receiver</th>
            <th>Amount</th>
            <th>P(Fraud)</th>
            <th>Risk Tier</th>
            <th>Rational Decision</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody id="txn-tbody">
          <tr><td colspan="8" style="text-align: center; color: var(--text-dim);">Loading transactions...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    async function refreshData() {
      try {
        const statusRes = await fetch('/api/v1/status');
        const statusData = await statusRes.json();
        document.getElementById('stat-count').innerText = statusData.warehouse_metrics.total_transactions;
        document.getElementById('stat-risk').innerText = statusData.warehouse_metrics.avg_risk;
        document.getElementById('stat-vol').innerText = '$' + Number(statusData.warehouse_metrics.total_volume).toLocaleString();

        const txnsRes = await fetch('/api/v1/transactions?limit=25');
        const txnsData = await txnsRes.json();
        const tbody = document.getElementById('txn-tbody');
        tbody.innerHTML = '';
        if (txnsData.records.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-dim);">No transactions found. Click "Run Full Benchmark".</td></tr>';
          return;
        }
        txnsData.records.forEach(r => {
          const row = document.createElement('tr');
          row.innerHTML = `
            <td><code>${r.SNOWFLAKE_TXN_ID}</code></td>
            <td>${r.SENDER_ID}</td>
            <td>${r.RECEIVER_ID}</td>
            <td>$${Number(r.AMOUNT).toFixed(2)}</td>
            <td>${Number(r.P_FRAUD_SCORE).toFixed(3)}</td>
            <td><span class="badge">${r.RISK_TIER}</span></td>
            <td><span class="status-badge status-${r.ACTION_DECISION}">${r.ACTION_DECISION}</span></td>
            <td style="color:var(--text-dim); font-size:11px;">${r.TIMESTAMP_UTC}</td>
          `;
          tbody.appendChild(row);
        });
      } catch (err) {
        console.error(err);
      }
    }

    async function handleScreen(e) {
      e.preventDefault();
      const payload = {
        sender_id: document.getElementById('sender_id').value,
        receiver_id: document.getElementById('receiver_id').value,
        amount: parseFloat(document.getElementById('amount').value),
        channel: document.getElementById('channel').value,
        device_id: document.getElementById('device_id').value,
        location: document.getElementById('location').value,
      };

      const res = await fetch('/api/v1/screen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      const consoleBox = document.getElementById('audit-console');
      let text = `=== TRANSACTION SCREENED ===\\n`;
      text += `Snowflake Txn ID: ${data.snowflake_txn_id}\\n`;
      text += `Timestamp UTC   : ${data.snowflake_metadata.generated_timestamp_utc}\\n`;
      text += `Datacenter ID   : ${data.snowflake_metadata.datacenter_id} | Worker ID: ${data.snowflake_metadata.worker_id} | Seq: ${data.snowflake_metadata.sequence}\\n`;
      text += `Decision        : ${data.screening_decision.action} (Risk: ${data.screening_decision.risk_tier}, P(Fraud)=${data.screening_decision.p_fraud_probability.toFixed(3)})\\n\\n`;
      text += `[Expected Utility Matrix]:\\n`;
      for (const [act, eu] of Object.entries(data.screening_decision.expected_utilities)) {
        text += `  * ${act.padEnd(20)} => $${eu.toFixed(2)}\\n`;
      }
      text += `\\n[Subsystem Traces]:\\n`;
      data.audit_trail.forEach(t => text += `  * ${t}\\n`);
      consoleBox.innerText = text;

      refreshData();
    }

    async function runBenchmark() {
      const consoleBox = document.getElementById('audit-console');
      consoleBox.innerText = 'Executing 6 multi-subject benchmark scenarios in simulator...';
      const res = await fetch('/api/v1/run_benchmark', { method: 'POST' });
      const data = await res.json();
      consoleBox.innerText = `Benchmark Completed: ${data.transactions_processed} transactions screened and stored into Snowflake FACT_TRANSACTIONS.`;
      refreshData();
    }

    window.onload = refreshData;
  </script>
</body>
</html>
"""


# Directory path to frontend assets
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")


@app.route("/static/<filepath:path>", method="GET")
def serve_static(filepath: str) -> Any:
    """Serves static CSS and JS assets from frontend/static."""
    return static_file(filepath, root=STATIC_DIR)


@app.route("/css/<filepath:path>", method="GET")
def serve_css(filepath: str) -> Any:
    """Serves CSS files from css/ directory."""
    css_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "css")
    return static_file(filepath, root=css_dir)


@app.route("/js/<filepath:path>", method="GET")
def serve_js(filepath: str) -> Any:
    """Serves JS files from js/ directory."""
    js_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js")
    return static_file(filepath, root=js_dir)


@app.route("/style.css", method="GET")
def serve_style_root() -> Any:
    """Serves root style.css."""
    return static_file("style.css", root=os.path.dirname(os.path.abspath(__file__)))


@app.route("/script.js", method="GET")
def serve_script_root() -> Any:
    """Serves root script.js."""
    return static_file("script.js", root=os.path.dirname(os.path.abspath(__file__)))


@app.route("/", method="GET")
def serve_dashboard() -> Any:
    """Serves the rich interactive single-page dashboard website."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return static_file("index.html", root=FRONTEND_DIR)
    response.set_header("Content-Type", "text/html; charset=utf-8")
    return DASHBOARD_HTML


def run_web_server(host: str = "127.0.0.1", port: int = 3030) -> None:
    """Starts the Bottle WSGI HTTP server."""
    # Allow port override from environment variable or command line argument
    if "PORT" in os.environ:
        try:
            port = int(os.environ["PORT"])
        except ValueError:
            pass

    import sys
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    print(f"\n=======================================================")
    print(f" Starting Bottle Web Server on http://localhost:{port}/")
    print(f" Web Dashboard & RESTful Screening API Ready")
    print(f" Integrated: Bottle, Snowflake ID Generator, Snowflake DDL")
    print(f"=======================================================\n")
    bottle.run(app=app, host=host, port=port, quiet=False)


if __name__ == "__main__":
    run_web_server()
