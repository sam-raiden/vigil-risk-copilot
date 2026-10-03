# Development 07 — App UI fix (CoCo in Snowsight, 2026-10-03)

## Why
Opening the deployed app in Snowsight showed `TypeError: LayoutsMixin.container() got an unexpected keyword argument 'height'`. CoCo's first round only tested the agent backend, not the UI.

## Prompt (summary)
Check the Streamlit runtime version, make streamlit_app.py compatible (remove container height, review chat_input/columns, use_container_width, icons, rerun), pin Streamlit in environment.yml if allowed, re-upload to VIGIL.CORE.VIGIL_APP_STAGE, recreate the app, and say honestly what was verified.

## CoCo result
- Pinned `streamlit=1.35.0` (snowflake channel) + pandas in environment.yml; rewrote streamlit_app.py (no container height, material icons replaced, chat_input placed at page bottom, two-column layout kept); re-uploaded both files; recreated VIGIL_APP; read the staged files back and grepped for the removed constructs.
- CoCo stated plainly that it cannot render the Streamlit UI from its sandbox and that the UI must be opened and clicked manually.
- Verified by the user's agent in Chrome after the fix: the app loads (no TypeError), shows the Vigil header, six example-question buttons, an empty "Audit Panel" placeholder and a chat input at the bottom.
- NOT yet visually confirmed at the time of writing: a full example-question round trip rendered in the audit panel (the browser extension disconnected while the agent call was running).
