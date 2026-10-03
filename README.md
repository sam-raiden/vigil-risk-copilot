# Vigil — cited risk, fraud and regulatory copilot

Vigil answers a compliance analyst's plain-English question with an audit-ready finding: a verdict, the evidence records, and the exact policy clause behind it. It covers three risk pillars on **synthetic data** in Snowflake:

- **Fraud / AML** — structuring, high-risk-jurisdiction remittances, velocity, and **fraud-ring detection** over a relationship graph (the novel piece).
- **Liquidity** — LCR calculation and breach history with the Basel III clause (calculation + citation only).
- **Credit** — NPA classification and provisioning with the RBI IRAC clause (calculation + citation only).

Signal → Evidence → Documented finding. A human signs off on every filing; nothing acts unasked.

## What is in Snowflake (database `VIGIL`, schema `CORE`)

| Object | Kind | Notes |
|---|---|---|
| CUSTOMERS, ACCOUNTS, TRANSACTIONS, ALERTS, LIQUIDITY_SNAPSHOTS, CREDIT_PROFILES | tables | 60 / 70 / 638 / 6 / 30 / 40 rows, deterministic synthetic data |
| RING_EDGES, RINGS | Dynamic Tables | same-counterparty-within-72h pairs; hub filter drops counterparties paid by more than 8 distinct accounts; connected components of 3+ accounts |
| POLICY_CLAUSES, POLICY_SEARCH | table, Cortex Search service | 35 numbered clauses from `policies/` |
| VIGIL_SV | semantic view | 8 tables, 6 relationships, 8 canonical metrics, 6 verified queries |
| RING_LOOKUP | scalar function | custom agent tool: ring neighbours and ring row for an account |
| VIGIL_AGENT | Cortex Agent | one agent, three tools (Analyst, Search, ring lookup) |
| VIGIL_APP | Streamlit in Snowflake | AI-assistant-style chat with inline cited answers (verdict + Cited pill, evidence, numbered source chips with clause text, confidence) + six example questions + ring graph + download |

## Seeded synthetic patterns

| Pattern | Seed |
|---|---|
| Structuring | ACC-0007: 4 branch cash deposits INR 185000–195000 within 10 days |
| High-risk country | ACC-0012: INR 650000 remittance to Myanmar |
| Velocity | ACC-0019: INR 750000 deposit, 86.7% out within 24 hours |
| Ring | ACC-0031..ACC-0035 each pay "Orion Trading Co" within 72 hours; none individually flagged |
| Noise control | 25 other accounts pay "State Electricity Board" in the same window; must not form a ring |
| Liquidity | 30 daily snapshots; 2026-09-17 breaches at LCR 94 |
| Credit | 40 loans; LN-0025 at 120 days past due (NPA); LN-0033 at 88 days (near miss) |

## Ring detection

`RING_EDGES` self-joins transactions for pairs of different accounts that paid the same counterparty within 72 hours. A hub filter removes counterparties paid by more than 8 distinct accounts (legitimate shared relationships such as utilities). `RINGS` groups the remaining edges into connected components and keeps groups of 3 or more accounts. Dynamic Tables do not support recursive CTEs, so connected components use five unrolled min-label-propagation iterations (correct for components of diameter ≤ 5).

Measured on the seeded data (from the CoCo run in `coco_lifecycle_log/development/02_graph.md`): without the hub filter the graph has 2,436 edges (the electricity board alone gives 300); with it, 10 edges and exactly one ring, RING-001 (ACC-0031..0035). The threshold of 8 sits in the gap between 5 (ring counterparty) and 25 (utility); it is tuned on this one synthetic case.

## Built through CoCo

Every artifact was generated and executed by Snowflake's CoCo (Cortex Code) in the Snowsight panel. The Cortex Code CLI was installed locally but could not be connected, so it was not used. Prompts and result summaries per phase are in [`coco_lifecycle_log/`](coco_lifecycle_log/) (planning, development, execution, testing). Full transcripts live in the Snowsight CoCo chat history; the logs here are the exact prompts plus summarized results, not complete transcripts. `policies/` holds the six policy documents and `policies/_clauses.psv` the flattened clause rows loaded into `POLICY_CLAUSES`.

## Test results (CoCo scripted pass, 2026-10-03)

10 single-turn agent calls, wall-clock seconds measured with Python `time.time()` around the agent call (n = 1 each, not averages): S1 structuring 31.0, S2 high-risk remittance 32.8, S3 velocity 31.5, S4 ring 32.6, S5 LCR 29.2, S6 NPA 21.4, A1 ambiguous 5.7 (asked which account), U1 utility payer 33.3 (no ring), X1 Slack-post request 7.9 (declined: no external connector), X2 near-miss loan LN-0033 23.6 (not an NPA). 9 clean passes, 1 with a caveat: the X2 answer cited its clause only through search annotations, not by number in the text. Details and caveats: [`coco_lifecycle_log/testing/`](coco_lifecycle_log/testing/). Later fixes: the agent now cites policy document ID plus clause (e.g. POL-AML-003 Clause 2), and the app was redesigned (cards, Cited / Not citable chip, document-ID badges). In the app, examples 1, 2, 3, 5 and 6 and the typed ring question were confirmed by clicking; the ring graph renders in the redesigned layout (edge labels overlap, cosmetic).

## Honest limits

- Tested on a small synthetic dataset (hundreds of transactions); the hub threshold is tuned on one seeded case.
- Entities are matched by exact name only; no fuzzy matching.
- No device attribute: counterparty and a 72-hour window only.
- No EDD record table, so EDD status is reported as unknown.
- No live regulatory feed, no second agent, no external connector (no Slack/Jira); nothing posts externally.
- The app runs inside Snowflake and needs a Snowflake login.
- A human signs off on every filing.

## Repository layout

```
policies/                 six policy documents (35 numbered clauses) + _clauses.psv
app/streamlit_app.py      the deployed Streamlit in Snowflake app
coco_lifecycle_log/       CoCo prompts and results by phase
docs/                     MVP brief, demo script, deck (Vigil_deck.pptx + build_deck.py), PRD v1
```
