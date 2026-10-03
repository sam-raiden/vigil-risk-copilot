# Development 09 - UI polish patch

Tool: Cortex Code in Snowsight (the CLI was not used).

## Prompt (abridged)
Small polish patch to streamlit_app.py of VIGIL_APP, only in VIGIL.CORE, change nothing else. Fix (a) cards showing raw markdown, (b) a stray leading fragment in the Evidence card, (c) a doubled dash in policy badges. Add md_to_html (escape, **bold**, bullet lists, line breaks) for card bodies; strip a leading parenthetical fragment in split_sections; make pol_badge never emit a second dash. Test on saved NPA and LCR responses, compile, check no container(height=, :material/ or hide_index, redeploy, read back, print the final file.

## CoCo result
CoCo fetched the deployed source, ran fresh NPA and LCR agent calls, inspected the raw section text, wrote the patched file, tested the three helpers on saved responses plus a synthetic stray-fragment case, then redeployed and printed the final file. (One of its inspection commands errored and it continued; a final six-example agent re-test was still running when I last looked and I did not wait for its output, so no result is claimed for it.)

## What I (Claude Code) checked
- Copied CoCo's printed final file with the code block's copy button (indentation intact) into app/streamlit_app.py: compiles, zero hits for container(height=, :material/, hide_index.
- Opened the deployed app in a fresh tab and clicked the NPA example: Evidence card now renders real bullets and bold, no stray "(record IDs, amounts, dates)" fragment, policy badge shows one dash (POL-CR-001 Clause 2 - "..."), Confidence card reads as clean prose, 23.1 s measured, download button and human-review banner present.
- Remaining flaw: the one-line chat summary truncates mid-bold and can show a raw "**Subs..." (not fixed).
- Not re-checked after the patch: the ring graph, and examples 1-5 individually.
