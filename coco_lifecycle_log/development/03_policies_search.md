# Development 03 — Policy clauses and Cortex Search (CoCo in Snowsight, 2026-10-03)

## Prompt (summary)
Create VIGIL.CORE.POLICY_CLAUSES(DOC_ID, DOC_TITLE, CLAUSE_NO, CLAUSE_TITLE, CLAUSE_TEXT, CITATION) and load the 35 clauses from policies/_clauses.psv verbatim (CITATION = DOC_ID || ' Clause ' || CLAUSE_NO). Create Cortex Search service VIGIL.CORE.POLICY_SEARCH, TARGET_LAG 1 day, COMPUTE_WH. Verify counts and 6 test searches.

## CoCo result
- 35 rows, 6 distinct docs, Rupee sign preserved, service ACTIVE with all 35 rows indexed. CoCo combined CLAUSE_TITLE + CLAUSE_TEXT into one SEARCH_TEXT column so titles contribute to relevance.
- Test searches, expected clause found in top results for all 6:
  - ring of accounts paying same counterparty within 72 hours -> POL-AML-001 Clause 4.5
  - remittance to high risk country EDD threshold -> POL-AML-002 Clause 3
  - LCR below 100 breach escalation -> POL-LIQ-001 Clause 3
  - NPA provisioning percentage substandard -> POL-CR-001 Clause 4
  - deposit then withdrawn within 24 hours -> POL-AML-003 Clause 2
  - repeated cash deposits just under 2 lakh -> POL-AML-001 Clause 3 (ranked 2nd behind Clause 2, the reporting threshold; CoCo noted both are from the same policy and relevant)
