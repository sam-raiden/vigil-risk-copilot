# Development 13 - Professional, Snowflake-native look

Tool: Cortex Code in the Snowsight panel (no CLI).

## Why
After the Snowflake-colour pass (development/12) the user said the UI still looked like a colourful AI-generated template and asked for a professional look, as if it were another feature of the Snowflake site.

## Prompt (abridged; full text is in the Snowsight chat history)
UI/CSS only. Back up the stage file as `streamlit_app_v5_backup.py`. Flat and restrained: white page, #F5F7FA surfaces, 1px #DDE3EA borders, 8px radius, no gradients, no tinted card backgrounds. One accent, Snowflake Blue #29B5E8 (Medium Blue #11567F for key text and the graph hub), used sparingly. Slim top bar instead of a hero banner, neutral grey chips, plain white bordered example cards with a text-link Ask, light grey user bubble, uppercase grey section labels, verdict with a 3px blue left border, white source chips with blue outline, solid blue Download button, white graph panel with a grey-edged graph, light/dark safe, Streamlit 1.35.0 limits kept. Redeploy, read back, confirm no linear-gradient( and none of the old purple/orange/pink/teal colours.

## CoCo result
- The first attempt of this prompt hit "Internal server error: You may need to start a new chat"; I started a new chat and re-sent the same self-contained prompt, which worked. The user clicked Allow on the stage download, the backup and the upload.
- CoCo reported linear-gradient( count 0 and none of the banned colours in the staged file.
- CoCo noted the app was recreated with warehouse COMPUTE_WH instead of the original VIGIL_WH (which no longer exists or is inaccessible). It could not render the app or test dark mode.

## What I (Claude Code) checked
- Fresh tab: slim header, flat example cards, blue Ask links (they look grey while the app is still starting), ring question answered: user bubble in light grey, verdict with blue left border and Cited pill, evidence, graph with a Medium Blue hub and grey edges, confidence note, solid blue Download finding, 43.3 s measured.
- app/streamlit_app.py in the repo is the staged file read back (24,219 chars; compiles; 0 gradients; no forbidden patterns; no old colours). tests/test_local.py passes.
- Rollback: copy `streamlit_app_v5_backup.py` over `streamlit_app.py` on VIGIL.CORE.VIGIL_APP_STAGE and recreate the app.
- Not verified: dark mode, the other five examples after this restyle, the downloaded file, source expanders.
