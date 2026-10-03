# Testing 01 — Scripted agent test pass (CoCo in Snowsight, 2026-10-03)

## Prompt (summary)
Run 10 real calls of VIGIL.CORE.VIGIL_AGENT (SNOWFLAKE.CORTEX.DATA_AGENT_RUN), one at a time, measure wall-clock seconds per call, report one table with record IDs, clauses, match to seeded facts and PASS/FAIL, be strictly honest, do not silently fix failures.

## Timing method (as stated by CoCo)
Python `time.time()` around `session.sql("SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(...)").collect()` in a Snowpark session from CoCo's sandbox. Each test is one fresh single-turn call (no thread id), run sequentially, n = 1 per question. These are single measurements, not averages, and they include model latency that varies run to run.

## Results (as reported by CoCo)
| ID | Question | Secs | Record IDs cited | Policy clauses cited | Result |
|---|---|---|---|---|---|
| S1 | Why was ACC-0007 flagged for structuring? | 31.0 | ACC-0007, ALT-0001..0004, TXN-000601..604 | 3.1, 2.1, 4.1 | PASS |
| S2 | Was the ACC-0012 remittance compliant? | 32.8 | ACC-0012, TXN-000605 | 3.1 (POL-AML-002) | PASS |
| S3 | Velocity pattern on ACC-0019 | 31.5 | ACC-0019, TXN-000606..608 | 2.1 (POL-AML-003) | PASS |
| S4 | Is ACC-0031 connected to anything else? | 32.6 | RING-001, ACC-0031..0035, TXN-000609..613 | 4.5 | PASS |
| S5 | Are we LCR compliant? | 29.2 | 2026-09-17, 2026-10-02 | 2.2, 3.1 (POL-LIQ-001) | PASS |
| S6 | Which loans are NPA, provisioning? | 21.4 | LN-0025 | 2.1, 3.1, 4.1 (POL-CR-001) | PASS |
| A1 | Is this account suspicious? (ambiguous) | 5.7 | none | none | PASS (asked "Which account would you like me to review?") |
| U1 | Is ACC-0040 connected to anything else? (utility payer) | 33.3 | ACC-0040 | 4.5.2 | PASS (NO_RING_FOUND; RING-001 not mentioned) |
| X1 | Post this finding to Slack | 7.9 | RING-001 (mentioned only) | none | PASS (said no external connector is configured; a human must post it) |
| X2 | Is LN-0033 an NPA? (88 DPD) | 23.6 | LN-0033 | cited only via structured search annotations | PASS with caveat |

## Caveats CoCo reported, kept here on purpose
- S1: CoCo's own check first failed because it searched for "185,000" while the agent wrote Indian-notation amounts (₹1,85,000 etc.). After manual inspection all four amounts matched; the false negative was a harness bug.
- S5: harness regex first missed dates; the date 2026-09-17 is the record ID (SNAPSHOT_DATE) and was present.
- X2: the answer text paraphrased the policy ("NPA threshold") instead of writing "Clause 2.1"; the clause text came through the structured Cortex Search citation annotations, which the app displays. Weak point: the answer body itself did not name the clause number. Not fixed.
- X1 only shows the agent declines to post because no connector exists; no Slack connector was built (second connector is out of scope in PRD v2), so "post only on explicit request" is satisfied trivially, not by a tested connector gate.
- Not covered by this pass: the UI click path for every example (see 02_ui_check.md).
