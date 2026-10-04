# Vigil - voiceover script (ElevenLabs)

Paste one scene at a time and generate each as its own clip. Break tags are capped at 3 seconds each, so longer waits chain several. Timings assume the agent takes 30-45 s per answer on screen: cut the wait in the video editor, or let the pause run. Spoken pace is about 150 words per minute. Total: about 4 minutes.

---

## Scene 1 - Setup (about 20 s)

Banks and lenders drown in alerts. Analysts spend their time hunting for evidence and the right policy clause, and only then can they write up the finding. This is Vigil, a risk, fraud and regulatory copilot, built on Snowflake Cortex. Every answer comes with a record I D and a policy clause, or it says it cannot answer. All the data you see is synthetic.

## Scene 2 - Looks clean (about 30 s)

Here are five accounts, A C C zero zero three one to zero zero three five. Each made one small transfer, between eight and fifteen thousand rupees, to the same counterparty, and none of them is flagged. No single transaction rule fires on any of them. <break time="1.5s" /> Let's ask Vigil about one of them.

## Scene 3 - The ring (about 60 s)

I ask: "Is account A C C zero zero three one connected to anything else?" <break time="3s" /> <break time="3s" /> <break time="2s" /> Vigil finds a ring, ring zero zero one, with five member accounts that all paid the same counterparty, Orion Trading Co. The evidence table lists the links, and the transaction I Ds are listed below it. The graph shows the account linked to the other four, a connection no single transaction would reveal. <break time="1s" /> Every source expands to the quoted clause. Here it is policy A M L zero zero one, clause four. And the confidence note says what the data cannot show: whether Orion Trading Co is a legitimate shared merchant, and the account's E D D status, which is unknown. A human has to decide.

## Scene 4 - Noise control (about 30 s)

Now an innocent case. I ask about account A C C zero zero four zero. <break time="3s" /> <break time="3s" /> No ring. This account's counterparties are ordinary merchants and a utility, the State Electricity Board. A hub filter excludes counterparties that many unrelated accounts pay, so a utility like that doesn't create a false ring.

## Scene 5 - Liquidity (about 30 s)

Liquidity next. I ask whether our liquidity coverage ratio is compliant, and when it last breached. <break time="3s" /> <break time="3s" /> Vigil says we are compliant today, and the last breach was on the seventeenth of September, at ninety-four percent. It shows the figures behind the ratio, and cites the Basel Three liquidity policy, clauses two to four.

## Scene 6 - Credit (about 30 s)

Credit. I ask which loans are non-performing, and what provision is required. <break time="3s" /> <break time="3s" /> Loan L N zero zero two five is a hundred and twenty days past due, which makes it Substandard. Fifteen percent of twenty-five lakh rupees is a provision of three lakh seventy-five thousand, citing the credit policy, clauses two to five.

## Scene 7 - Guardrails (about 30 s)

Guardrails matter in compliance. If I ask "Is this account suspicious?" without naming an account, Vigil asks which one, instead of guessing. <break time="2s" /> And if I ask it to post a finding to Slack, it says no external connector is configured, and a human must do it. It never acts on its own.

## Scene 8 - Download (about 10 s)

Every answer comes with a Download finding button, for a draft that is ready for human review.

## Scene 9 - Close (about 25 s)

Under the hood, one Cortex Agent uses three tools: analytics over a semantic view, search across thirty-five policy clauses, and a ring lookup built on Dynamic Tables. We built every part with Cortex Code in Snowsight. The limits are honest: a small synthetic dataset, a hub threshold tuned on one case, and no live regulatory feed. A human signs off on every filing. Vigil takes an analyst from signal, to evidence, to a documented finding.
