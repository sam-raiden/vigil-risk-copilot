# Development 05 — Ring lookup tool and VIGIL_AGENT (CoCo in Snowsight, 2026-10-03)

## Prompt (summary)
Create the ring-lookup custom tool VIGIL.CORE.RING_LOOKUP(ACCOUNT_ID) and ONE Cortex Agent VIGIL.CORE.VIGIL_AGENT with exactly three tools (Cortex Analyst over VIGIL_SV, Cortex Search over POLICY_SEARCH, generic custom tool for RING_LOOKUP). No Slack and no other connector. Natural-language instructions: cite record ID + policy clause for every claim; state uncertainty; ask when transaction/account/loan unspecified; always call ring lookup for fraud/AML; EDD status unknown (no EDD table); never post externally (no external tool exists); human signs off; no accuracy percentages; fixed answer format (Verdict / Evidence / Policy citations / Confidence note). Smoke-test with two questions.

## CoCo result
- RING_LOOKUP first built as a table function and tested (ACC-0031 -> RING-001 with 4 edges; ACC-0007 and ACC-0036 -> NO_RING_FOUND).
- Agent smoke test showed the generic-tool framework calls UDFs as scalar functions, so CoCo replaced RING_LOOKUP with a scalar function returning OBJECT and re-ran. Also had to pass a runtime warehouse for the generic tool.
- Re-test 1 'Is account ACC-0031 connected to anything else?': ring_lookup returned RING-001; policy_search retrieved Clause 4.5 and 5.1; answer cites RING-001, ACC-0031..0035, TXN-000609..000613 and quotes Clause 4.5.1; follows Verdict/Evidence/Policy/Confidence format; includes "human must review and sign off" and "no external connector configured".
- Re-test 2 'Why was ACC-0007 flagged for structuring?': analyst, ring_lookup (NO_RING_FOUND) and policy_search all called; cites TXN-000601..604, ALT-0001..0004, amounts 185000/189000/192000/195000, and quotes Clause 3.1.
