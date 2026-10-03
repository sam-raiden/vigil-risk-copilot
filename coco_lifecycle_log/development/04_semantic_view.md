# Development 04 — Semantic view VIGIL.CORE.VIGIL_SV (CoCo in Snowsight, 2026-10-03)

## Prompt (summary)
Build semantic view VIGIL.CORE.VIGIL_SV over all 8 tables with PKs, relationships, comments/synonyms, canonical metrics (flagged count/amount, deposit total, distinct accounts per counterparty, latest LCR, breach days, NPA count/amount, NPA provision per POL-CR-001), and six verified queries for the PRD questions. Validate each through Cortex Analyst against the seeded facts.

## CoCo result
Workflow CoCo followed: agent-studio skill -> JSON proto (8 tables + 6 VQRs) -> `cortex agent-studio sv-generate` (base YAML: PKs, dimensions, 6 VQRs, 1 relationship) -> Python enrichment (6 relationships, 8 canonical metrics, synonyms, descriptions) -> `sv-write` -> `sv-deploy` to VIGIL.CORE.VIGIL_SV.
Validation of the 6 verified questions via Cortex Analyst: zero mismatches against seeded facts (ACC-0007 4 deposits; ACC-0012 650000 Myanmar; ACC-0019 750000 in / 650000 out; RING-001 members ACC-0031..0035, 5 members, Orion Trading Co, TXN-000609..613; LCR breach 2026-09-17 at 94.00; LN-0025 120 DPD, 2,500,000, Substandard, provision 375,000, LN-0033 not returned).
Approvals: the user's agent approved each sandbox command (python/cortex agent-studio) individually in the chat.
