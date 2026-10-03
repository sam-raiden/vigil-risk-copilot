# Planning 02 — End-to-end workflow (CoCo in Snowsight, 2026-10-03)

## Prompt (verbatim)
Outline the end-to-end workflow: signal detection -> evidence gathering -> documented finding, for three pillars: (1) fraud/AML with graph-based ring detection (RING_EDGES dynamic table self-join on shared counterparty/device/time window, connected-components clustering into RINGS, hub-node noise filter), (2) liquidity (Basel III LCR compliance, calculation + policy citation only), (3) credit (NPA classification and provisioning, calculation + policy citation only). Include the agent/tool design (Cortex Analyst, Cortex Search, a ring-lookup tool, Slack only on explicit user request) and the rule that every answer must cite a record ID and a policy clause. Planning only: do not create any objects yet.

## CoCo response — key excerpts (full ~7k-char response is in the Snowsight CoCo chat "Building Risk and Fraud Intelligence Copilot for Banking")
- Architecture: Cortex Agent orchestrator with tools: Cortex Analyst (semantic views), Cortex Search (policy docs), Ring Lookup (Python UDTF), Slack Notify ("ONLY on explicit ask").
- Mandatory output contract: every answer includes >=1 record ID (ALERT_ID, TRANSACTION_ID, LOAN_ACCOUNT_ID, SNAPSHOT_DATE, RING_ID) and >=1 policy clause; if either missing the agent must self-correct before returning.
- Pillar 1 signal detection: RING_EDGES dynamic table as self-join of TRANSACTIONS on shared counterparty or channel + tight time window, different accounts.
- Agent system-prompt key rules (citation mandate, uncertainty statement, clarify-if-ambiguous, Slack only on request).

## Adaptation decision
The PRD data model has no device column, so "shared device" is approximated by shared counterparty within a time window (consistent with POL-AML-001 clause 4.5).
