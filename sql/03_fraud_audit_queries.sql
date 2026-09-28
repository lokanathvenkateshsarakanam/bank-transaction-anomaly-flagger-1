-- ============================================================================
-- 03_FRAUD_AUDIT_QUERIES.SQL
-- Advanced Analytical SQL Queries for Forensic Fraud Investigation
-- Demonstrates ADSA Graph Queries (Recursive CTE) and Smurfing Window Functions
-- ============================================================================

-- 1. ADSA U2 Cycle Detection via Recursive Common Table Expression (CTE)
-- Detects directed circular money-laundering paths up to 4 hops (A -> B -> C -> A)
WITH RECURSIVE TransactionPath AS (
    -- Anchor member: Initial transaction hop
    SELECT 
        sender_id AS original_sender,
        receiver_id AS current_node,
        1 AS hop_count,
        ARRAY[sender_id, receiver_id] AS path_history,
        amount
    FROM core_transactions
    WHERE created_at >= NOW() - INTERVAL '24 HOURS'
    
    UNION ALL
    
    -- Recursive member: Traverse outgoing transaction hops
    SELECT 
        tp.original_sender,
        t.receiver_id AS current_node,
        tp.hop_count + 1,
        tp.path_history || t.receiver_id,
        t.amount
    FROM TransactionPath tp
    JOIN core_transactions t ON tp.current_node = t.sender_id
    WHERE tp.hop_count < 4
      -- Stop recursion if we hit a node already in the path other than original sender
      AND (t.receiver_id = tp.original_sender OR NOT (t.receiver_id = ANY(tp.path_history)))
      AND t.created_at >= NOW() - INTERVAL '24 HOURS'
)
SELECT 
    original_sender,
    current_node,
    hop_count,
    path_history AS circular_laundering_loop
FROM TransactionPath
WHERE original_sender = current_node AND hop_count >= 2;


-- 2. ADSA U2 Smurfing / Structuring Detection via Window Aggregations
-- Finds collector accounts receiving multiple deposits just below regulatory thresholds ($9,000 - $9,999)
SELECT 
    receiver_id AS collector_account,
    COUNT(DISTINCT sender_id) AS distinct_mule_senders,
    SUM(amount) AS total_structured_volume,
    MIN(created_at) AS first_deposit,
    MAX(created_at) AS last_deposit,
    MAX(created_at) - MIN(created_at) AS time_span
FROM core_transactions
WHERE amount BETWEEN 9000.00 AND 9999.99
  AND created_at >= NOW() - INTERVAL '2 HOURS'
GROUP BY receiver_id
HAVING COUNT(DISTINCT sender_id) >= 3;


-- 3. DMGT U2 Equivalence Class Cluster Query
-- Partitions accounts sharing identical device fingerprints or IP addresses
SELECT 
    device_fingerprint,
    COUNT(account_id) AS cluster_size,
    STRING_AGG(account_id, ', ') AS linked_accounts_in_equivalence_class,
    BOOL_OR(is_blacklisted) AS contains_blacklisted_member
FROM core_accounts
WHERE device_fingerprint IS NOT NULL AND device_fingerprint != ''
GROUP BY device_fingerprint
HAVING COUNT(account_id) > 1;
