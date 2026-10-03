# Planning 01 — Ontology & canonical metrics (CoCo in Snowsight, 2026-10-03)

## Prompt
I'm building a Risk, Fraud & Regulatory Intelligence Copilot for banking/NBFC compliance. Target data model: CUSTOMERS, ACCOUNTS, TRANSACTIONS, ALERTS, LIQUIDITY_SNAPSHOTS, CREDIT_PROFILES, RING_EDGES (Dynamic Table), RINGS (full column lists as in PRD Section 3). Draft a semantic ontology and describe the relationships and canonical risk metrics I should define. Planning only: do not create any objects yet.

## CoCo response (captured from page text; truncated at the point the page rendered)
Entity relationships: CUSTOMERS 1-N ACCOUNTS 1-N TRANSACTIONS 1-N ALERTS; CUSTOMERS 1-N CREDIT_PROFILES; RING_EDGES links ACCOUNTS pairwise (N:N via ACCOUNT_A/ACCOUNT_B); RINGS aggregates ACCOUNT_IDs + TRANSACTION_IDs (array); LIQUIDITY_SNAPSHOTS standalone institution-level time series.

Dimension groups proposed: Customer (risk_segment, kyc_status, country, customer_tenure), Account (account_type, account_status, account_age_days), Transaction (transaction_type, channel, counterparty_country, currency, is_flagged/flag_reason), Alert (alert_type, severity, alert_status), Credit (npa_flag, dpd_bucket, credit_score_band).

Canonical AML/fraud metrics proposed: flagged_transaction_count, flagged_transaction_amount, flag_rate, high_risk_jurisdiction_txn_pct, (list continues in CoCo chat "Building Risk and Fraud Intelligence Copilot for Banking").
