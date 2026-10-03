# Development 01 — Synthetic data (CoCo in Snowsight, 2026-10-03)

## Prompt (verbatim summary of PRD v2 seeds; sent after the v2 PRD superseded the first attempt, which was stopped and discarded)
Rebuild VIGIL.CORE: CUSTOMERS, ACCOUNTS, TRANSACTIONS, ALERTS, LIQUIDITY_SNAPSHOTS, CREDIT_PROFILES. Deterministic SQL only. ~60 customers, ~70 accounts, ~600 small background transactions over 45 days. Seeds: ACC-0007 structuring (4 branch cash deposits 185k/189k/192k/195k within 10 days); ACC-0012 INR 650000 remittance to Myanmar; ACC-0019 INR 750000 deposit with INR 650000 (86.7%) out within 24h; ACC-0031..0035 each pay 'Orion Trading Co' within 72h, unflagged; ACC-0036..0060 pay 'State Electricity Board' in the same window (noise control); 30 LCR snapshots with 2026-09-17 at 94 (BREACH); 40 credit profiles with LN-0025 at 120 DPD (NPA) and LN-0033 at 88 DPD (near miss). Verify counts, FK orphans, and each pattern.

## CoCo result (statements run in Snowflake via CoCo; approvals granted per chat for CREATE and INSERT only)
| Table | Rows |
|---|---|
| CUSTOMERS | 60 |
| ACCOUNTS | 70 |
| TRANSACTIONS | 638 (600 background + 38 seeded) |
| ALERTS | 6 |
| LIQUIDITY_SNAPSHOTS | 30 |
| CREDIT_PROFILES | 40 |

FK orphan checks: 0 for ACCOUNTS->CUSTOMERS, TRANSACTIONS->ACCOUNTS, ALERTS->TRANSACTIONS, CREDIT_PROFILES->CUSTOMERS.
Pattern checks (8 verification queries, all passed per CoCo): ACC-0007 structuring (4 deposits, Sep 13-22, 4 alerts); ACC-0012 Myanmar remittance; ACC-0019 velocity; Orion Trading Co 5 distinct accounts; State Electricity Board 25 distinct accounts (ACC-0036..0060, 25 txns, 48-hour window); 2026-09-17 LCR 94.00 BREACH (HQLA 47B / outflows 50B), other 29 days COMPLIANT (105-131); LN-0025 120 DPD NPA INR 2.5M; LN-0033 88 DPD NPA_FLAG FALSE.

Full chat transcript: Snowsight CoCo chat "Building Risk and Fraud Intelligence Copilot for Banking".
