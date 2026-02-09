import streamlit as st
import csv
import io
import math
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Optional

st.set_page_config(
    page_title="LinkedIn Network Intelligence - GVRN-AI",
    page_icon="🔗",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0f172a; }
    .block-container { padding-top: 2rem; }
    .hero-title {
        font-size: 2.5rem; font-weight: 800;
        background: linear-gradient(135deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .hero-subtitle { font-size: 1.1rem; color: #94a3b8; margin-top: 0.5rem; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border: 1px solid #475569; border-radius: 12px;
        padding: 1.2rem; text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 800; color: #38bdf8; }
    .metric-label { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
    .section-header {
        font-size: 1.3rem; font-weight: 700; color: #f1f5f9;
        margin-top: 2rem; margin-bottom: 1rem;
        padding-bottom: 0.5rem; border-bottom: 2px solid #334155;
    }
    .relationship-card {
        background: #1e293b; border: 1px solid #334155;
        border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;
    }
    .relationship-name { font-size: 1rem; font-weight: 600; color: #f1f5f9; }
    .relationship-company { font-size: 0.85rem; color: #64748b; }
    .strength-bar { height: 6px; border-radius: 3px; margin-top: 0.5rem; }
    .badge-warm { background: #22c55e; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
    .badge-cold { background: #f59e0b; color: #000; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
    .badge-dead { background: #ef4444; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
    .action-item {
        background: #1e293b; border-left: 3px solid #38bdf8;
        padding: 0.8rem 1rem; margin-bottom: 0.5rem;
        border-radius: 0 8px 8px 0; color: #e2e8f0;
    }
    .privacy-note {
        background: #1e293b; border: 1px solid #22c55e;
        border-radius: 10px; padding: 1rem;
        color: #86efac; font-size: 0.85rem; text-align: center;
    }
    div[data-testid="stMetricValue"] { color: #38bdf8; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 8px; color: #94a3b8; padding: 8px 16px; }
    .stTabs [aria-selected="true"] { background-color: #334155; color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

@dataclass
class Connection:
    first_name: str
    last_name: str
    email: str
    company: str
    position: str
    connected_on: datetime
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

@dataclass
class Message:
    sender: str
    recipient: str
    date: datetime
    content: str
    @property
    def is_deep(self):
        if len(self.content) < 100: return False
        shallow = ["congrats", "congratulations", "thanks", "thank you", "happy birthday", "great post"]
        if any(p in self.content.lower() for p in shallow) and len(self.content) < 150: return False
        return True

def load_sample_data():
    connections = [
        Connection("Sarah", "Chen", "", "Stripe", "Staff Engineer", datetime(2024, 1, 15)),
        Connection("Mike", "Torres", "", "Acme Corp", "VP Engineering", datetime(2023, 3, 20)),
        Connection("Jennifer", "Liu", "", "Google", "Product Manager", datetime(2022, 6, 10)),
        Connection("David", "Kim", "", "Meta", "AI Researcher", datetime(2023, 9, 5)),
        Connection("Lisa", "Park", "", "TechStartup", "Founder", datetime(2023, 11, 12)),
        Connection("James", "Wong", "", "Amazon", "Solutions Architect", datetime(2022, 2, 18)),
        Connection("Anna", "Lee", "", "Microsoft", "Senior PM", datetime(2024, 7, 22)),
        Connection("Chris", "Brown", "", "OpenAI", "Research Engineer", datetime(2023, 8, 30)),
        Connection("Rachel", "Green", "", "Anthropic", "ML Engineer", datetime(2023, 12, 14)),
        Connection("Tom", "Wilson", "", "Netflix", "Engineering Manager", datetime(2023, 4, 8)),
        Connection("Amy", "Zhang", "", "Stripe", "Senior Engineer", datetime(2024, 3, 1)),
        Connection("Ben", "Taylor", "", "Deloitte", "AI Consultant", datetime(2023, 5, 15)),
        Connection("Carmen", "Rodriguez", "", "Health Corp", "CTO", datetime(2022, 11, 20)),
        Connection("Derek", "Patel", "", "AWS", "Principal SA", datetime(2024, 6, 10)),
        Connection("Emma", "Walsh", "", "Telstra", "Digital Lead", datetime(2023, 7, 25)),
    ]
    messages = [
        Message("Sarah Chen", "Me", datetime(2024, 12, 15), "Hey! Great to connect. Would love to catch up about AI infrastructure sometime. I've been exploring some new patterns for distributed inference that might interest you."),
        Message("Me", "Sarah Chen", datetime(2024, 12, 16), "Absolutely! I've been working on some interesting agent architectures lately. Let's grab coffee next week? I think there could be some overlap with what you're doing at Stripe."),
        Message("Sarah Chen", "Me", datetime(2024, 12, 17), "Sounds great! Tuesday works for me. There's a cool AI meetup happening too if you're interested."),
        Message("Mike Torres", "Me", datetime(2024, 11, 20), "Thanks for the intro to that candidate - they were excellent! Really appreciate you thinking of us."),
        Message("Me", "Mike Torres", datetime(2024, 11, 21), "Glad it worked out! Let me know if you need any other referrals. Always happy to help."),
        Message("Jennifer Liu", "Me", datetime(2024, 5, 10), "Let's catch up soon! I'd love to hear about your new venture."),
        Message("David Kim", "Me", datetime(2024, 10, 5), "Your post on AI governance was really insightful. Would love to discuss further and maybe collaborate on something."),
        Message("Me", "David Kim", datetime(2024, 10, 6), "Thanks David! I'm putting together a framework for AI audits - happy to share more details if you're interested in contributing."),
        Message("Lisa Park", "Me", datetime(2024, 8, 15), "Congrats on the new role!"),
        Message("James Wong", "Me", datetime(2023, 6, 20), "Great meeting you at the conference! Let's stay in touch and catch up over coffee sometime."),
        Message("Ben Taylor", "Me", datetime(2024, 9, 12), "Hey Nathan, saw your post about AI governance frameworks. We should chat - I think there's a consulting angle here that could work for both of us."),
        Message("Me", "Ben Taylor", datetime(2024, 9, 13), "Absolutely Ben! I've been thinking about the enterprise governance gap. Would love to explore what a partnership could look like."),
        Message("Carmen Rodriguez", "Me", datetime(2024, 4, 20), "Thanks for the recommendation! It really helped with my application. I owe you one."),
        Message("Emma Walsh", "Me", datetime(2024, 7, 30), "Would you be open to a quick call about AI strategy for our digital transformation? Your healthcare background could be really relevant."),
        Message("Me", "Emma Walsh", datetime(2024, 7, 31), "Definitely! Let me know what time works for you next week. Happy to share some frameworks I've been developing."),
    ]
    endorsements_received = {"sarah chen": 2, "mike torres": 2, "david kim": 1, "chris brown": 3, "ben taylor": 1, "carmen rodriguez": 2}
    endorsements_given = {"sarah chen": 1, "mike torres": 1, "jennifer liu": 2, "emma walsh": 1}
    recs_received = {"mike torres": 1, "carmen rodriguez": 1}
    recs_given = {"jennifer liu": 1}
    return connections, messages, endorsements_received, endorsements_given, recs_received, recs_given

def analyze_network(connections, messages, endorse_recv, endorse_given, recs_recv, recs_given):
    HALF_LIFE = 180
    msgs_by_person = defaultdict(list)
    for m in messages:
        msgs_by_person[m.sender.lower()].append(m)
        msgs_by_person[m.recipient.lower()].append(m)
    results = []
    for conn in connections:
        name_lower = conn.full_name.lower()
        person_msgs = msgs_by_person.get(name_lower, [])
        deep_msgs = [m for m in person_msgs if m.is_deep]
        if deep_msgs: last_contact = max(m.date for m in deep_msgs)
        elif person_msgs: last_contact = max(m.date for m in person_msgs)
        else: last_contact = conn.connected_on
        days_since = (datetime.now() - last_contact).days
        strength = 100 * math.pow(0.5, days_since / HALF_LIFE)
        e_recv = endorse_recv.get(name_lower, 0)
        e_given = endorse_given.get(name_lower, 0)
        r_recv = recs_recv.get(name_lower, 0)
        r_given = recs_given.get(name_lower, 0)
        reciprocity = (r_given * 10 + e_given * 2) - (r_recv * 10 + e_recv * 2)
        vouch = 0
        if not person_msgs: vouch += 0
        elif not deep_msgs: vouch += 5
        elif len(deep_msgs) < 5: vouch += 15
        else: vouch += 30
        if days_since > 730: vouch += 0
        elif days_since > 365: vouch += 5
        elif days_since > 180: vouch += 10
        else: vouch += 20
        if r_recv > 0: vouch += 30
        elif r_given > 0: vouch += 10
        vouch += min(e_recv * 2, 10)
        if len(person_msgs) > 20: vouch += 10
        elif len(person_msgs) > 10: vouch += 5
        vouch = min(vouch, 100)
        status = "warm" if strength > 50 else ("cold" if strength > 20 else "dormant")
        results.append({"name": conn.full_name, "company": conn.company, "position": conn.position, "strength": round(strength, 1), "vouch_score": round(vouch, 1), "reciprocity": reciprocity, "days_since": days_since, "messages": len(person_msgs), "deep_messages": len(deep_msgs), "last_contact": last_contact, "status": status, "endorsements_received": e_recv, "endorsements_given": e_given, "recs_received": r_recv, "recs_given": r_given})
    return sorted(results, key=lambda x: x["strength"], reverse=True)

st.markdown('<p class="hero-title">🔗 LinkedIn Network Intelligence</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Break platform data asymmetry. Surface the insights LinkedIn won\'t show you.</p>', unsafe_allow_html=True)
st.markdown('<div class="privacy-note">🔒 All analysis runs locally. No data is sent to external servers. Your network data stays private.</div>', unsafe_allow_html=True)
st.markdown("---")

data_source = st.radio("Data Source", ["📊 Sample Data (Demo)", "📁 Upload LinkedIn Export"], horizontal=True)
if data_source == "📁 Upload LinkedIn Export":
    st.markdown("### Upload Your LinkedIn Export")
    st.markdown("1. Go to **LinkedIn Settings > Data Privacy > Get a copy of your data**\n2. Select: Connections, Messages, Endorsements, Recommendations\n3. Wait 24-72 hours, download and extract the ZIP\n4. Upload your Connections.csv below")
    uploaded = st.file_uploader("Upload Connections.csv", type="csv")
    if not uploaded:
        st.info("Upload your LinkedIn export to get started, or switch to Sample Data to see what's possible.")
        st.stop()

connections, messages, e_recv, e_given, r_recv, r_given = load_sample_data()
results = analyze_network(connections, messages, e_recv, e_given, r_recv, r_given)

st.markdown("")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{len(connections)}</div><div class="metric-label">Connections</div></div>', unsafe_allow_html=True)
with c2:
    advocates = len([r for r in results if r["vouch_score"] >= 40])
    st.markdown(f'<div class="metric-card"><div class="metric-value">{advocates}</div><div class="metric-label">Advocates</div></div>', unsafe_allow_html=True)
with c3:
    going_cold = len([r for r in results if r["status"] == "cold"])
    st.markdown(f'<div class="metric-card"><div class="metric-value">{going_cold}</div><div class="metric-label">Going Cold</div></div>', unsafe_allow_html=True)
with c4:
    they_owe = len([r for r in results if r["reciprocity"] > 0])
    st.markdown(f'<div class="metric-card"><div class="metric-value">{they_owe}</div><div class="metric-label">Owe You Favors</div></div>', unsafe_allow_html=True)
with c5:
    dormant = len([r for r in results if r["status"] == "dormant"])
    st.markdown(f'<div class="metric-card"><div class="metric-value">{dormant}</div><div class="metric-label">Dormant</div></div>', unsafe_allow_html=True)

st.markdown("")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 Network Health", "⭐ Advocates", "💰 Reciprocity", "🔄 Resurrect", "🎯 Warm Paths"])

with tab1:
    st.markdown('<div class="section-header">Relationship Strength Map</div>', unsafe_allow_html=True)
    for r in results:
        badge_class = "badge-warm" if r["status"] == "warm" else ("badge-cold" if r["status"] == "cold" else "badge-dead")
        badge_text = r["status"].upper()
        bar_color = "#22c55e" if r["strength"] > 50 else ("#f59e0b" if r["strength"] > 20 else "#ef4444")
        bar_width = max(r["strength"], 2)
        st.markdown(f'<div class="relationship-card"><div style="display:flex;justify-content:space-between;align-items:center;"><div><span class="relationship-name">{r["name"]}</span> <span class="{badge_class}" style="margin-left:8px;">{badge_text}</span><br><span class="relationship-company">{r["position"]} at {r["company"]}</span></div><div style="text-align:right;"><span style="color:#38bdf8;font-weight:700;font-size:1.2rem;">{r["strength"]}%</span><br><span style="color:#64748b;font-size:0.75rem;">{r["days_since"]}d ago - {r["messages"]} msgs</span></div></div><div class="strength-bar" style="background:#334155;"><div style="height:6px;border-radius:3px;background:{bar_color};width:{bar_width}%;"></div></div></div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-header">Top Advocates - People Who Would Vouch for You</div>', unsafe_allow_html=True)
    advocates_sorted = sorted(results, key=lambda x: x["vouch_score"], reverse=True)
    for r in advocates_sorted:
        vouch_color = "#22c55e" if r["vouch_score"] >= 40 else ("#f59e0b" if r["vouch_score"] >= 20 else "#64748b")
        signals = []
        if r["recs_received"] > 0: signals.append("Recommended you")
        if r["endorsements_received"] > 0: signals.append(f'{r["endorsements_received"]} endorsements')
        if r["deep_messages"] > 0: signals.append(f'{r["deep_messages"]} deep conversations')
        signal_text = " | ".join(signals) if signals else "No strong signals yet"
        st.markdown(f'<div class="relationship-card"><div style="display:flex;justify-content:space-between;align-items:center;"><div><span class="relationship-name">{r["name"]}</span><br><span class="relationship-company">{r["position"]} at {r["company"]}</span><br><span style="color:#94a3b8;font-size:0.8rem;">{signal_text}</span></div><div style="text-align:right;"><span style="color:{vouch_color};font-weight:700;font-size:1.5rem;">{r["vouch_score"]}</span><br><span style="color:#64748b;font-size:0.75rem;">Vouch Score</span></div></div></div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-header">Reciprocity Ledger - Social Capital Balance Sheet</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### They Owe You (Safe to Ask)")
        they_owe_list = sorted([r for r in results if r["reciprocity"] > 0], key=lambda x: x["reciprocity"], reverse=True)
        if they_owe_list:
            for r in they_owe_list:
                st.markdown(f'<div class="relationship-card"><span class="relationship-name">{r["name"]}</span> - <span class="relationship-company">{r["company"]}</span><br><span style="color:#22c55e;font-weight:600;">+{r["reciprocity"]} points</span></div>', unsafe_allow_html=True)
        else:
            st.markdown("*No one currently owes you*")
    with col2:
        st.markdown("#### You Owe Them (Consider Helping)")
        you_owe_list = sorted([r for r in results if r["reciprocity"] < 0], key=lambda x: x["reciprocity"])
        if you_owe_list:
            for r in you_owe_list:
                st.markdown(f'<div class="relationship-card"><span class="relationship-name">{r["name"]}</span> - <span class="relationship-company">{r["company"]}</span><br><span style="color:#ef4444;font-weight:600;">{r["reciprocity"]} points</span></div>', unsafe_allow_html=True)
        else:
            st.markdown("*You are all square!*")

with tab4:
    st.markdown('<div class="section-header">Conversation Resurrection - Dormant Threads Worth Reviving</div>', unsafe_allow_html=True)
    catch_up_phrases = ["catch up", "grab coffee", "get together", "happy to help", "let me know", "would love to"]
    resurrections = []
    msgs_by_person = defaultdict(list)
    for m in messages:
        msgs_by_person[m.sender.lower()].append(m)
        msgs_by_person[m.recipient.lower()].append(m)
    for conn in connections:
        person_msgs = msgs_by_person.get(conn.full_name.lower(), [])
        for m in person_msgs:
            days_ago = (datetime.now() - m.date).days
            if days_ago > 90 and any(p in m.content.lower() for p in catch_up_phrases):
                resurrections.append({"name": conn.full_name, "company": conn.company, "days_ago": days_ago, "hook": m.content[:120]})
                break
    if resurrections:
        for r in sorted(resurrections, key=lambda x: x["days_ago"]):
            st.markdown(f'<div class="action-item"><strong>{r["name"]}</strong> - {r["company"]} - <span style="color:#f59e0b;">{r["days_ago"]} days ago</span><br><em style="color:#94a3b8;">"{r["hook"]}..."</em></div>', unsafe_allow_html=True)
    else:
        st.info("No dormant conversations found with natural re-engagement hooks.")

with tab5:
    st.markdown('<div class="section-header">Warm Path Discovery - Find Your Bridge to Any Company</div>', unsafe_allow_html=True)
    target = st.text_input("Target Company", placeholder="e.g. Stripe, Google, Anthropic")
    if target:
        paths = [r for r in results if target.lower() in r["company"].lower()]
        if paths:
            for r in sorted(paths, key=lambda x: x["strength"] + x["vouch_score"], reverse=True):
                warmth = r["strength"] + r["vouch_score"]
                if warmth > 80: approach, ac = "Direct ask - strong relationship", "#22c55e"
                elif warmth > 40: approach, ac = "Warm request after catch-up", "#f59e0b"
                else: approach, ac = "Re-engage first, then ask", "#ef4444"
                st.markdown(f'<div class="relationship-card"><div style="display:flex;justify-content:space-between;align-items:center;"><div><span class="relationship-name">{r["name"]}</span><br><span class="relationship-company">{r["position"]} at {r["company"]}</span><br><span style="color:{ac};font-size:0.85rem;">{approach}</span></div><div style="text-align:right;"><span style="color:#38bdf8;font-size:0.85rem;">Strength: {r["strength"]}%</span><br><span style="color:#818cf8;font-size:0.85rem;">Vouch: {r["vouch_score"]}</span></div></div></div>', unsafe_allow_html=True)
        else:
            st.warning(f"No direct connections found at {target}. Try a broader search.")
    else:
        st.info("Enter a company name above to find your warmest path in.")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748b;font-size:0.8rem;padding:1rem;">Built by <a href="https://gvrn-ai.com" style="color:#38bdf8;">GVRN-AI</a> | <a href="https://github.com/CloudAIX/linkedin-intelligence" style="color:#38bdf8;">GitHub</a> | Breaking Platform Data Asymmetry</div>', unsafe_allow_html=True)
