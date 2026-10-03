# Development 10 — Second UI redesign (AI-assistant style)

Tool: Cortex Code in the Snowsight panel (no CLI).

## Prompt (abridged; full text is in the Snowsight chat history)
Redesign VIGIL_APP's UI only, in the style of top AI assistants (Claude / ChatGPT / Perplexity). First back up the stage file to `streamlit_app_v2_backup.py`. Keep behaviour, agent call, parsing helpers, PRD features and the Streamlit 1.35.0 limits (no container(height=), no :material/, no hide_index, no external fonts or CDN). Centered ~820px column; slim header; empty state with greeting and a 2x3 grid of example cards; inline assistant answer: Verdict + Cited / Not citable pill, Evidence (bullets + compact table), numbered Sources chips with expanders showing clause text, ring graph only for ring questions, muted Confidence note; footer with measured seconds, Download finding and the human-review line; pill chat input; neutral palette, one accent, light/dark safe CSS. Ring graph: no edge labels, counterparty in the title, hub node in the accent colour. Test helpers on saved NPA and LCR responses, compile, redeploy, read back, report honestly.

## CoCo result
- Backed up the previous stage file, wrote the new UI, tested the helpers against saved responses, redeployed and read the file back.
- CoCo caught two of its own bugs during testing: the first copy of the helpers omitted `call_agent` and the regexes (the app would have crashed), and the helpers used a different name for the `html` import. Both were fixed before deploy.
- New behaviour to know: the app now runs a read-only query on VIGIL.CORE.POLICY_CLAUSES to show quoted clause text in the source expanders (citation IDs are pattern-checked first). Dark mode follows the OS setting.
- Rollback: copy `streamlit_app_v2_backup.py` over `streamlit_app.py` on VIGIL.CORE.VIGIL_APP_STAGE and recreate the app.

## What I (Claude Code) checked
- Fresh tab, full reload: greeting, 2x3 example cards with hint text, pill input render. Hint text sits just below each card rather than inside it (minor).
- Clicked "Ring connections": inline answer with Verdict + CITED pill, Evidence bullets, ring-edge table titled with Orion Trading Co, record-ID chips, SOURCES chips (POL-AML-001 Clause 4, 5; POL-AML-004 Clause 2) with expanders, ring graph with highlighted hub ACC-0031 and NO overlapping edge labels, Confidence note, 34.3 s measured, Download finding button, human-review line.
- Not checked: expanding a source card, dark mode, the other five examples after this redesign, the downloaded file contents.
- Visible flaw: the verdict line ended in an ellipsis ("...detected coordinated-activity fraud ring...").
- app/streamlit_app.py in the repo is now the stage file read back through CoCo (21,067 bytes; compiles; no forbidden patterns).
