# Development 11 — Branding and colour pass

Tool: Cortex Code in the Snowsight panel (no CLI).

## Why
After the AI-assistant-style redesign (development/10) the user said the app had no colour, no branding and a small, plain app name.

## Prompt (abridged; full text is in the Snowsight chat history)
Branding and colour pass on VIGIL_APP, UI only. Back up the stage file first (`streamlit_app_v3_backup.py`). Add an indigo-to-violet palette with a teal accent for the verdict, a hero with an inline SVG logo and a large gradient "Vigil" wordmark plus tagline, tinted example cards with the hint inside the card, gradient user bubbles and send button, indigo source chips, a tinted graph panel, a branded footer, and fix the verdict line ellipsis. Keep behaviour, helpers, the Streamlit 1.35.0 limits (no container(height=), no :material/, no hide_index, no external fonts or CDN), and light/dark safe CSS.

## CoCo result
- Backed up the previous stage file, rewrote the UI layer, kept the parsing helpers byte-identical to the previous version, redeployed and read the file back.
- CoCo said it did not verify graphviz rendering, dark mode, or whether the hero and cards fit a laptop screen.
- Rollback: copy `streamlit_app_v3_backup.py` over `streamlit_app.py` on VIGIL.CORE.VIGIL_APP_STAGE and recreate the app.

## What I (Claude Code) checked
- Fresh tab, full reload: hero with logo and large gradient wordmark, tinted example cards, gradient bubbles and send button, indigo chips, teal verdict card, lavender graph panel, branded footer.
- Ring example: answer rendered, the source expander opened and showed the clause text, the verdict now reads as a full sentence (no ellipsis).
- app/streamlit_app.py in the repo is the stage file read back through CoCo's clipboard copy (26,681 bytes; compiles; no forbidden patterns).

## Not verified / remaining flaws
- Dark mode, the other five examples after this pass, the downloaded file contents.
- Each example card has a separate "Ask" button below it (the click target), and the hero plus cards need scrolling to see all six cards on a laptop.
- Graph colours are fixed for light mode.
