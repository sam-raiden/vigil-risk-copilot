"""Local test of app/streamlit_app.py with a fake Snowflake session.

Runs the real app code under Streamlit's AppTest (pin streamlit==1.35.0, as deployed).
It tests rendering and parsing only; it does NOT call the real agent or touch Snowflake.
Run: python tests/test_local.py
"""
import json, os, re, sys, types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app", "streamlit_app.py")

RING = {
    "ring": {"ring_id": "RING-001", "shared_link": "Orion Trading Co", "status": "RING"},
    "edges": [{"account_a": "ACC-0031", "account_b": "ACC-003%d" % i} for i in (2, 3, 4, 5)],
}
TEXT = (
    "Verdict: ACC-0031 is part of RING-001, a five-account ring paying Orion Trading Co within 72 hours.\n"
    "Evidence:\n- TXN-000609 on 2026-09-20 links ACC-0031 to ACC-0032.\n- RING-001 has five members.\n"
    "Policy citations:\n- POL-AML-001 Clause 4 - coordinated activity must be escalated.\n"
    "Confidence note: High confidence. EDD status is unknown. A human must sign off."
)
RESPONSE = json.dumps({"content": [
    {"type": "text", "text": TEXT},
    {"type": "tool_result", "tool_result": {"name": "ring_lookup", "status": "success",
        "content": [{"json": {"result": json.dumps(RING)}}]}},
]})


class Row(dict):
    def __getitem__(self, k):
        return dict.__getitem__(self, k) if isinstance(k, str) else list(self.values())[k]


class Q:
    def __init__(self, sql):
        self.sql = sql

    def collect(self):
        if "DATA_AGENT_RUN" in self.sql:
            return [(RESPONSE,)]
        return [Row(CITATION="POL-AML-001 Clause 4", DOC_TITLE="AML Policy",
                    CLAUSE_TITLE="Coordinated activity", CLAUSE_TEXT="Accounts acting together must be escalated.")]


class Session:
    def sql(self, s):
        return Q(s)


def install_stub():
    for name in ("snowflake", "snowflake.snowpark", "snowflake.snowpark.context"):
        sys.modules[name] = types.ModuleType(name)
    sys.modules["snowflake.snowpark.context"].get_active_session = lambda: Session()


def main():
    install_stub()
    from streamlit.testing.v1 import AppTest

    src = open(APP, encoding="utf-8").read()
    bad = re.findall(r"container\(height=|:material/|hide_index|googleapis|cdn", src)
    assert not bad, "forbidden for Streamlit 1.35.0 / no-CDN: %s" % bad

    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception, at.exception
    print("PASS: empty state renders, no exception")

    btns = [b for b in at.button if "Ask" in str(b.label)]
    print("example buttons found:", len(btns))
    assert btns, "no example buttons"
    btns[3].click().run()
    assert not at.exception, at.exception
    msgs = at.session_state["messages"]
    assert msgs and msgs[-1]["role"] == "assistant", "no assistant message stored"
    p = msgs[-1]["parsed"]
    assert p["cited"] and p["has_ring"], p
    assert "RING-001" in p["rids"] and "POL-AML-001 Clause 4" in p["pol_cits"]
    print("PASS: example click -> agent (stubbed) -> parsed: cited=%s ring=%s rids=%s" % (p["cited"], p["has_ring"], p["rids"]))

    html = " ".join(m.value for m in at.markdown)
    for needle in ("RING-001", "Orion Trading Co", "POL-AML-001 Clause 4", "Accounts acting together"):
        assert needle in html, "missing in rendered page: " + needle
    print("PASS: verdict, ring id, source chip and quoted clause text all rendered")

    at.chat_input[0].set_value("Is this account suspicious?").run()
    assert not at.exception, at.exception
    print("PASS: typed question accepted, no exception")
    print("ALL LOCAL TESTS PASSED")


if __name__ == "__main__":
    main()
