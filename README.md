# Bank Transaction Anomaly Flagger (First-Pass Fraud Screen)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Flokanathvenkateshsarakanam%2Fbank-transaction-anomaly-flagger-1)

> **Problem Statement:** A bank wants a first-pass fraud screen before a transaction reaches manual review.  
> **Curriculum Integration:** 
> - **DMGT (U1)**: Propositional-Logic Rule Engine  
> - **DMGT (U2)**: Transaction Relations & Equivalence Classes  
> - **AI (U1)**: Rational-Agent Decision Rules (PEAS & Expected Utility Optimization)  
> - **ADSA (U2)**: Transaction Network as a Directed Weighted Graph (Cycle Detection & Flow Analysis)  
> - **OOPJ**: Object-Oriented Account & Transaction Domain Architecture  
> - **Bottle Framework**: WSGI Micro-Web Service & Interactive Telemetry Dashboard  
> - **Snowflake Framework**: 64-bit Distributed ID Generation & Cloud Data Warehouse / Lakehouse DDL Ingestion  
> - **Language**: Python 3.10+ (Standard Library + Bottle + Snowflake Connector)

---

## 1. Curriculum Architecture & Theoretical Mapping

| Subject & Unit | Theoretical Concept | Concrete Implementation in Code |
| :--- | :--- | :--- |
| **DMGT (U1)** | Propositional Logic, Well-Formed Formulas (WFF), Logical Connectives ($\neg, \land, \lor, \implies, \iff$), Modus Ponens Inference, Truth Tables | `dmgt/propositional_engine.py`: AST classes (`Prop`, `Not`, `And`, `Or`, `Implies`), `PropositionalFraudRule`, `generate_truth_table()`, `PropositionalLogicEngine` |
| **DMGT (U2)** | Binary Relations $R \subseteq A \times A$, Reflexivity, Symmetry, Transitivity, Equivalence Classes $[x]$, Quotient Sets $A / R$, Relational Composition $R \circ S$, Transitive Closure $R^+$ | `dmgt/relations.py`: `BinaryRelation`, `EquivalenceRelation`, `AccountIdentityRelationManager`, `compose()`, `compute_transitive_closure()` |
| **AI (U1)** | Rational Agent, PEAS Framework, Partially Observable Adversarial Environment, Utility-Based Decision Policy ($\arg\max_a EU(a)$) | `ai/agent.py`: `RationalFraudScreeningAgent`, `Percept`, `DecisionOutcome`, `evaluate_expected_utility()`, `decide()` |
| **ADSA (U2)** | Transaction Network Directed Graph, Adjacency Lists, 3-Color DFS Cycle Detection (Circular Money Laundering), Fan-In/Fan-Out Flow Velocity (Smurfing), BFS Shortest Path to Blacklisted Entities | `adsa/graph.py`: `TransactionGraph`, `Edge`; `adsa/cycle_detector.py`: `CycleDetector`; `adsa/flow_analyzer.py`: `GraphFlowAnalyzer` |
| **OOPJ** | Encapsulation, Data Integrity & Invariants, State Lifecycle Transitions, Polymorphism | `models/account.py`: `Account` (private fields, invariants, moving average updates); `models/transaction.py`: `Transaction` |
| **Bottle** | WSGI Micro-Web Framework, RESTful JSON Routing, Embedded Live Dashboard | `web_app.py`: `app = Bottle()`, `/api/v1/screen`, `/api/v1/status`, `/api/v1/transactions`, single-page dashboard |
| **Snowflake** | 64-bit Distributed ID Generator (Twitter Snowflake specification) & Cloud Data Warehouse Schema / Ingestion Engine | `snowflake_integration/snowflake_id.py`: `SnowflakeIdGenerator`; `snowflake_integration/snowflake_warehouse.py`: `SnowflakeWarehouseConnector`, DDL (`FACT_TRANSACTIONS`, `DIM_ACCOUNTS`, `DIM_ANOMALY_AUDIT`) |

---

## 2. Theoretical Breakdown

### 2.1 DMGT Unit 1: Propositional Logic Rule Engine
Every financial anomaly rule is formulated as a formal logical implication:
$$\text{Condition} \implies \text{FlagConsequent}$$

Where $\text{Condition}$ is a Well-Formed Formula (WFF) composed of atomic propositions:
- $P_{\text{HIGH\_AMOUNT}}$: $\text{Amount} > 3 \times \mu_{\text{historical}}$
- $P_{\text{NEW\_DEVICE}}$: Device fingerprint differs from registered baseline
- $P_{\text{OFF\_HOURS}}$: Transaction timestamp between 01:00 AM and 05:00 AM
- $P_{\text{FOREIGN\_LOCATION}}$: Transaction originates outside domestic region
- $P_{\text{NEW\_ACCOUNT}}$: Account age $< 14$ days
- $P_{\text{UNVERIFIED\_KYC}}$: Account verification level is Tier 1 Unverified

**Example Rules:**
1. **Account Takeover (ATO):**
   $$(P_{\text{HIGH\_AMOUNT}} \land P_{\text{NEW\_DEVICE}}) \implies \text{SUSPECT\_ACCOUNT\_TAKEOVER}$$
2. **Synthetic Onboarding Fraud:**
   $$(P_{\text{NEW\_ACCOUNT}} \land P_{\text{UNVERIFIED\_KYC}} \land P_{\text{HIGH\_AMOUNT}}) \implies \text{SUSPECT\_SYNTHETIC\_ONBOARDING}$$
3. **Off-Hours Exfiltration:**
   $$(P_{\text{OFF\_HOURS}} \land (P_{\text{FOREIGN\_LOCATION}} \lor P_{\text{NEW\_DEVICE}})) \implies \text{SUSPECT\_OFF\_HOURS\_EXFILTRATION}$$

### 2.2 DMGT Unit 2: Transaction Relations & Equivalence Classes
Let $A$ be the universe of bank accounts.
We define identity relations $R_{\text{device}}, R_{\text{IP}}, R_{\text{SSN}} \subseteq A \times A$:
$$(x, y) \in R_{\text{device}} \iff \text{Device}(x) = \text{Device}(y)$$

- **Equivalence Properties:**
  1. **Reflexive:** $\forall x \in A, (x, x) \in R$ (an account shares its own device).
  2. **Symmetric:** $(x, y) \in R \implies (y, x) \in R$.
  3. **Transitive:** $(x, y) \in R \land (y, z) \in R \implies (x, z) \in R$.
- **Equivalence Class $[x]$:**
  $$[x] = \{ y \in A \mid (x, y) \in R \}$$
  The set of all accounts linked to the same physical hardware or identity cluster.
- **Quotient Set $A / R$:**
  Partitions the banking universe into disjoint device/identity clusters. If any member in $[x]$ is blacklisted, all related accounts inherit high scrutiny!
- **Composition of Relations ($R \circ S$):**
  $$(x, z) \in R \circ S \iff \exists y \in A \text{ s.t. } (x, y) \in R \land (y, z) \in S$$
  Used for multi-hop fund flow reachability.

### 2.3 AI Unit 1: Rational Agent (PEAS & Expected Utility)
- **Performance Measure ($P$):** Maximize bank utility:
  $$\text{Utility} = \text{Fraud Prevented} - \text{False-Positive Friction} - \text{Manual Review Labor Cost} - \text{Fraud Losses}$$
- **Environment ($E$):** Partially observable, stochastic, sequential, dynamic, multi-agent adversarial.
- **Actuators ($A$):** Action space $\mathcal{A} = \{\text{APPROVE}, \text{FLAG\_MANUAL\_REVIEW}, \text{FREEZE\_ACCOUNT}\}$.
- **Sensors ($S$):** Transaction attributes, DMGT logic outputs, DMGT equivalence relations, ADSA graph topology.
- **Rational Decision Policy:**
  Given posterior fraud belief $p = P(\text{Fraud} \mid \text{Percept})$, the agent calculates the Expected Utility $EU(a)$ for each action $a \in \mathcal{A}$:
  $$EU(\text{APPROVE}) = p \cdot (-\text{amount}) + (1 - p) \cdot (0.01 \cdot \text{amount})$$
  $$EU(\text{FLAG}) = p \cdot (0.90 \cdot \text{amount} - C_{\text{review}}) + (1 - p) \cdot (-C_{\text{review}} - 0.02 \cdot \text{amount})$$
  $$EU(\text{FREEZE}) = p \cdot (\text{amount}) + (1 - p) \cdot (-0.25 \cdot \text{amount} - 100)$$
  **Optimal Rational Choice:**
  $$a^* = \arg\max_{a \in \mathcal{A}} EU(a)$$

### 2.4 ADSA Unit 2: Transaction Network Directed Graph
Transactions form a directed weighted graph $G = (V, E)$:
- $V$: Accounts (nodes)
- $E = (u, v, w, t)$: Directed edges from sender $u$ to receiver $v$ with weight $w$ (amount) and timestamp $t$.
- **Graph Algorithms:**
  1. **Circular Layering (Cycle Detection):** Detects loops ($A \to B \to C \to A$) using 3-color DFS (WHITE, GRAY, BLACK). A back-edge to a GRAY node on the recursion stack identifies circular money laundering.
  2. **Smurfing / Fan-In Anomaly:** Identifies accounts receiving multiple rapid deposits from distinct senders ($d^-(v) \ge \theta$) to evade currency transaction reporting limits.
  3. **BFS Proximity to Blacklist:** Finds shortest path distance $k$ to confirmed fraudulent accounts.

---

## 3. Directory Layout

```
bank_anomaly_flagger/
├── models/                     # OOPJ: Domain classes & Enums
│   ├── __init__.py
│   ├── types.py                # TransactionStatus, ActionType, RiskTier, KYCStatus
│   ├── account.py              # Account class with encapsulation & moving averages
│   └── transaction.py          # Transaction class with lifecycle states
├── dmgt/                       # Discrete Mathematics & Graph Theory
│   ├── __init__.py
│   ├── propositional_engine.py # U1: AST, Connectives, Modus Ponens, Truth Tables
│   └── relations.py            # U2: BinaryRelation, Equivalence Classes, Composition
├── adsa/                       # Advanced Data Structures & Algorithms
│   ├── __init__.py
│   ├── graph.py                # U2: Directed Graph using Adjacency Lists
│   ├── cycle_detector.py       # U2: 3-Color DFS Cycle Detection
│   └── flow_analyzer.py        # U2: Fan-In / Smurfing & BFS Proximity
├── ai/                         # Artificial Intelligence
│   ├── __init__.py
│   └── agent.py                # U1: Rational Agent PEAS & Expected Utility Optimization
├── snowflake_integration/      # Snowflake Framework Integration
│   ├── __init__.py
│   ├── snowflake_id.py         # 64-bit Distributed ID Generator (Twitter Snowflake)
│   └── snowflake_warehouse.py  # Snowflake DDL Schema, Ingestion & Analytics Queries
├── tests/                      # Full Unit Test Suite (25 tests)
│   ├── test_dmgt.py            # Logic, Truth Tables, Equivalence Relations, Closure
│   ├── test_adsa.py            # Directed Graphs, Cycle Detection, Smurfing, BFS
│   ├── test_ai.py              # Expected Utility Payoffs, Rational Decisions
│   ├── test_oopj.py            # Encapsulation, Invariants, State Lifecycle
│   ├── test_snowflake.py       # Snowflake ID Generator & Warehouse Ingestion
│   └── test_bottle_app.py      # Bottle WSGI Routing & REST Endpoints
├── simulator.py                # Benchmark Banking Scenarios & Rule Seeding
├── main.py                     # CLI Demonstrator & Formal Verification Reporter
├── web_app.py                  # Bottle Web Application & Interactive Dashboard
└── README.md                   # Complete Documentation
```

---

## 4. Execution Instructions

### 1. Running the CLI Demonstration
```bash
python main.py
```
This runs the full CLI pipeline:
1. Displays the formal curriculum mapping (DMGT, AI, ADSA, OOPJ, Bottle, Snowflake).
2. Generates and prints the **DMGT U1 Truth Table** for fraud rules.
3. Computes and displays the **DMGT U2 Quotient Set $A / R$** (Equivalence partitions).
4. Generates unique 64-bit **Snowflake IDs** for each transaction.
5. Ingests all screened transactions into the **Snowflake Cloud Data Warehouse** (`FACT_TRANSACTIONS`, `DIM_ANOMALY_AUDIT`).
6. Queries Snowflake analytics and prints a concise batch screening audit summary.

### 2. Launching the Interactive Web Dashboard (Bottle Framework)
```bash
python web_app.py
```
Starts the Bottle micro-web server on `http://localhost:3030/`. Open this URL in any browser to:
- Test custom transactions in real-time.
- View live Snowflake warehouse ledger records.
- Inspect the complete audit trail and Expected Utility payoff matrix.

### 3. Running the Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```
Runs all 33 unit tests across DMGT, ADSA, AI, OOPJ, Snowflake, Bottle, and Security frameworks.

### 4. Deploying to Vercel (1-Click Cloud Deployment)

The repository is configured for serverless deployment on **Vercel** via `vercel.json` and `api/index.py`:

1. Push your repository to GitHub:
   ```bash
   git push -u origin main
   ```
2. Log into [Vercel](https://vercel.com/) and click **"Add New Project"** $\to$ **"Project"**.
3. Import `lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger`.
4. Click **Deploy** *(Vercel will detect `requirements.txt`, install dependencies, and build the serverless functions)*.
5. Your live app will be accessible at:
   `https://bank-transaction-anomaly-flagger.vercel.app` (or your custom Vercel domain).

---

## 5. Summary of Simulation Scenarios

| Scenario | Description | Theoretical Component | Agent Action | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **TXN_001** | Alice transfers $45 for groceries from registered phone | Baseline Benign | `APPROVE` | All logic rules pass, no cycles, $EU(\text{APPROVE}) > 0$. |
| **TXN_002** | Charlie transfers $4,500 (>60x baseline) from unknown device at 3 AM | **DMGT U1** Modus Ponens | `FLAG_MANUAL_REVIEW` | Rule `RULE_ATO_01` fires: $(P_{\text{HIGH}} \land P_{\text{DEV}}) \implies \text{ATO}$. |
| **TXN_003** | Layer C sends $9,300 back to Layer A ($A \to B \to C \to A$) | **ADSA U2** Cycle Detection | `FLAG_MANUAL_REVIEW` | Directed cycle detected in graph recursion stack. |
| **TXN_004** | 3 Mules rapidly deposit $9,200 to Collector X | **ADSA U2** + **DMGT U2** | `FLAG_MANUAL_REVIEW` | Fan-in anomaly detected ($d^- \ge 2$) + Mules in same device equivalence class. |
| **TXN_005** | Confirmed blacklisted fraudster attempts $1,200 transfer | **ADSA U2** + **AI U1** | `FREEZE_ACCOUNT` | 0-hop blacklist match ($P(\text{Fraud}) = 0.950$). $EU(\text{FREEZE}) = \$1,120.00$. |
| **TXN_006** | Seemingly clean account transfers $200 with clean KYC | **DMGT U2** Equivalence Class | `FLAG_MANUAL_REVIEW` | Account device fingerprint matches blacklisted fraudster in $A / R_{\text{device}}$. |
