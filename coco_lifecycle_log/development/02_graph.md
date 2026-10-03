# Development 02 — Graph layer (CoCo in Snowsight, 2026-10-03)

## Prompt (summary)
Create Dynamic Table RING_EDGES(ACCOUNT_A, ACCOUNT_B, SHARED_ATTRIBUTE, SHARED_VALUE, LINK_STRENGTH): self-join TRANSACTIONS for different accounts paying the same counterparty within 72h; hub filter excludes counterparties paid by more than 8 distinct accounts. Create Dynamic Table RINGS(RING_ID, MEMBER_ACCOUNTS, SHARED_LINK, TRANSACTION_IDS, DETECTED_AT) as connected components with 3+ accounts. TARGET_LAG 1 hour, COMPUTE_WH. Verify the seeded ring is found, the electricity board is excluded, show the no-filter counterfactual and justify the threshold with measured counts.

## CoCo result
- RING_EDGES: 10 edges, all 'Orion Trading Co' (C(5,2) for 5 accounts), LINK_STRENGTH 1 each; zero edges from any other counterparty. Refresh mode FULL (self-join), lag 1 hour.
- RINGS: exactly one ring, RING-001: members ACC-0031..ACC-0035, SHARED_LINK 'Orion Trading Co', TRANSACTION_IDS TXN-000609..TXN-000613. No other rings.
- Connected components: Dynamic Tables do not support WITH RECURSIVE, so CoCo used fixed-iteration (5) min-label propagation in pure SQL. Correct for components with diameter <= 5 (documented limitation).
- Hub filter proof: without the filter the graph has 2,436 edges (State Electricity Board alone yields 300 = C(25,2)); with it, 10 edges. Measured distinct accounts per counterparty: Orion Trading Co 5 (kept), State Electricity Board 25 (excluded), each background counterparty 35 (excluded), single-use counterparties 1. Threshold 8 sits in the 5-to-25 gap; no counterparty has 6-24 accounts. The threshold is tuned on this one synthetic case.

Approvals: ALTER DYNAMIC TABLE ... REFRESH approved by the user's agent per statement.

## Note on approvals
During this step "Always allow ALTER" was enabled in the Snowsight CoCo chat (accidentally, by the user). ALTER statements now run without a prompt in that chat. Mitigation: all prompts are scoped to VIGIL.CORE objects, and executed ALTER statements are reviewed in the chat history after each step.
