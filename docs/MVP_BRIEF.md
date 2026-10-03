# Vigil — MVP brief (draft for the Hack2Skill template)

Problem statement: Risk, Fraud and Regulatory Intelligence Copilot (Snowflake CoCo CLI Hackathon, GCC Edition).

## MVP brief
Vigil is a cited risk, fraud and regulatory copilot for banking and NBFC compliance teams. An analyst asks a plain-English question and gets an audit-ready finding: a verdict, the evidence records, and the exact policy clause behind it. It covers all three pillars named in the problem statement, on synthetic data inside Snowflake:

- **Fraud / AML** — structuring, high-risk-jurisdiction remittances, velocity, and ring detection. Rings are the novel piece: a Dynamic Table links accounts that paid the same counterparty within 72 hours, a hub filter drops counterparties paid by more than 8 accounts (utilities), and a second Dynamic Table groups the rest into connected components of 3+ accounts. The seeded ring (ACC-0031..0035) is found even though no single account is flagged, and the seeded utility (25 payers) is not reported as a ring.
- **Liquidity** — LCR calculation and breach history with the Basel III clause (calculation + citation only).
- **Credit** — NPA classification and provisioning with the RBI IRAC clause (calculation + citation only).

One Cortex Agent has three tools (analytics over a semantic view with six verified queries, policy search over 35 numbered clauses, and a ring lookup). A Streamlit-in-Snowflake app shows a branded (indigo-violet palette, logo and hero) AI-assistant-style chat whose answers are inline (verdict with a Cited pill, evidence, numbered source chips that expand to the clause text, ring graph, confidence note, measured seconds, finding download). It never presents an uncited answer as a finding and asks which account/loan when the question does not say.

Signal → Evidence → Documented finding. A human signs off on every filing; nothing acts unasked.

## How CoCo was used (all four phases)
Every Snowflake object was generated and executed through CoCo in the Snowsight panel (the CLI was installed but could not be connected, so it was not used), and prompts plus result summaries are logged in `coco_lifecycle_log/`: planning (ontology, metrics, workflow), development (synthetic data, Dynamic Tables, policy table and Cortex Search, semantic view with verified queries, ring-lookup tool, agent, Streamlit app, its fix, a citation fix so every policy citation names its document, two UI redesigns and a branding pass), execution (end-to-end deployment) and testing (ten scripted agent calls with measured timings). Honest note: the logs are exact prompts plus summarized results, not full transcripts.

## Measured results
- Ring detection on the seeded data: 2,436 candidate edges without the hub filter, 10 with it, exactly one ring (RING-001, ACC-0031..0035). Threshold 8 sits in the gap between 5 (ring counterparty) and 25 (utility); tuned on this one synthetic case.
- Semantic view: all six verified questions matched the seeded facts (0 mismatches in CoCo's check).
- Agent test pass: 10 scripted single-turn calls, 9 clean passes and 1 pass with a caveat (the LN-0033 answer cited its clause only via search annotations, not by number in the text). Method: Python wall-clock around the agent call, n = 1 per question.
- Time from question to answer, measured per call: 5.7 s (ambiguous question, clarifying reply) to 33.3 s (utility check); structuring 31.0 s, high-risk remittance 32.8 s, velocity 31.5 s, ring 32.6 s, LCR 29.2 s, NPA 21.4 s. The app itself measured 28.4 s for the ring question from the UI. These are single runs, not averages, and say nothing about a manual process because no manual baseline was measured.

## Challenges faced
- **Agent tool types:** the first RING_LOOKUP was a table function; Cortex Agents call generic tools as scalar functions, so it was rebuilt as a scalar function returning an OBJECT.
- **Dynamic Tables cannot recurse:** connected components use five unrolled min-label-propagation steps (correct for components of diameter ≤ 5).
- **App crashed on first open:** the first Streamlit build used a call the Snowflake runtime did not support (`container(height=...)`). CoCo had only tested the agent backend, not the UI; this was caught by opening the app, fixed through CoCo, and the fix pins Streamlit 1.35.0.
- **Browser automation was unstable** with Snowsight's heavy pages, so UI checks took several attempts; examples 1, 2, 3, 5, 6 were finally confirmed by clicking (see `coco_lifecycle_log/testing/02_ui_check.md`).
- **Accidental setting:** "Always allow ALTER" was enabled in the CoCo chat by mistake; all later prompts were scoped to VIGIL objects.

## Honest limits
Small synthetic dataset (hundreds of transactions); hub threshold tuned on one seeded case; exact-name entity matching only; no device attribute (counterparty and a 72-hour window only); no EDD record table so EDD status is "unknown"; no live regulatory feed; no second agent or external connector (so no Slack/Jira; nothing posts externally); the app runs inside Snowflake and needs a login; a human signs off on every filing.

## Links (to fill after publishing)
- Public GitHub repository: https://github.com/sam-raiden/vigil-risk-copilot
- Deployed prototype: Snowsight > Projects > Streamlit > VIGIL.CORE.VIGIL_APP (requires Snowflake login; not publicly reachable)
- Public demo view link: TBD (needs a screen recording or a public viewer; not produced yet)
- Presentation: `docs/Vigil_deck.pptx`
