import streamlit as st
import json
import time
import re
import pandas as pd
from datetime import datetime, timezone
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Vigil", page_icon=":shield:", layout="wide")

session = get_active_session()

EXAMPLES = [
    "Why was account ACC-0007 flagged for structuring?",
    "Was the remittance on account ACC-0012 to the high risk country compliant?",
    "Show me the velocity pattern on account ACC-0019.",
    "Is account ACC-0031 connected to anything else?",
    "Are we compliant with our liquidity coverage ratio?",
    "Which loan accounts are NPA and what provisioning is required?",
]

for key, default in [("messages", []), ("latest", None), ("q", None), ("secs", None)]:
    if key not in st.session_state:
        st.session_state[key] = default


def call_agent(question: str):
    payload = json.dumps(
        {"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}]}
    )
    escaped = payload.replace("\\", "\\\\").replace("'", "\\'")
    sql = f"SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN('VIGIL.CORE.VIGIL_AGENT', '{escaped}')"
    t0 = time.time()
    rows = session.sql(sql).collect()
    elapsed = round(time.time() - t0, 1)
    raw = rows[0][0]
    return parse_response(raw), elapsed


def parse_response(raw_json: str) -> dict:
    data = json.loads(raw_json)
    if "code" in data and data.get("code") != "200":
        return _empty(error=data.get("message", "Unknown agent error"))

    content = data.get("content", [])
    texts, tables, citations, ring_data = [], [], [], None

    for item in content:
        t = item.get("type")
        if t == "text":
            texts.append(item.get("text", ""))
            for ann in item.get("annotations", []):
                if ann.get("type") == "cortex_search_citation":
                    citations.append(ann.get("text", ""))
        elif t == "table":
            rs = item.get("table", {}).get("result_set", {})
            meta = rs.get("resultSetMetaData", {})
            cols = [c["name"] for c in meta.get("rowType", [])]
            rows = rs.get("data", [])
            title = item.get("table", {}).get("title", "")
            tables.append({"title": title, "columns": cols, "rows": rows})
        elif t == "tool_result":
            tr = item.get("tool_result", {})
            if tr.get("name") == "ring_lookup" and tr.get("status") == "success":
                for c in tr.get("content", []):
                    j = c.get("json", {})
                    r = j.get("result", "")
                    if r and "ring_id" in str(r).lower():
                        try:
                            ring_data = json.loads(r) if isinstance(r, str) else r
                        except Exception:
                            pass

    full_text = "\n".join(texts)
    record_ids = sorted(
        set(
            re.findall(
                r"(?:TXN-\d+|ACC-\d+|ALT-\d+|RING-\d+|LN-\d+|\d{4}-\d{2}-\d{2})",
                full_text,
            )
        )
    )
    has_policy = bool(re.search(r"Clause\s+\d", full_text, re.IGNORECASE))
    verdict = ""
    confidence = ""
    for line in full_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("**Verdict") and not verdict:
            verdict = stripped
        if "confidence" in stripped.lower() and (
            "note" in stripped.lower() or "high" in stripped.lower()
        ):
            if not confidence:
                confidence = stripped

    has_ring = ring_data is not None and "ring_id" in str(ring_data).lower()
    return {
        "full_text": full_text,
        "tables": tables,
        "citations": citations,
        "record_ids": record_ids,
        "has_policy": has_policy or len(citations) > 0,
        "has_ring": has_ring,
        "ring_data": ring_data,
        "verdict": verdict or (full_text[:300] if full_text else "No response"),
        "confidence": confidence,
        "error": None,
    }


def _empty(error=""):
    return {
        "full_text": "",
        "tables": [],
        "citations": [],
        "record_ids": [],
        "has_policy": False,
        "has_ring": False,
        "ring_data": None,
        "verdict": "",
        "confidence": "",
        "error": error,
    }


def build_dot(ring_data):
    if not ring_data:
        return None
    edges = ring_data.get("edges", [])
    ring = ring_data.get("ring", {})
    if ring.get("status") == "NO_RING_FOUND" or not edges:
        return None
    rid = ring.get("ring_id", "")
    sl = ring.get("shared_link", "")
    dot = (
        f'graph {{\n label="{rid}: {sl}"\n labelloc="t"\n fontsize=14\n'
        ' node [shape=box style=filled fillcolor="#E8F0FE" fontsize=10]\n'
        ' edge [fontsize=8 color="#555555"]\n'
    )
    for e in edges:
        a, b = e.get("account_a", ""), e.get("account_b", "")
        sv = e.get("shared_value", "")
        dot += f' "{a}" -- "{b}" [label="{sv}"]\n'
    dot += "}\n"
    return dot


def make_markdown(question, parsed, elapsed):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    md = f"# Vigil Finding\n\n"
    md += f"**Question:** {question}\n\n**Timestamp:** {ts}\n\n"
    md += f"**Measured wall-clock seconds for this call:** {elapsed}\n\n"
    md += f"## Verdict\n\n{parsed.get('verdict', 'N/A')}\n\n"
    md += f"## Evidence\n\n**Record IDs:** {', '.join(parsed.get('record_ids') or ['None'])}\n\n"
    for tbl in parsed.get("tables", []):
        md += f"### {tbl.get('title', 'Data')}\n\n"
        if tbl["columns"]:
            md += "| " + " | ".join(tbl["columns"]) + " |\n"
            md += "| " + " | ".join(["---"] * len(tbl["columns"])) + " |\n"
            for row in tbl["rows"][:20]:
                md += "| " + " | ".join(str(c) for c in row) + " |\n"
        md += "\n"
    md += "## Policy Citations\n\n"
    for cit in parsed.get("citations", []):
        md += f"- {cit}\n"
    if not parsed.get("citations"):
        md += "No structured citations retrieved.\n"
    md += f"\n## Confidence Note\n\n{parsed.get('confidence') or 'N/A'}\n\n"
    md += "---\n\n*Draft for human review; a human signs off on any filing.*\n"
    return md


st.markdown("### :shield: Vigil")
st.caption("Risk, Fraud & Regulatory Intelligence Copilot — all data is synthetic")

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown("#### Chat")
    cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        short = ex if len(ex) <= 55 else ex[:52] + "..."
        if cols[i % 2].button(short, key=f"ex_{i}", use_container_width=True):
            st.session_state["pending"] = EXAMPLES[i]

    chat_box = st.container(height=420)
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"][:3000])

    user_input = st.chat_input("Ask Vigil...")
    question = None
    if user_input:
        question = user_input
    elif "pending" in st.session_state:
        question = st.session_state.pop("pending")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with chat_box:
            with st.chat_message("user"):
                st.markdown(question)

        with st.spinner("Vigil is investigating..."):
            parsed, elapsed = call_agent(question)

        answer = parsed.get("full_text", "") if not parsed.get("error") else f"Error: {parsed['error']}"
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state["latest"] = parsed
        st.session_state["q"] = question
        st.session_state["secs"] = elapsed
        st.rerun()

with right:
    st.markdown("#### Audit Panel")
    p = st.session_state["latest"]
    q = st.session_state["q"]
    secs = st.session_state["secs"]

    if p is None:
        st.info("Ask a question to see the audit-ready finding here.")
    elif p.get("error"):
        st.error(f"Agent error: {p['error']}")
    else:
        has_rid = len(p.get("record_ids", [])) > 0
        has_pol = p.get("has_policy", False)
        if not has_rid or not has_pol:
            parts = []
            if not has_rid:
                parts.append("no record ID")
            if not has_pol:
                parts.append("no policy clause")
            st.warning(f"**Not citable:** this response contains {' and '.join(parts)}. Do not present as a finding.")

        st.markdown("##### Verdict")
        st.markdown(p.get("verdict", "N/A"))

        if p.get("tables"):
            st.markdown("##### Evidence")
            for tbl in p["tables"]:
                if tbl.get("title"):
                    st.caption(tbl["title"])
                if tbl["columns"] and tbl["rows"]:
                    df = pd.DataFrame(tbl["rows"], columns=tbl["columns"])
                    st.dataframe(df, use_container_width=True, hide_index=True)

        if p.get("record_ids"):
            st.markdown("##### Record IDs")
            st.code(", ".join(p["record_ids"]), language=None)

        if p.get("citations"):
            st.markdown("##### Policy Citations")
            for cit in p["citations"]:
                st.info(cit, icon=":material/policy:")

        if p.get("has_ring") and p.get("ring_data"):
            st.markdown("##### Account Graph")
            dot = build_dot(p["ring_data"])
            if dot:
                st.graphviz_chart(dot)

        if p.get("confidence"):
            st.markdown("##### Confidence Note")
            st.markdown(p["confidence"])

        st.markdown(f"**Measured wall-clock seconds for this call:** {secs}")

        md = make_markdown(q, p, secs)
        st.download_button(
            ":material/download: Download finding as Markdown",
            data=md,
            file_name=f"vigil_finding_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )
