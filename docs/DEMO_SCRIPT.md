# Vigil — demo script (about 4 minutes)

Record in Snowsight with VIGIL_APP open. The agent takes 20–35 s per answer in my measured runs, so talk over the wait or cut it.

1. **Setup (20 s).** Open on the branded landing view (logo, gradient "Vigil" wordmark, tinted example cards). "All data is synthetic. Vigil answers compliance questions with a record ID and a policy clause, or says it cannot."
2. **Look clean (30 s).** In a SQL tab show ACC-0031..0035: five small transfers (INR 8–15k), none flagged. "No per-transaction rule fires on any of these."
3. **The ring (60 s).** Click "Is account ACC-0031 connected to anything else?" → wait → the answer shows RING-001, five members, Orion Trading Co, TXN-000609..613, POL-AML-001 Clause 4, the ring graph; open a Sources expander to show the quoted clause. Say: "The graph found what no single transaction shows. The confidence note says what the data cannot establish."
4. **Noise control (30 s).** Type "Is account ACC-0040 connected to anything else?" → no ring. "ACC-0040 paid the electricity board, which 25 accounts paid; the hub filter excludes it."
5. **Liquidity (30 s).** Click the LCR example → breach on 2026-09-17 at 94, POL-LIQ-001 Clauses 3, 4, 5.
6. **Credit (30 s).** Click the NPA example → LN-0025, 120 days past due, INR 25 lakh, Substandard, 15% = INR 3.75 lakh, POL-CR-001 Clauses 2-5.
7. **Guardrails (30 s).** Type "Is this account suspicious?" → it asks which account. Then "Post this finding to Slack" → it says no external connector is configured and a human must do it.
8. **Download (10 s).** Click "Download finding" under the answer.
9. **Close (20 s).** Honest limits: small synthetic data, threshold tuned on one case, exact-name matching, no EDD table, no live regulatory feed, a human signs off on every filing. Do not quote any percentage improvement; the only numbers are the measured seconds above.

Not in scope and not shown: a Slack or Jira connector, scheduled jobs, real data.
