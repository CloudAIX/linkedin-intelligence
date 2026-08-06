"""
LinkedIn Network Intelligence — Web Demo
Streamlit front-end for linkedin_intel.py.
Run: python3 -m streamlit run app.py

Upload your LinkedIn data export (Connections.csv, messages.csv, and optionally
endorsement/recommendation CSVs), or explore with the bundled sample data.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from linkedin_intel import (
    LinkedInDataParser,
    NetworkAnalyzer,
    generate_report,
    generate_sample_data,
)

st.set_page_config(page_title="LinkedIn Network Intelligence", page_icon="🕸️", layout="wide")

SAMPLE_DIR = Path(__file__).parent / "output" / "sample_linkedin_export"


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Analyzing your network…")
def build_analyzer(data_dir: str, my_name: str) -> NetworkAnalyzer:
    parser = LinkedInDataParser(Path(data_dir)).parse_all()
    return NetworkAnalyzer(parser, my_name=my_name)


def score_row(s) -> dict:
    return {
        "Name": s.name,
        "Company": s.company,
        "Strength": round(s.half_life_strength, 1),
        "Vouch score": round(s.vouch_score, 1),
        "Reciprocity": s.reciprocity_balance,
        "Days since contact": s.days_since_contact,
        "Messages": s.messages_exchanged,
    }


# ── Sidebar: data source ──────────────────────────────────────────────────────

st.sidebar.title("🕸️ Network Intelligence")
st.sidebar.caption("Break platform data asymmetry — your export, your insights.")

my_name = st.sidebar.text_input("Your name (as it appears in messages)", value="")

source = st.sidebar.radio("Data source", ["Sample data", "Upload my LinkedIn export"])

data_dir = None

if source == "Sample data":
    if not SAMPLE_DIR.exists():
        generate_sample_data(SAMPLE_DIR)
    data_dir = str(SAMPLE_DIR)
    st.sidebar.success("Using bundled sample network")
else:
    uploads = st.sidebar.file_uploader(
        "Upload export CSVs",
        type="csv",
        accept_multiple_files=True,
        help="From LinkedIn: Settings → Data privacy → Get a copy of your data. "
             "Upload Connections.csv and messages.csv at minimum.",
    )
    if uploads:
        tmp = Path(tempfile.mkdtemp(prefix="li_intel_"))
        for f in uploads:
            (tmp / f.name).write_bytes(f.getvalue())
        missing = [n for n in ("Connections.csv", "messages.csv")
                   if not (tmp / n).exists()]
        if missing:
            st.sidebar.warning(f"Missing: {', '.join(missing)} — analysis may be partial.")
        data_dir = str(tmp)
        st.sidebar.success(f"{len(uploads)} file(s) loaded")

if data_dir is None:
    st.title("LinkedIn Network Intelligence")
    st.write(
        "Analyze your LinkedIn data export to surface relationship decay, "
        "vouch scores, reciprocity, warm paths into target companies, and "
        "conversations worth reviving."
    )
    st.info("Choose **Sample data** in the sidebar, or upload your own export to begin.")
    st.stop()

analyzer = build_analyzer(data_dir, my_name)
scores = analyzer.calculate_relationship_scores()

# ── KPI header ────────────────────────────────────────────────────────────────

st.title("Your Network, Decoded")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Connections", len(analyzer.parser.connections))
k2.metric("Messages parsed", len(analyzer.parser.messages))
active = sum(1 for s in scores if s.days_since_contact <= 90)
k3.metric("Active (≤90 days)", active)
cold = sum(1 for s in scores if s.days_since_contact > 365)
k4.metric("Gone cold (>1 yr)", cold)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_warm, tab_cold, tab_advocates, tab_recip, tab_paths, tab_revive, tab_report = st.tabs(
    ["🔥 Warmest", "🧊 Going cold", "📣 Advocates", "⚖️ Reciprocity",
     "🚪 Warm paths", "💬 Revive", "📄 Full report"]
)

with tab_warm:
    st.subheader("Strongest current relationships")
    st.caption("Ranked by half-life relationship strength (recency-weighted interaction depth).")
    st.dataframe([score_row(s) for s in analyzer.get_warmest_relationships()],
                 use_container_width=True)

with tab_cold:
    st.subheader("Valuable relationships going cold")
    st.caption("High vouch score, long silence — reach out before the relationship decays.")
    st.dataframe([score_row(s) for s in analyzer.get_going_cold()],
                 use_container_width=True)

with tab_advocates:
    st.subheader("Top advocates")
    st.caption("People most likely to vouch for you: recommendations, endorsements, deep conversations.")
    st.dataframe([score_row(s) for s in analyzer.get_top_advocates()],
                 use_container_width=True)

with tab_recip:
    they_owe, you_owe = analyzer.get_reciprocity_balance()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("They owe you")
        st.caption("You've given more than you've received — safe to ask.")
        st.dataframe([score_row(s) for s in they_owe], use_container_width=True)
    with c2:
        st.subheader("You owe them")
        st.caption("Give back before you ask for anything.")
        st.dataframe([score_row(s) for s in you_owe], use_container_width=True)

with tab_paths:
    st.subheader("Warm paths into a target company")
    target = st.text_input("Target company", placeholder="e.g. Atlassian")
    if target:
        paths = analyzer.find_warm_paths(target)
        if paths:
            st.dataframe([score_row(s) for s in paths], use_container_width=True)
        else:
            st.info(f"No connections found at “{target}”.")

with tab_revive:
    st.subheader("Conversations worth reviving")
    st.caption("Dormant threads where someone promised to catch up — a ready-made re-opener.")
    opps = analyzer.find_resurrection_opportunities()
    if opps:
        st.dataframe(
            [{
                "Name": o["name"],
                "Company": o["company"],
                "Days ago": o["days_ago"],
                "Last message": o["last_message_date"].strftime("%Y-%m-%d")
                                if isinstance(o["last_message_date"], datetime) else o["last_message_date"],
                "Hook": o["hook"],
            } for o in opps],
            use_container_width=True,
        )
    else:
        st.info("No dormant catch-up threads found.")

with tab_report:
    st.subheader("Full intelligence report")
    report_md = generate_report(analyzer)
    st.download_button(
        "Download report (Markdown)",
        report_md,
        file_name="network_intelligence_report.md",
        mime="text/markdown",
    )
    st.markdown(report_md)
