# Development 06 — Streamlit app VIGIL_APP (CoCo in Snowsight, 2026-10-03)

## Prompt (summary)
Build and deploy Streamlit in Snowflake app VIGIL.CORE.VIGIL_APP: two columns (chat + six example buttons | audit panel with verdict, evidence table, record IDs, policy citations with clause text, confidence note, measured seconds, markdown download, ring graph for ring questions); call VIGIL_AGENT; show a "Not citable" warning when an answer has no record ID or no policy clause. Test six examples plus an ambiguous question and print the source.

## CoCo result (first attempt)
- Wrote /tmp/streamlit_app.py, created stage VIGIL.CORE.VIGIL_APP_STAGE and a deployment helper procedure VIGIL.CORE._STAGE_FILE, uploaded streamlit_app.py + environment.yml, created VIGIL.CORE.VIGIL_APP (COMPUTE_WH).
- CoCo could not render the page, so it validated through backend agent calls only. Its backend results: Q1 structuring (TXN-000601..604, ALT-0001..0004, Clause 3.1), Q2 high-risk (TXN-000605, Clause 3.1, EDD required, 650K Myanmar), Q3 velocity (TXN-000606/607/608, Clause 2.1, 750K in / 650K out = 86.7%), Q4 ring (RING-001, Clause 4.5), Q5 LCR (2026-09-17 breach, Clauses 3.1/2.2), Q6 NPA (LN-0025, 120 DPD, 2.5M, 375K provision, Clauses 2.1/3.1/4.1), Q7 ambiguous 'Is this account suspicious?' -> agent asked "Which account would you like me to review?".
- Defect found when the user's agent opened the app: `TypeError: LayoutsMixin.container() got an unexpected keyword argument 'height'` (the Streamlit runtime is older than the code assumed). CoCo's backend tests had not exercised the UI. A follow-up CoCo prompt asked it to check the runtime version, make the code compatible, redeploy and report honestly what it could and could not verify. See 07_app_fix.md.
