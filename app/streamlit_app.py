import streamlit as st
import json, time, re, html as html_mod
import pandas as pd
from datetime import datetime, timezone
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Vigil", layout="wide")
session = get_active_session()

CARD = (
    "border-radius:8px;padding:16px 18px;margin-bottom:12px;"
    "border:1px solid rgba(128,128,128,.2);background:rgba(128,128,128,.06);"
)
st.markdown(
    "<style>"
    ".vcard{" + CARD + "}"
    ".vcard-verdict{" + CARD + "border-left:4px solid rgba(128,128,128,.35);}"
    ".vcard-verdict.cited{border-left-color:#2ea043;}"
    ".vcard-verdict.notcitable{border-left-color:#da3633;}"
    ".vcard-policy{" + CARD + "border-left:3px solid rgba(59,130,246,.5);}"
    ".vcard-conf{" + CARD + "opacity:.85;font-size:.92em;}"
    ".chip{display:inline-block;padding:2px 10px;border-radius:12px;font-size:.78em;"
    "margin:2px 3px;}"
    ".chip-green{background:rgba(46,160,67,.15);color:#2ea043;border:1px solid rgba(46,160,67,.3);}"
    ".chip-red{background:rgba(218,54,51,.12);color:#da3633;border:1px solid rgba(218,54,51,.3);}"
    ".chip-blue{background:rgba(59,130,246,.12);color:#3b82f6;border:1px solid rgba(59,130,246,.3);}"
    ".chip-gray{background:rgba(128,128,128,.12);color:inherit;border:1px solid rgba(128,128,128,.25);}"
    ".pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.72em;"
    "font-family:monospace;margin:1px 2px;background:rgba(128,128,128,.10);"
    "border:1px solid rgba(128,128,128,.2);}"
    ".footer-banner{text-align:center;padding:8px;font-size:.82em;opacity:.7;"
    "border-top:1px solid rgba(128,128,128,.2);margin-top:16px;}"
    ".summary-line{font-size:.9em;opacity:.8;}"
    "</style>",
    unsafe_allow_html=True,
)

EXAMPLES = [
    "Why was account ACC-0007 flagged for structuring?",
    "Was the remittance on account ACC-0012 to the high risk country compliant?",
    "Show me the velocity pattern on account ACC-0019.",
    "Is account ACC-0031 connected to anything else?",
    "Are we compliant with our liquidity coverage ratio?",
    "Which loan accounts are NPA and what provisioning is required?",
]
SHORT = [
    "Structuring (ACC-0007)",
    "High-risk remittance (ACC-0012)",
    "Velocity pattern (ACC-0019)",
    "Ring connections (ACC-0031)",
    "LCR compliance",
    "NPA provisioning",
]
for k, v in [("messages", []), ("parsed", None), ("q", None), ("secs", None)]:
    if k not in st.session_state:
        st.session_state[k] = v


def md_to_html(text):
    t = html_mod.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    lines = t.split("\n")
    out, in_list = [], False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[-*]\s+", stripped):
            if not in_list:
                out.append("<ul style='margin:4px 0;padding-left:20px;'>")
                in_list = True
            item = re.sub(r"^[-*]\s+", "", stripped)
            out.append("<li>" + item + "</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            if stripped:
                out.append(stripped + "<br>")
    if in_list:
        out.append("</ul>")
    result = "\n".join(out)
    if result.endswith("<br>"):
        result = result[:-4]
    return result


def call_agent(question):
    payload = json.dumps(
        {"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}]}
    )
    escaped = payload.replace("\\", "\\\\").replace("'", "\\'")
    sql = (
        "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN("
        "'VIGIL.CORE.VIGIL_AGENT', '{}')".format(escaped)
    )
    t0 = time.time()
    rows = session.sql(sql).collect()
    elapsed = round(time.time() - t0, 1)
    return rows[0][0], elapsed


_SECTION_RE = re.compile(
    r"(?:^|\n)\s*\*{0,2}(Verdict|Evidence|Policy\s*citations?|Confidence\s*note)\s*"
    r"[\*:]*\s*[:\u2014\-]*\s*",
    re.IGNORECASE,
)
_FRAG_RE = re.compile(r"^\([^)]*\)\s*[:*]*\s*")
_RID_RE = re.compile(r"(?:TXN-\d+|ACC-\d+|ALT-\d+|RING-\d+|LN-\d+|\d{4}-\d{2}-\d{2})")
_POL_RE = re.compile(r"POL-[A-Z]+-\d+\s+Clause\s+[\d.]+")
_CLAUSE_RE = re.compile(r"[Cc]lause\s+\d")


def parse_agent(raw_json):
    data = json.loads(raw_json)
    if "code" in data and "message" in data and data.get("code") != "200":
        return {"error": data.get("message", "Agent error")}

    content = data.get("content", [])
    texts, tables, search_cits, ring_data = [], [], [], None

    for item in content:
        t = item.get("type")
        if t == "text":
            texts.append(item.get("text", ""))
            for ann in item.get("annotations", []):
                if ann.get("type") == "cortex_search_citation":
                    search_cits.append(ann.get("text", ""))
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

    full = "\n".join(texts)
    sections = split_sections(full)
    rids = sorted(set(_RID_RE.findall(full)))
    pol_cits = _POL_RE.findall(full)
    has_rid = len(rids) > 0
    has_pol = len(pol_cits) > 0 or bool(_CLAUSE_RE.search(full)) or len(search_cits) > 0
    has_ring = ring_data is not None and "ring_id" in str(ring_data).lower()

    return {
        "error": None,
        "full_text": full,
        "sections": sections,
        "tables": tables,
        "search_cits": search_cits,
        "pol_cits": pol_cits,
        "rids": rids,
        "has_rid": has_rid,
        "has_pol": has_pol,
        "cited": has_rid and has_pol,
        "has_ring": has_ring,
        "ring_data": ring_data,
        "summary": build_summary(sections, full),
    }


def split_sections(text):
    parts = {"verdict": "", "evidence": "", "policy": "", "confidence": "", "raw": text}
    splits = list(_SECTION_RE.finditer(text))
    if not splits:
        parts["verdict"] = text.strip()
        return parts
    key_map = {"verdict": "verdict", "evidence": "evidence",
               "policy": "policy", "policy citations": "policy",
               "policy citation": "policy",
               "confidence note": "confidence", "confidence": "confidence"}
    for i, m in enumerate(splits):
        name = m.group(1).strip().lower()
        key = key_map.get(name, name.split()[0])
        start = m.end()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
        body = text[start:end].strip()
        body = _FRAG_RE.sub("", body)
        body = body.lstrip(":*").strip()
        parts[key] = body
    return parts


def build_summary(sections, full):
    v = sections.get("verdict", "")
    if v:
        first = v.split("\n")[0].strip().lstrip("*").rstrip("*").strip()
        if len(first) > 120:
            first = first[:117] + "..."
        return first
    return full[:120].strip() + "..." if full else "No response"


def build_dot(ring_data):
    if not ring_data:
        return None
    edges = ring_data.get("edges", [])
    ring = ring_data.get("ring", {})
    if ring.get("status") == "NO_RING_FOUND" or not edges:
        return None
    rid = ring.get("ring_id", "")
    sl = ring.get("shared_link", "")
    lines = [
        "graph {",
        '  label="' + rid + ": " + sl + '"',
        '  labelloc="t"  fontsize=14',
        '  bgcolor="transparent"',
        '  node [shape=box style=filled fillcolor="#d0e0f0" fontsize=10 color="#888"]',
        '  edge [fontsize=8 color="#888"]',
    ]
    for e in edges:
        a, b = e.get("account_a", ""), e.get("account_b", "")
        sv = e.get("shared_value", "")
        lines.append('  "' + a + '" -- "' + b + '" [label="' + sv + '"]')
    lines.append("}")
    return "\n".join(lines)


def make_markdown(question, parsed, secs):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    s = parsed.get("sections", {})
    md = "# Vigil Finding\n\n"
    md += "**Question:** " + question + "\n\n"
    md += "**Timestamp:** " + ts + "\n\n"
    md += "**Measured wall-clock seconds for this call:** " + str(secs) + "\n\n"
    md += "## Verdict\n\n" + s.get("verdict", "N/A") + "\n\n"
    md += "## Evidence\n\n" + s.get("evidence", "N/A") + "\n\n"
    rids = parsed.get("rids") or ["None"]
    md += "**Record IDs:** " + ", ".join(rids) + "\n\n"
    for tbl in parsed.get("tables", []):
        md += "### " + tbl.get("title", "Data") + "\n\n"
        if tbl["columns"]:
            md += "| " + " | ".join(tbl["columns"]) + " |\n"
            md += "| " + " | ".join(["---"] * len(tbl["columns"])) + " |\n"
            for row in tbl["rows"][:20]:
                md += "| " + " | ".join(str(c) for c in row) + " |\n"
        md += "\n"
    md += "## Policy Citations\n\n" + s.get("policy", "N/A") + "\n\n"
    md += "## Confidence Note\n\n" + s.get("confidence", "N/A") + "\n\n"
    md += "---\n\n*Draft for human review; a human signs off on any filing.*\n"
    return md


def rid_pills(rids):
    return " ".join('<span class="pill">' + html_mod.escape(r) + "</span>" for r in rids)


def pol_badge(cit_text):
    m = re.match(r"(POL-[A-Z]+-\d+)\s+(Clause\s+[\d.]+)", cit_text)
    if m:
        doc, clause = m.group(1), m.group(2)
        rest = cit_text[m.end():]
        rest = re.sub(r"^\s*[\u2014\-]+\s*", " ", rest).strip()
        return (
            '<span class="chip chip-blue">' + html_mod.escape(doc) + "</span> "
            + "<strong>" + html_mod.escape(clause) + "</strong>"
            + (" &mdash; " + md_to_html(rest) if rest else "")
        )
    return md_to_html(cit_text)


hcol1, hcol2 = st.columns([6, 1])
with hcol1:
    st.markdown(
        '<span style="font-size:1.6em;font-weight:700;letter-spacing:-.02em;">Vigil</span>'
        '&ensp;<span style="font-size:.95em;opacity:.6;">Risk, Fraud & Regulatory Intelligence</span>',
        unsafe_allow_html=True,
    )
with hcol2:
    st.markdown(
        '<span class="chip chip-gray">Synthetic data</span>',
        unsafe_allow_html=True,
    )

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<span style="font-weight:600;">Examples</span>', unsafe_allow_html=True)
    chip_cols = st.columns(3)
    for i, label in enumerate(SHORT):
        if chip_cols[i % 3].button(label, key="ex_" + str(i), use_container_width=True):
            st.session_state["_pending"] = EXAMPLES[i]

    st.markdown("---")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(
                    '<span class="summary-line">' + html_mod.escape(msg.get("summary", "")) + "</span>"
                    + "<br><em style='opacity:.55;font-size:.82em;'>Full finding in the audit panel.</em>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(msg["content"])

with right:
    st.markdown('<span style="font-weight:600;">Audit Panel</span>', unsafe_allow_html=True)
    p = st.session_state["parsed"]
    q = st.session_state["q"]
    secs = st.session_state["secs"]

    if p is None:
        st.markdown(
            '<div class="vcard" style="text-align:center;opacity:.6;padding:40px;">'
            "Ask a question to see the audit-ready finding here."
            "</div>",
            unsafe_allow_html=True,
        )
    elif p.get("error"):
        st.error("Agent error: " + str(p["error"]))
    else:
        s = p.get("sections", {})
        cited = p.get("cited", False)

        cls = "cited" if cited else "notcitable"
        badge = (
            '<span class="chip chip-green">Cited</span>'
            if cited
            else '<span class="chip chip-red">Not citable</span>'
        )
        if not cited:
            reason_parts = []
            if not p.get("has_rid"):
                reason_parts.append("no record ID")
            if not p.get("has_pol"):
                reason_parts.append("no policy clause")
            badge += (
                ' <span style="font-size:.8em;opacity:.7;">'
                + " and ".join(reason_parts)
                + "</span>"
            )
        verdict_body = s.get("verdict", p.get("full_text", "No response")[:600])
        st.markdown(
            '<div class="vcard-verdict ' + cls + '">'
            + badge + "<br><br>"
            + md_to_html(verdict_body)
            + "</div>",
            unsafe_allow_html=True,
        )

        evidence_text = s.get("evidence", "")
        if evidence_text or p.get("tables") or p.get("rids"):
            st.markdown(
                '<div class="vcard"><strong>Evidence</strong><br><br>'
                + md_to_html(evidence_text)
                + "</div>",
                unsafe_allow_html=True,
            )
            for tbl in p.get("tables", []):
                if tbl.get("title"):
                    st.caption(tbl["title"])
                if tbl["columns"] and tbl["rows"]:
                    df = pd.DataFrame(tbl["rows"], columns=tbl["columns"])
                    st.dataframe(df, use_container_width=True)
            if p.get("rids"):
                st.markdown(
                    '<div style="margin-bottom:12px;">'
                    + rid_pills(p["rids"])
                    + "</div>",
                    unsafe_allow_html=True,
                )

        pol_text = s.get("policy", "")
        pol_lines = [
            l.strip().lstrip("-").strip()
            for l in pol_text.split("\n")
            if l.strip() and l.strip() != "-"
        ]
        if pol_lines:
            for line in pol_lines:
                st.markdown(
                    '<div class="vcard-policy">' + pol_badge(line) + "</div>",
                    unsafe_allow_html=True,
                )
        elif p.get("search_cits"):
            for cit in p["search_cits"]:
                st.markdown(
                    '<div class="vcard-policy">' + md_to_html(cit[:300]) + "</div>",
                    unsafe_allow_html=True,
                )

        if p.get("has_ring") and p.get("ring_data"):
            dot = build_dot(p["ring_data"])
            if dot:
                st.markdown(
                    '<div class="vcard"><strong>Account Graph</strong></div>',
                    unsafe_allow_html=True,
                )
                st.graphviz_chart(dot)

        conf = s.get("confidence", "")
        if conf:
            st.markdown(
                '<div class="vcard-conf">'
                + "<strong>Confidence</strong><br>"
                + md_to_html(conf)
                + "</div>",
                unsafe_allow_html=True,
            )

        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        md = make_markdown(q, p, secs)
        fcol1, fcol2 = st.columns([1, 1])
        with fcol1:
            st.markdown(
                "**Measured wall-clock seconds for this call:** " + str(secs)
            )
        with fcol2:
            st.download_button(
                "Download finding",
                data=md,
                file_name="vigil_finding_" + ts_str + ".md",
                mime="text/markdown",
                use_container_width=True,
            )
        st.markdown(
            '<div class="footer-banner">'
            "Draft for human review. A human signs off on every filing."
            "</div>",
            unsafe_allow_html=True,
        )


user_input = st.chat_input("Ask Vigil...")
question = None
if user_input:
    question = user_input
elif "_pending" in st.session_state:
    question = st.session_state.pop("_pending")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.status("Vigil is investigating...", expanded=True) as status:
        st.write("Querying transaction data...")
        raw, elapsed = call_agent(question)
        st.write("Parsing response...")
        parsed = parse_agent(raw)
        status.update(label="Done in " + str(elapsed) + "s", state="complete")

    summary = parsed.get("summary", "")
    st.session_state.messages.append(
        {"role": "assistant", "content": summary, "summary": summary}
    )
    st.session_state["parsed"] = parsed
    st.session_state["q"] = question
    st.session_state["secs"] = elapsed
    st.rerun()
