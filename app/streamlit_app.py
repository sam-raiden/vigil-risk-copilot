import streamlit as st
import json, time, re, html
html_mod = html
import pandas as pd
from datetime import datetime, timezone
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Vigil", layout="centered")
session = get_active_session()


def logo_svg(size=44, uid="a"):
    return (
        '<svg width="' + str(size) + '" height="' + str(size) + '" viewBox="0 0 48 48" '
        'aria-label="Vigil">'
        '<path d="M24 3 L42 10 V23 C42 34 34.5 41.5 24 45 C13.5 41.5 6 34 6 23 V10 Z" fill="#29B5E8"/>'
        '<path d="M12.5 24 C16 18 20 15.5 24 15.5 C28 15.5 32 18 35.5 24 C32 30 28 32.5 24 32.5 '
        'C20 32.5 16 30 12.5 24 Z" fill="#ffffff" opacity=".95"/>'
        '<circle cx="24" cy="24" r="5.2" fill="#11567F"/>'
        '<circle cx="25.8" cy="22.2" r="1.6" fill="#ffffff"/></svg>'
    )


st.markdown("""<style>
:root{
--v-accent:#29B5E8;--v-med:#11567F;
--v-text:#1E2A38;--v-secondary:#5B6B7B;
--v-surface:#F5F7FA;--v-border:#DDE3EA;
--v-page:#FFFFFF;--v-verdict-bg:#F5F9FC;
--v-user-bg:#EEF2F6;
}
@media (prefers-color-scheme: dark){:root{
--v-page:#0E1B27;--v-surface:#14263A;--v-border:#25405A;
--v-text:#E6EDF3;--v-secondary:#8FA3B5;
--v-accent:#29B5E8;--v-med:#29B5E8;
--v-verdict-bg:#14263A;--v-user-bg:#14263A;
}}
html,body,[class*="css"],.stMarkdown,button,input,textarea{font-family:-apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif !important;}
.block-container{max-width:820px !important;padding-top:1.2rem !important;padding-bottom:7rem !important;}
.stMarkdown p,.stMarkdown li{line-height:1.6;}
header[data-testid="stHeader"]{background:transparent;}
.v-topbar{display:flex;align-items:center;gap:12px;padding:10px 0 14px 0;border-bottom:1px solid var(--v-border);margin-bottom:16px;}
.v-topbar-title{font-size:20px;font-weight:600;color:var(--v-text);}
.v-topbar-sub{color:var(--v-secondary);font-size:.82rem;}
.v-topbar-chips{margin-left:auto;display:flex;gap:6px;}
.v-chip{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.72rem;font-weight:600;
border:1px solid var(--v-border);color:var(--v-secondary);background:transparent;}
.v-hero{text-align:center;padding:10px 0 14px 0;}
.v-hero h2{font-size:1.25rem;font-weight:600;margin:0 0 4px 0;padding:0;color:var(--v-text);}
.v-hero p{color:var(--v-secondary);font-size:.9rem;margin:0;}
.v-card{border:1px solid var(--v-border);border-radius:8px;padding:12px 14px;margin:4px 0 4px 0;
background:var(--v-page);transition:border-color .15s;}
.v-card:hover{border-color:var(--v-accent);}
.v-ct{font-weight:600;font-size:.9rem;line-height:1.3;color:var(--v-text);}
.v-ch{color:var(--v-secondary);font-size:.78rem;line-height:1.35;}
.v-asklink{font-size:.78rem;color:var(--v-med);font-weight:600;cursor:pointer;background:none;border:none;padding:0;margin-top:4px;}
.v-asklink:hover{text-decoration:underline;}
div[data-testid="stButton"] > button{border-radius:6px;border:none;background:transparent;
padding:2px 0;min-height:0;font-size:.78rem;font-weight:600;color:var(--v-med);
transition:color .15s;}
div[data-testid="stButton"] > button:hover{color:var(--v-accent);background:transparent;}
div[data-testid="stButton"] > button:focus:not(:active){color:var(--v-med);background:transparent;}
div[data-testid="stDownloadButton"] > button{background:var(--v-accent) !important;color:#fff !important;border:0 !important;
border-radius:6px;font-weight:700;transition:opacity .15s;}
div[data-testid="stDownloadButton"] > button:hover{opacity:.9;color:#fff !important;}
div[data-testid="stDownloadButton"] > button p{color:#fff !important;}
.v-user{display:flex;justify-content:flex-end;margin:22px 0 14px 0;}
.v-user div{max-width:78%;background:var(--v-user-bg);color:var(--v-text);border-radius:12px 12px 4px 12px;
padding:10px 16px;line-height:1.6;}
.v-who{display:flex;align-items:center;gap:8px;font-weight:600;font-size:.88rem;margin:6px 0 2px 0;color:var(--v-text);}
.v-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;
color:var(--v-secondary);font-weight:700;margin:18px 0 6px 0;}
.v-verdict{border:1px solid var(--v-border);border-left:3px solid var(--v-accent);border-radius:8px;
padding:12px 16px;background:var(--v-verdict-bg);}
.v-vlead{font-size:1.02rem;line-height:1.6;font-weight:600;color:var(--v-text);}
.v-body{line-height:1.6;color:var(--v-text);}
.v-body ul{margin:4px 0;padding-left:20px;}
.v-pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.72rem;font-weight:700;
letter-spacing:.02em;text-transform:none;}
.v-pill.ok{background:transparent;color:var(--v-med);border:1px solid var(--v-border);}
.v-pill.ok::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;
background:var(--v-accent);margin-right:5px;vertical-align:middle;}
.v-pill.no{background:transparent;color:#92610A;border:1px solid var(--v-border);}
.v-ids{margin:8px 0 4px 0;}
.v-id{display:inline-block;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.74rem;padding:1px 8px;
margin:2px 3px 2px 0;border-radius:6px;border:1px solid var(--v-border);background:var(--v-surface);color:var(--v-secondary);}
.v-src{display:inline-flex;align-items:center;gap:6px;padding:4px 12px 4px 5px;margin:3px 6px 3px 0;border-radius:999px;
border:1px solid var(--v-accent);background:var(--v-page);color:var(--v-med);font-size:.82rem;font-weight:600;}
.v-src b{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;
background:var(--v-accent);color:#fff;font-size:.7rem;}
div[data-testid="stExpander"] details,div[data-testid="stExpander"]{border-radius:8px !important;border-color:var(--v-border) !important;}
div[data-testid="stExpander"] summary{font-size:.86rem;}
div[data-testid="stGraphVizChart"]{border:1px solid var(--v-border);border-radius:8px;padding:12px;background:var(--v-page);}
.v-conf{color:var(--v-secondary);font-size:.88rem;line-height:1.6;border-left:2px solid var(--v-border);padding-left:12px;margin-top:16px;}
.v-foot{color:var(--v-secondary);font-size:.8rem;padding-top:10px;}
.v-review{color:var(--v-secondary);font-size:.76rem;margin:4px 0 6px 0;}
.v-sep{height:1px;background:var(--v-border);margin:26px 0 4px 0;}
.v-brandfoot{text-align:center;color:var(--v-secondary);font-size:.74rem;margin-top:28px;padding-top:10px;
border-top:1px solid var(--v-border);}
div[data-testid="stChatInput"]{border-radius:8px !important;border:1px solid var(--v-border) !important;overflow:hidden;
transition:border-color .15s;}
div[data-testid="stChatInput"]:focus-within{border-color:var(--v-accent) !important;box-shadow:0 0 0 1px var(--v-accent) !important;}
div[data-testid="stChatInput"] textarea{padding-left:14px !important;}
div[data-testid="stDataFrame"]{border-radius:8px;overflow:hidden;}
div[data-testid="stDataFrame"] [data-testid="glideDataEditor"] [class*="header"]{background:var(--v-surface) !important;}
</style>""", unsafe_allow_html=True)

EXAMPLES = [
    "Why was account ACC-0007 flagged for structuring?",
    "Was the remittance on account ACC-0012 to the high risk country compliant?",
    "Show me the velocity pattern on account ACC-0019.",
    "Is account ACC-0031 connected to anything else?",
    "Are we compliant with our liquidity coverage ratio?",
    "Which loan accounts are NPA and what provisioning is required?",
]
CARDS = [
    ("Structuring alert", "Why ACC-0007 was flagged"),
    ("High-risk remittance", "Was ACC-0012 compliant?"),
    ("Velocity pattern", "Pass-through on ACC-0019"),
    ("Ring connections", "Who is ACC-0031 linked to?"),
    ("LCR compliance", "Liquidity coverage vs floor"),
    ("NPA provisioning", "Loans in NPA and provisions"),
]
if "messages" not in st.session_state:
    st.session_state["messages"] = []


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
_RID_RE = re.compile(r"(?:TXN-\d+|ACC-\d+|ALT-\d+|RING-\d+|LN-\d+|\d{4}-\d{2}-\d{2})")
_POL_RE = re.compile(r"POL-[A-Z]+-\d+\s+Clause\s+[\d.]+")
_CLAUSE_RE = re.compile(r"[Cc]lause\s+\d")
_FRAG_RE = re.compile(r"^\([^)]*\)\s*[:*]*\s*")


def md_to_html(text):
    out, in_list = [], False
    for line in (text or "").split("\n"):
        s = line.strip()
        esc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(s))
        if s.startswith("- ") or s.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + esc[2:].strip() + "</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if s:
            out.append(esc + "<br>")
    if in_list:
        out.append("</ul>")
    result = "".join(out)
    if result.endswith("<br>"):
        result = result[:-4]
    return result


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
    v = sections.get("verdict", "") or full
    if not v:
        return "No response"
    first = ""
    for line in v.split("\n"):
        line = re.sub(r"\*\*|__|`", "", line).strip()
        line = re.sub(r"^[-*#>\s]+", "", line)
        line = _FRAG_RE.sub("", line).lstrip(":*").strip()
        if line:
            first = line
            break
    if not first:
        return "No response"
    if len(first) > 120:
        first = first[:117].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return first


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


_CIT_KEY = re.compile(r"(POL-[A-Z]+-\d+)\s+Clause\s+(\d+)")


def citations_of(parsed):
    seen, out = set(), []
    text = parsed.get("sections", {}).get("policy", "") + "\n" + parsed.get("full_text", "")
    for m in _CIT_KEY.finditer(text):
        key = m.group(1) + " Clause " + m.group(2)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


@st.cache_data(show_spinner=False)
def clause_lookup(keys):
    safe = [k for k in keys if re.fullmatch(r"POL-[A-Z]+-\d+ Clause \d+", k)]
    if not safe:
        return {}
    in_list = ",".join("'" + k + "'" for k in safe)
    rows = session.sql(
        "SELECT CITATION, DOC_TITLE, CLAUSE_TITLE, CLAUSE_TEXT FROM VIGIL.CORE.POLICY_CLAUSES "
        "WHERE CITATION IN (" + in_list + ")"
    ).collect()
    return {r["CITATION"]: (r["DOC_TITLE"], r["CLAUSE_TITLE"], r["CLAUSE_TEXT"]) for r in rows}


def policy_note(parsed, key):
    for line in parsed.get("sections", {}).get("policy", "").split("\n"):
        m = _CIT_KEY.search(line)
        if m and m.group(1) + " Clause " + m.group(2) == key:
            rest = re.sub(r"^[\s.\d]*[\u2014\-:]*\s*", "", line[m.end():]).strip().strip('"\u201c\u201d').strip()
            return rest
    return ""


_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\u20B9(])")


def verdict_lead(sections, full):
    v = sections.get("verdict", "") or full or ""
    lines = []
    for line in v.split("\n"):
        line = re.sub(r"\*\*|__|`", "", line).strip()
        line = re.sub(r"^[-*#>\s]+", "", line)
        line = _FRAG_RE.sub("", line).lstrip(":*").strip()
        if line:
            lines.append(line)
    if not lines:
        return "No response", ""
    sents = _SENT_RE.split(lines[0])
    lead = sents[0]
    used = 1
    if len(lead) < 90 and len(sents) > 1:
        lead = lead + " " + sents[1]
        used = 2
    rest = " ".join(sents[used:])
    remaining = ([rest] if rest else []) + lines[1:]
    return lead, "\n".join(remaining)


def build_dot(ring_data):
    if not ring_data:
        return None
    edges = ring_data.get("edges", [])
    ring = ring_data.get("ring", {})
    if ring.get("status") == "NO_RING_FOUND" or not edges:
        return None
    deg = {}
    for e in edges:
        for n in (e.get("account_a", ""), e.get("account_b", "")):
            deg[n] = deg.get(n, 0) + 1
    hub = max(deg, key=deg.get)
    title = ring.get("ring_id", "") + "  \u00b7  shared counterparty: " + ring.get("shared_link", "")
    lines = [
        "graph {",
        '  label="' + title.replace('"', "") + '" labelloc="t" fontsize=12 fontcolor="#1E2A38"',
        '  fontname="Helvetica" bgcolor="transparent" pad=0.3 nodesep=0.5',
        '  node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=11 '
        'fillcolor="#FFFFFF" color="#29B5E8" fontcolor="#1E2A38" penwidth=1 margin="0.18,0.08"]',
        '  edge [color="#8FA3B5" penwidth=1.4]',
        '  "' + hub + '" [fillcolor="#11567F" color="#11567F" '
        'fontcolor="#ffffff" penwidth=1.5]',
    ]
    for e in edges:
        lines.append('  "' + e.get("account_a", "") + '" -- "' + e.get("account_b", "") + '"')
    lines.append("}")
    return "\n".join(lines)


def render_answer(idx, msg):
    p, q, secs = msg["parsed"], msg["q"], msg["secs"]
    st.markdown('<div class="v-who">' + logo_svg(22, "m" + str(idx)) + "Vigil</div>", unsafe_allow_html=True)
    if p.get("error"):
        st.error("Agent error: " + str(p["error"]))
        return
    s = p.get("sections", {})
    cited = p.get("cited", False)
    if cited:
        pill = '<span class="v-pill ok">Cited</span>'
    else:
        why = []
        if not p.get("has_rid"):
            why.append("no record ID")
        if not p.get("has_pol"):
            why.append("no policy clause")
        pill = '<span class="v-pill no">Not citable' + (" &middot; " + " and ".join(why) if why else "") + "</span>"

    st.markdown('<div class="v-label">VERDICT &ensp;' + pill + "</div>", unsafe_allow_html=True)
    lead, more = verdict_lead(s, p.get("full_text", ""))
    st.markdown(
        '<div class="v-verdict"><div class="v-vlead">'
        + html_mod.escape(lead) + "</div>"
        + ('<div class="v-body" style="margin-top:6px;">' + md_to_html(more) + "</div>" if more else "")
        + "</div>",
        unsafe_allow_html=True,
    )

    ev = s.get("evidence", "")
    if ev or p.get("tables") or p.get("rids"):
        st.markdown('<div class="v-label">EVIDENCE</div>', unsafe_allow_html=True)
        if ev:
            st.markdown('<div class="v-body">' + md_to_html(ev) + "</div>", unsafe_allow_html=True)
        for tbl in p.get("tables", []):
            if tbl["columns"] and tbl["rows"]:
                if tbl.get("title"):
                    st.caption(tbl["title"])
                st.dataframe(pd.DataFrame(tbl["rows"], columns=tbl["columns"]), use_container_width=True)
        if p.get("rids"):
            st.markdown('<div class="v-ids">' + "".join(
                '<span class="v-id">' + html_mod.escape(r) + "</span>" for r in p["rids"]) + "</div>",
                unsafe_allow_html=True)

    cits = citations_of(p)
    if cits:
        st.markdown('<div class="v-label">SOURCES</div>', unsafe_allow_html=True)
        st.markdown("".join(
            '<span class="v-src"><b>' + str(i + 1) + "</b>" + html_mod.escape(c) + "</span>"
            for i, c in enumerate(cits)), unsafe_allow_html=True)
        found = clause_lookup(tuple(cits))
        for i, c in enumerate(cits):
            with st.expander("[" + str(i + 1) + "]  " + c):
                if c in found:
                    dt, ct, tx = found[c]
                    st.markdown("**" + dt + "** \u00b7 " + ct)
                    st.markdown("> " + tx.replace("\n", "\n> "))
                else:
                    st.caption("Clause text not found in VIGIL.CORE.POLICY_CLAUSES.")
                note = policy_note(p, c)
                if note:
                    st.caption("How it applies: " + note)
    elif p.get("search_cits"):
        st.markdown('<div class="v-label">SOURCES</div>', unsafe_allow_html=True)
        for i, c in enumerate(p["search_cits"]):
            with st.expander("[" + str(i + 1) + "]  Policy source"):
                st.markdown(c[:600])

    if p.get("has_ring") and p.get("ring_data"):
        dot = build_dot(p["ring_data"])
        if dot:
            st.markdown('<div class="v-label">ACCOUNT GRAPH</div>', unsafe_allow_html=True)
            st.graphviz_chart(dot, use_container_width=True)

    conf = s.get("confidence", "")
    if conf:
        st.markdown('<div class="v-conf"><strong>Confidence</strong> &middot; ' + md_to_html(conf) + "</div>",
                    unsafe_allow_html=True)

    f1, f2 = st.columns([3, 2])
    with f1:
        st.markdown('<div class="v-foot">Measured wall-clock seconds for this call: <strong>'
                    + str(secs) + "</strong></div>", unsafe_allow_html=True)
    with f2:
        st.download_button(
            "Download finding", data=make_markdown(q, p, secs),
            file_name="vigil_finding_" + msg["ts"] + ".md", mime="text/markdown",
            key="dl_" + str(idx), use_container_width=True,
        )
    st.markdown('<div class="v-review">Draft for human review. A human signs off on every filing.</div>',
                unsafe_allow_html=True)


st.markdown(
    '<div class="v-topbar">' + logo_svg(28, "h")
    + '<div><div class="v-topbar-title">Vigil</div>'
    '<div class="v-topbar-sub">Risk, fraud and regulatory intelligence</div></div>'
    '<div class="v-topbar-chips"><span class="v-chip">Synthetic data</span>'
    '<span class="v-chip">Human in the loop</span></div></div>',
    unsafe_allow_html=True,
)

msgs = st.session_state["messages"]
if not msgs:
    st.markdown(
        '<div class="v-hero"><h2>What should we look into?</h2>'
        "<p>Ask about an alert, an account, liquidity or credit. Every answer is cited.</p></div>",
        unsafe_allow_html=True,
    )
    for row in range(3):
        c1, c2 = st.columns(2, gap="small")
        for col, i in ((c1, row * 2), (c2, row * 2 + 1)):
            title, hint = CARDS[i]
            with col:
                st.markdown(
                    '<div class="v-card">'
                    '<div class="v-ct">' + title + '</div><div class="v-ch">' + hint + "</div></div>",
                    unsafe_allow_html=True,
                )
                if st.button("Ask \u2192", key="ex_" + str(i), use_container_width=True):
                    st.session_state["_pending"] = EXAMPLES[i]
else:
    for idx, msg in enumerate(msgs):
        if msg["role"] == "user":
            if idx > 0:
                st.markdown('<div class="v-sep"></div>', unsafe_allow_html=True)
            st.markdown('<div class="v-user"><div>' + html_mod.escape(msg["content"]) + "</div></div>",
                        unsafe_allow_html=True)
        else:
            render_answer(idx, msg)

st.markdown(
    '<div class="v-brandfoot">Vigil \u2014 built on Snowflake Cortex</div>',
    unsafe_allow_html=True,
)

user_input = st.chat_input("Ask Vigil anything about risk, fraud or compliance...")
question = user_input or st.session_state.pop("_pending", None)

if question:
    if msgs:
        st.markdown('<div class="v-sep"></div>', unsafe_allow_html=True)
    st.markdown('<div class="v-user"><div>' + html_mod.escape(question) + "</div></div>", unsafe_allow_html=True)
    with st.status("Vigil is investigating...", expanded=False) as status:
        raw, elapsed = call_agent(question)
        parsed = parse_agent(raw)
        status.update(label="Done in " + str(elapsed) + "s", state="complete")
    msgs.append({"role": "user", "content": question})
    msgs.append({
        "role": "assistant", "parsed": parsed, "q": question, "secs": elapsed,
        "ts": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "content": parsed.get("summary", ""),
    })
    st.rerun()