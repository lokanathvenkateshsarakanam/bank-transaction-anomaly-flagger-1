/**
 * Bank Transaction Anomaly Flagger - Frontend Client Engine
 * Integrates Bottle API, Snowflake ID & Warehouse, DMGT Logic, and ADSA Graph Visualizer.
 */

// Global State
let currentGraphData = { nodes: [], edges: [] };
let cachedRules = [];
let animFrameId = null;

// Preset Scenarios
const PRESETS = {
  routine: {
    sender_id: "ACC_ALICE",
    receiver_id: "ACC_BOB",
    amount: 45.0,
    channel: "MOBILE_APP",
    device_id: "DEV_ALICE_PHONE",
    ip_address: "192.168.1.10",
    location: "US",
  },
  ato: {
    sender_id: "ACC_CHARLIE",
    receiver_id: "ACC_BOB",
    amount: 4500.0,
    channel: "ONLINE_BANKING",
    device_id: "DEV_UNKNOWN_ATTACKER",
    ip_address: "45.12.89.200",
    location: "FOREIGN_ISLANDS",
  },
  cycle: {
    sender_id: "ACC_LAYER_C",
    receiver_id: "ACC_LAYER_A",
    amount: 9300.0,
    channel: "WIRE_TRANSFER",
    device_id: "DEV_CORP_C",
    ip_address: "127.0.0.1",
    location: "US",
  },
  smurf: {
    sender_id: "ACC_MULE_1",
    receiver_id: "ACC_COLLECTOR_X",
    amount: 9200.0,
    channel: "ONLINE_BANKING",
    device_id: "DEV_FARM_X",
    ip_address: "10.0.0.99",
    location: "US",
  },
  blacklist: {
    sender_id: "ACC_MALLORY_FRAUD",
    receiver_id: "ACC_BOB",
    amount: 1200.0,
    channel: "WIRE_TRANSFER",
    device_id: "DEV_DARK_NET_01",
    ip_address: "185.220.101.5",
    location: "US",
  },
  puppet: {
    sender_id: "ACC_PUPPET_CLEAN",
    receiver_id: "ACC_ALICE",
    amount: 200.0,
    channel: "MOBILE_APP",
    device_id: "DEV_DARK_NET_01", // Shared device with Mallory!
    ip_address: "185.220.101.5",
    location: "US",
  },
};

// ============================================================================
// Initialization & Navigation
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  loadPresets();
  refreshWarehouseData();
  loadRulesLab();
  initNetworkGraph();
  window.addEventListener("resize", resizeCanvas);
});

function initTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.classList.add("active");

      if (targetId === "tab-graph") {
        setTimeout(resizeCanvas, 50);
      }
    });
  });
}

function loadPresets() {
  window.applyPreset = function (key) {
    const p = PRESETS[key];
    if (!p) return;
    document.getElementById("sender_id").value = p.sender_id;
    document.getElementById("receiver_id").value = p.receiver_id;
    document.getElementById("amount").value = p.amount.toFixed(2);
    document.getElementById("channel").value = p.channel;
    document.getElementById("device_id").value = p.device_id;
    document.getElementById("ip_address").value = p.ip_address;
    document.getElementById("location").value = p.location;
  };
}

// ============================================================================
// Screening Execution & Telemetry Rendering
// ============================================================================

window.handleScreenTransaction = async function (e) {
  if (e) e.preventDefault();

  const payload = {
    sender_id: document.getElementById("sender_id").value.trim(),
    receiver_id: document.getElementById("receiver_id").value.trim(),
    amount: parseFloat(document.getElementById("amount").value),
    channel: document.getElementById("channel").value,
    device_id: document.getElementById("device_id").value.trim(),
    ip_address: document.getElementById("ip_address").value.trim(),
    location: document.getElementById("location").value.trim(),
  };

  const btn = document.getElementById("submit-btn");
  btn.innerText = "Screening via AI Rational Agent...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/v1/screen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (res.status !== 200) {
      alert("Error: " + (data.error || "Screening failed"));
      return;
    }

    renderScreeningResult(data);
    refreshWarehouseData();
    fetchGraphData();
  } catch (err) {
    console.error(err);
    alert("Connection error to Bottle server.");
  } finally {
    btn.innerText = "Screen Transaction with AI Rational Agent";
    btn.disabled = false;
  }
};

function renderScreeningResult(data) {
  const dec = data.screening_decision;
  const meta = data.snowflake_metadata;

  // Decision Badge
  const badgeEl = document.getElementById("decision-badge");
  badgeEl.className = `decision-badge badge-${dec.action}`;
  badgeEl.innerText = dec.action;

  // Snowflake ID Details
  document.getElementById("snow-id-val").innerText = data.snowflake_txn_id;
  document.getElementById("snow-time").innerText = meta.generated_timestamp_utc;
  document.getElementById("snow-dc").innerText = meta.datacenter_id;
  document.getElementById("snow-worker").innerText = meta.worker_id;
  document.getElementById("snow-seq").innerText = meta.sequence;

  // Risk Score Meter
  const pct = Math.min(100, Math.max(0, dec.p_fraud_probability * 100));
  const fillEl = document.getElementById("risk-meter-fill");
  fillEl.style.width = pct + "%";
  document.getElementById("risk-val-text").innerText = `${pct.toFixed(1)}% (${dec.risk_tier})`;

  if (pct < 20) {
    fillEl.style.backgroundColor = "var(--color-approve)";
  } else if (pct < 55) {
    fillEl.style.backgroundColor = "var(--color-flag)";
  } else {
    fillEl.style.backgroundColor = "var(--color-freeze)";
  }

  // Expected Utility Payoffs
  const utGrid = document.getElementById("utility-grid");
  utGrid.innerHTML = "";
  const utilities = dec.expected_utilities;
  for (const [actionName, eu] of Object.entries(utilities)) {
    const isOptimal = actionName === dec.action;
    const card = document.createElement("div");
    card.className = `utility-card ${isOptimal ? "optimal" : ""}`;
    card.innerHTML = `
      <div class="utility-title">${actionName}${isOptimal ? " ★ (Optimal)" : ""}</div>
      <div class="utility-val" style="color: ${eu >= 0 ? "var(--color-approve)" : "var(--color-freeze)"}">
        $${Number(eu).toFixed(2)}
      </div>
    `;
    utGrid.appendChild(card);
  }

  // Audit Trail Console
  const consoleEl = document.getElementById("audit-console");
  let trailText = `[Screening Timestamp: ${new Date().toISOString()}]\n`;
  trailText += `Transaction: ${data.snowflake_txn_id} ($${Number(data.amount).toFixed(2)})\n`;
  trailText += `Route: ${data.sender_id} -> ${data.receiver_id}\n`;
  trailText += `Fired Rules: ${dec.fired_rules.length ? dec.fired_rules.join(", ") : "None (Clean)"}\n\n`;
  trailText += `--- SUBSYSTEM REASONING TRACE ---\n`;
  data.audit_trail.forEach((t) => {
    trailText += `${t}\n`;
  });
  consoleEl.innerText = trailText;
}

// ============================================================================
// Snowflake Warehouse Ledger & Statistics
// ============================================================================

async function refreshWarehouseData() {
  try {
    const statusRes = await fetch("/api/v1/status");
    const statusData = await statusRes.json();
    const metrics = statusData.warehouse_metrics;

    document.getElementById("stat-total-txns").innerText = metrics.total_transactions;
    document.getElementById("stat-avg-risk").innerText = (metrics.avg_risk * 100).toFixed(1) + "%";
    document.getElementById("stat-total-vol").innerText = "$" + Number(metrics.total_volume).toLocaleString();

    const txnsRes = await fetch("/api/v1/transactions?limit=50");
    const txnsData = await txnsRes.json();
    renderTransactionsTable(txnsData.records);
  } catch (err) {
    console.error("Failed to refresh warehouse data:", err);
  }
}

function renderTransactionsTable(records) {
  const tbody = document.getElementById("warehouse-tbody");
  tbody.innerHTML = "";

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No records in Snowflake. Run the benchmark or screen a transaction.</td></tr>`;
    return;
  }

  records.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${r.SNOWFLAKE_TXN_ID}</code></td>
      <td><strong>${r.SENDER_ID}</strong></td>
      <td><strong>${r.RECEIVER_ID}</strong></td>
      <td>$${Number(r.AMOUNT).toFixed(2)}</td>
      <td>${(Number(r.P_FRAUD_SCORE) * 100).toFixed(1)}%</td>
      <td><span class="badge-tag">${r.RISK_TIER}</span></td>
      <td><span class="decision-badge badge-${r.ACTION_DECISION}" style="font-size:11px; padding:3px 10px;">${r.ACTION_DECISION}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

window.runFullBenchmark = async function () {
  const consoleEl = document.getElementById("audit-console");
  consoleEl.innerText = "Executing 6 comprehensive benchmark scenarios in Python simulator...";
  try {
    const res = await fetch("/api/v1/run_benchmark", { method: "POST" });
    const data = await res.json();
    consoleEl.innerText = `Success: ${data.transactions_processed} scenarios executed, screened, and committed to Snowflake FACT_TRANSACTIONS.`;
    refreshWarehouseData();
    fetchGraphData();
  } catch (err) {
    alert("Benchmark failed to run: " + err);
  }
};

// ============================================================================
// DMGT Logic Lab (U1 Truth Tables & U2 Relations)
// ============================================================================

async function loadRulesLab() {
  try {
    const res = await fetch("/api/v1/rules");
    const data = await res.json();
    cachedRules = data.rules || [];
    renderTruthTables(cachedRules);
  } catch (err) {
    console.error("Failed to load rules:", err);
  }
}

function renderTruthTables(rules) {
  const container = document.getElementById("rules-container");
  if (!container) return;
  container.innerHTML = "";

  rules.forEach((rule) => {
    const ruleCard = document.createElement("div");
    ruleCard.className = "card";
    ruleCard.style.marginBottom = "18px";

    const vars = Object.keys(rule.truth_table[0]).filter((k) => k !== "EVALUATION");

    let tableHtml = `
      <div class="card-title">
        <span>${rule.name} <code style="color:var(--accent-purple)">[${rule.rule_id}]</code></span>
        <span class="badge-tag">Weight: ${rule.weight}</span>
      </div>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
        Formal Implication: <code>${rule.formula} → ${rule.flag}</code>
      </p>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              ${vars.map((v) => `<th>${v}</th>`).join("")}
              <th>Formula Evaluation</th>
            </tr>
          </thead>
          <tbody>
            ${rule.truth_table
              .map(
                (row) => `
              <tr style="${row.EVALUATION ? "background: rgba(239, 68, 68, 0.1);" : ""}">
                ${vars.map((v) => `<td><code>${row[v]}</code></td>`).join("")}
                <td><strong style="color: ${row.EVALUATION ? "var(--color-freeze)" : "var(--color-approve)"}">
                  ${row.EVALUATION ? "TRUE (FIRES)" : "FALSE"}
                </strong></td>
              </tr>
            `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `;

    ruleCard.innerHTML = tableHtml;
    container.appendChild(ruleCard);
  });
}

// ============================================================================
// ADSA Network Graph Visualizer (Canvas Rendering with Circular Layering)
// ============================================================================

let canvas, ctx;
let nodesMap = {};
let edgesList = [];

function initNetworkGraph() {
  canvas = document.getElementById("network-canvas");
  if (!canvas) return;
  ctx = canvas.getContext("2d");
  resizeCanvas();
  fetchGraphData();
}

function resizeCanvas() {
  if (!canvas) return;
  const parent = canvas.parentElement;
  canvas.width = parent.clientWidth;
  canvas.height = parent.clientHeight;
  drawGraph();
}

async function fetchGraphData() {
  try {
    const accRes = await fetch("/api/v1/accounts");
    const accData = await accRes.json();
    const txnsRes = await fetch("/api/v1/transactions?limit=30");
    const txnsData = await txnsRes.json();

    buildGraphStructure(accData.accounts, txnsData.records);
    drawGraph();
  } catch (err) {
    console.error("Failed to fetch graph data:", err);
  }
}

function buildGraphStructure(accounts, txns) {
  nodesMap = {};
  edgesList = [];

  const width = canvas ? canvas.width : 800;
  const height = canvas ? canvas.height : 500;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.38;

  // Position nodes in a circular formation
  const n = accounts.length;
  accounts.forEach((acc, i) => {
    const angle = (i / n) * 2 * Math.PI;
    nodesMap[acc.account_id] = {
      id: acc.account_id,
      name: acc.holder_name,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      is_blacklisted: acc.is_blacklisted,
      device: acc.device_fingerprint,
    };
  });

  // Build edges
  txns.forEach((t) => {
    if (nodesMap[t.SENDER_ID] && nodesMap[t.RECEIVER_ID]) {
      const isCycleEdge =
        (t.SENDER_ID === "ACC_LAYER_C" && t.RECEIVER_ID === "ACC_LAYER_A") ||
        (t.SENDER_ID === "ACC_LAYER_A" && t.RECEIVER_ID === "ACC_LAYER_B") ||
        (t.SENDER_ID === "ACC_LAYER_B" && t.RECEIVER_ID === "ACC_LAYER_C");

      edgesList.push({
        source: nodesMap[t.SENDER_ID],
        target: nodesMap[t.RECEIVER_ID],
        amount: t.AMOUNT,
        decision: t.ACTION_DECISION,
        isCycle: isCycleEdge,
      });
    }
  });
}

function drawGraph() {
  if (!ctx || !canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 1. Draw Edges
  edgesList.forEach((edge) => {
    const { source, target, isCycle } = edge;

    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    ctx.lineTo(target.x, target.y);

    if (isCycle) {
      ctx.strokeStyle = "rgba(239, 68, 68, 0.85)";
      ctx.lineWidth = 3.0;
    } else {
      ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
      ctx.lineWidth = 1.5;
    }
    ctx.stroke();

    // Draw Arrowhead
    const angle = Math.atan2(target.y - source.y, target.x - source.x);
    const arrowLength = 12;
    const arrowX = target.x - 22 * Math.cos(angle);
    const arrowY = target.y - 22 * Math.sin(angle);

    ctx.beginPath();
    ctx.moveTo(arrowX, arrowY);
    ctx.lineTo(arrowX - arrowLength * Math.cos(angle - Math.PI / 6), arrowY - arrowLength * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(arrowX - arrowLength * Math.cos(angle + Math.PI / 6), arrowY - arrowLength * Math.sin(angle + Math.PI / 6));
    ctx.fillStyle = isCycle ? "#ef4444" : "#38bdf8";
    ctx.fill();
  });

  // 2. Draw Nodes
  Object.values(nodesMap).forEach((node) => {
    ctx.beginPath();
    ctx.arc(node.x, node.y, 16, 0, 2 * Math.PI);

    if (node.is_blacklisted) {
      ctx.fillStyle = "#ef4444";
      ctx.shadowColor = "#ef4444";
      ctx.shadowBlur = 12;
    } else if (node.device === "DEV_FARM_X") {
      ctx.fillStyle = "#a855f7"; // Mule Farm Equivalence Class
      ctx.shadowColor = "#a855f7";
      ctx.shadowBlur = 8;
    } else {
      ctx.fillStyle = "#0284c7";
      ctx.shadowBlur = 0;
    }

    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Node ID Label
    ctx.fillStyle = "#f1f5f9";
    ctx.font = "11px -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(node.id, node.x, node.y - 22);
  });
}
