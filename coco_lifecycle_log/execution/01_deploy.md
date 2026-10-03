# Execution 01 — End-to-end run and deployment (2026-10-03)

Pipeline executed through CoCo in Snowsight, in this order: data load (development/01) -> RING_EDGES/RINGS Dynamic Tables with refresh (02) -> POLICY_CLAUSES + POLICY_SEARCH (03) -> VIGIL_SV (04) -> RING_LOOKUP + VIGIL_AGENT (05) -> VIGIL_APP on stage VIGIL.CORE.VIGIL_APP_STAGE (06, 07). Dynamic Tables TARGET_LAG 1 hour; the only refresh is of data, nothing acts on new data.
App location: Snowsight > Projects > Streamlit > VIGIL.CORE.VIGIL_APP (url_id 6moyj5yc76wi4o2oj7ou). It runs inside Snowflake and needs a Snowflake login; it is not publicly reachable.
Account: trial account, ACCOUNTADMIN, credit about 396 of 400 at the start of the run.
Approval note: the user accidentally enabled "Always allow ALTER" in the CoCo chat; CREATE and INSERT were allowed per chat; every other statement/command was approved one by one.
