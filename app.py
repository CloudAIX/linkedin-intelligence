"""
AI Audit Toolkit — Web Demo
Streamlit front-end for the GVRN-AI audit framework.
Run: python3 -m streamlit run app.py
"""

import streamlit as st
import json
import io
from datetime import datetime
from pathlib import Path

# Import from the existing toolkit
from audit_toolkit import (
    Client, Opportunity, AuditProject,
    calculate_audit_roi,
    generate_interview_doc,
    generate_opportunity_matrix,
    generate_executive_report,
    generate_executive_pptx,
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="AI Audit Toolkit — GVRN-AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp {
        background-color: #0f1117;
    }
    
    /* Green accent for headers */
    h1, h2, h3 {
        color: #00C97B !important;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1a1a2e;
        border: 1px solid #2a2a44;
        border-radius: 12px;
        padding: 16px;
    }
    
    [data-testid="stMetricValue"] {
        color: #00C97B !important;
        font-size: 28px !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #00C97B;
        color: #1a1a2e;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
    }
    
    .stButton > button:hover {
        background-color: #00b36e;
        color: #1a1a2e;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1a2e;
        border-radius: 8px;
    }
    
    /* Info boxes */
    .gvrn-box {
        background-color: #1a1a2e;
        border-left: 4px solid #00C97B;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin: 12px 0;
    }
    
    .gvrn-stat {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #1a1a2e, #22223a);
        border: 1px solid #2a2a44;
        border-radius: 12px;
    }
    
    .gvrn-stat .number {
        font-size: 36px;
        font-weight: 700;
        color: #00C97B;
    }
    
    .gvrn-stat .label {
        font-size: 13px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR — CLIENT SETUP
# ============================================================================

with st.sidebar:
    st.image("https://img.shields.io/badge/GVRN--AI-Audit_Toolkit-00C97B?style=for-the-badge", use_container_width=True)
    st.markdown("### 🏢 Client Information")
    
    company_name = st.text_input("Company Name", value="Maplewood Residential Aged Care")
    
    industry = st.selectbox("Industry", [
        "aged_care",
        "healthcare", 
        "professional_services",
        "retail_ecommerce",
        "finance",
        "manufacturing",
    ], format_func=lambda x: x.replace("_", " ").title())
    
    employee_count = st.number_input("Employee Count", min_value=1, max_value=10000, value=40)
    contact_name = st.text_input("Primary Contact", value="Karen Mitchell")
    contact_email = st.text_input("Contact Email", value="karen.mitchell@maplewoodcare.com.au")
    avg_salary = st.number_input("Average Annual Salary ($)", min_value=30000, max_value=300000, value=62000, step=1000)
    implementation_cost = st.number_input("Est. Implementation Cost ($)", min_value=1000, max_value=500000, value=25000, step=1000)
    
    st.markdown("---")
    st.markdown("#### ⚡ Quick Actions")
    load_example = st.button("🔄 Load Example (Aged Care)", use_container_width=True)

# ============================================================================
# SESSION STATE
# ============================================================================

if "opportunities" not in st.session_state:
    st.session_state.opportunities = []

if load_example or (not st.session_state.opportunities):
    st.session_state.opportunities = [
        {
            "name": "Digital Incident Reporting & SIRS Compliance",
            "description": "Paper-based incident forms take 30-45 min each; SIRS notifications manually tracked in spreadsheet",
            "hours_saved_weekly": 6.0,
            "employees_affected": 3,
            "effort": "low",
            "impact": "high",
        },
        {
            "name": "AI-Assisted Quality Standards Documentation",
            "description": "Admin staff spend 12+ hrs/week compiling evidence portfolios for the 8 Aged Care Quality Standards",
            "hours_saved_weekly": 10.0,
            "employees_affected": 3,
            "effort": "low",
            "impact": "high",
        },
        {
            "name": "Automated AN-ACC Care Minutes Tracking",
            "description": "Manual tracking of care minutes across shifts; paper timesheets then re-entered into government portal",
            "hours_saved_weekly": 5.0,
            "employees_affected": 5,
            "effort": "low",
            "impact": "high",
        },
        {
            "name": "Electronic Medication Management",
            "description": "Paper medication charts with manual round tracking; double-handling increases medication error risk",
            "hours_saved_weekly": 4.0,
            "employees_affected": 8,
            "effort": "high",
            "impact": "high",
        },
        {
            "name": "Clinical Care Plan Automation",
            "description": "Quarterly care plan reviews done manually across 45 residents with paper-based assessments",
            "hours_saved_weekly": 3.0,
            "employees_affected": 8,
            "effort": "high",
            "impact": "high",
        },
        {
            "name": "Resident & Family Communication Portal",
            "description": "Manual phone calls and printed letters to families for care updates and incident notifications",
            "hours_saved_weekly": 3.0,
            "employees_affected": 4,
            "effort": "low",
            "impact": "low",
        },
        {
            "name": "Staff Rostering Optimisation",
            "description": "Manual roster creation in spreadsheets; difficulty balancing care minute targets and award conditions",
            "hours_saved_weekly": 5.0,
            "employees_affected": 2,
            "effort": "low",
            "impact": "low",
        },
    ]

# Build objects from state
client = Client(
    company_name=company_name,
    industry=industry,
    employee_count=employee_count,
    contact_name=contact_name,
    contact_email=contact_email,
    avg_salary=avg_salary,
)

opportunities = []
for o in st.session_state.opportunities:
    opportunities.append(Opportunity(
        name=o["name"],
        description=o["description"],
        hours_saved_weekly=o["hours_saved_weekly"],
        employees_affected=o["employees_affected"],
        effort=o["effort"],
        impact=o["impact"],
    ))

project = AuditProject(
    client=client,
    opportunities=opportunities,
    created_date=datetime.now().isoformat(),
    interviews_completed=8,
    status="analysis",
)

roi_data = calculate_audit_roi(opportunities, avg_salary, implementation_cost)

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.markdown("# 🎯 AI Audit Toolkit")
st.markdown(f"**{company_name}** — {industry.replace('_', ' ').title()} | {employee_count} employees")

# ============================================================================
# TAB LAYOUT
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🎯 Opportunities", 
    "📋 Interview Questions",
    "📈 ROI Analysis",
    "📥 Downloads",
])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================

with tab1:
    st.markdown("## Executive Summary")
    
    combined = roi_data["combined"]
    
    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Opportunities", len(opportunities))
    with col2:
        quick_wins = [o for o in opportunities if o.category == "quick_win"]
        st.metric("Quick Wins", len(quick_wins))
    with col3:
        st.metric("Hours Saved / Week", f"{combined['hours_saved_weekly']:.0f}")
    with col4:
        st.metric("Total Annual Value", f"${combined['total_annual_value']:,.0f}")
    
    st.markdown("---")
    
    # ROI highlights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="gvrn-stat">
            <div class="number">${combined['annual_savings']:,.0f}</div>
            <div class="label">Annual Cost Savings</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="gvrn-stat">
            <div class="number">{combined['roi_percentage']:.0f}%</div>
            <div class="label">First Year ROI</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="gvrn-stat">
            <div class="number">{combined['payback_months']:.1f} mo</div>
            <div class="label">Payback Period</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Opportunity matrix visual
    st.markdown("### Opportunity Matrix")
    
    matrix_data = {
        "🎯 Quick Wins": [o for o in opportunities if o.category == "quick_win"],
        "🚀 Big Swings": [o for o in opportunities if o.category == "big_swing"],
        "✨ Nice-to-Haves": [o for o in opportunities if o.category == "nice_to_have"],
        "⏸️ Deprioritize": [o for o in opportunities if o.category == "deprioritize"],
    }
    
    col1, col2 = st.columns(2)
    for i, (cat_name, cat_opps) in enumerate(matrix_data.items()):
        with col1 if i % 2 == 0 else col2:
            if cat_opps:
                with st.expander(f"{cat_name} ({len(cat_opps)})", expanded=(i < 2)):
                    for opp in cat_opps:
                        hrs = opp.hours_saved_weekly * opp.employees_affected
                        st.markdown(f"**{opp.name}** — {hrs:.0f} hrs/week saved")
                        st.caption(opp.description)

# ============================================================================
# TAB 2: OPPORTUNITIES
# ============================================================================

with tab2:
    st.markdown("## 🎯 Identified Opportunities")
    st.markdown("Edit existing opportunities or add new ones.")
    
    # Display existing opportunities
    for i, opp_data in enumerate(st.session_state.opportunities):
        with st.expander(f"**{i+1}. {opp_data['name']}** — {opp_data['effort'].upper()} effort / {opp_data['impact'].upper()} impact"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Description:** {opp_data['description']}")
                st.markdown(f"**Hours saved/week:** {opp_data['hours_saved_weekly']} × {opp_data['employees_affected']} employees")
            with col2:
                # Category badge
                cat = Opportunity(
                    name="", description="",
                    hours_saved_weekly=opp_data["hours_saved_weekly"],
                    employees_affected=opp_data["employees_affected"],
                    effort=opp_data["effort"],
                    impact=opp_data["impact"],
                ).category
                cat_labels = {
                    "quick_win": "🎯 Quick Win",
                    "big_swing": "🚀 Big Swing",
                    "nice_to_have": "✨ Nice-to-Have",
                    "deprioritize": "⏸️ Deprioritize",
                }
                st.info(cat_labels.get(cat, cat))
    
    # Add new opportunity
    st.markdown("---")
    st.markdown("### ➕ Add New Opportunity")
    
    with st.form("add_opportunity"):
        new_name = st.text_input("Opportunity Name")
        new_desc = st.text_area("Description (current problem)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_hours = st.number_input("Hours saved/week (per person)", min_value=0.5, max_value=40.0, value=5.0, step=0.5)
        with col2:
            new_employees = st.number_input("Employees affected", min_value=1, max_value=500, value=3)
        with col3:
            new_effort = st.selectbox("Effort", ["low", "medium", "high"])
        with col4:
            new_impact = st.selectbox("Impact", ["high", "medium", "low"])
        
        submitted = st.form_submit_button("Add Opportunity", use_container_width=True)
        if submitted and new_name:
            st.session_state.opportunities.append({
                "name": new_name,
                "description": new_desc,
                "hours_saved_weekly": new_hours,
                "employees_affected": new_employees,
                "effort": new_effort,
                "impact": new_impact,
            })
            st.rerun()

# ============================================================================
# TAB 3: INTERVIEW QUESTIONS
# ============================================================================

with tab3:
    st.markdown("## 📋 Interview Questions")
    st.markdown(f"Tailored for **{industry.replace('_', ' ').title()}** industry")
    
    role_filter = st.radio("Question Set", ["Both", "Stakeholder", "End-User"], horizontal=True)
    role_map = {"Both": "both", "Stakeholder": "stakeholder", "End-User": "enduser"}
    
    questions_md = generate_interview_doc(client, role_type=role_map[role_filter])
    st.markdown(questions_md)

# ============================================================================
# TAB 4: ROI ANALYSIS
# ============================================================================

with tab4:
    st.markdown("## 📈 ROI Analysis")
    
    combined = roi_data["combined"]
    
    # Summary table
    roi_table = {
        "Metric": [
            "Implementation Cost",
            "Hours Saved / Week",
            "Hourly Rate",
            "Weekly Savings",
            "Annual Cost Savings",
            "Annual Revenue Potential",
            "Total Annual Value",
            "Payback Period",
            "First Year ROI",
        ],
        "Value": [
            f"${combined['implementation_cost']:,.0f}",
            f"{combined['hours_saved_weekly']:.0f} hrs",
            f"${combined['hourly_rate']:.2f}",
            f"${combined['weekly_savings']:,.0f}",
            f"${combined['annual_savings']:,.0f}",
            f"${combined['annual_revenue_potential']:,.0f}",
            f"${combined['total_annual_value']:,.0f}",
            f"{combined['payback_months']:.1f} months",
            f"{combined['roi_percentage']:.0f}%",
        ],
    }
    st.table(roi_table)
    
    st.markdown("---")
    st.markdown("### ROI Calculation Method")
    st.code("""
1. Hours Saved/Week × Employees × 70% efficiency = Actual Hours Saved
2. Actual Hours × Hourly Rate = Weekly Savings
3. Weekly Savings × 52 = Annual Savings
4. 50% of Saved Hours × 2× Rate = Revenue Potential
5. (Annual Savings / Cost) × 100 = ROI %
    """)
    
    # By category breakdown
    if roi_data.get("by_category"):
        st.markdown("---")
        st.markdown("### By Category")
        for cat, cat_roi in roi_data["by_category"].items():
            cat_labels = {
                "quick_win": "🎯 Quick Wins",
                "big_swing": "🚀 Big Swings",
                "nice_to_have": "✨ Nice-to-Haves",
                "deprioritize": "⏸️ Deprioritize",
            }
            with st.expander(f"{cat_labels.get(cat, cat)} — ${cat_roi['annual_savings']:,.0f}/year"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Annual Savings", f"${cat_roi['annual_savings']:,.0f}")
                col2.metric("Hours/Week", f"{cat_roi['hours_saved_weekly']:.0f}")
                col3.metric("ROI", f"{cat_roi['roi_percentage']:.0f}%")

# ============================================================================
# TAB 5: DOWNLOADS
# ============================================================================

with tab5:
    st.markdown("## 📥 Download Deliverables")
    st.markdown("Generate and download client-ready documents.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Interview Questions")
        st.caption("Industry-specific discovery interview guide")
        questions_content = generate_interview_doc(client)
        st.download_button(
            "⬇️ Download Interview Questions (.md)",
            data=questions_content,
            file_name=f"{company_name.lower().replace(' ', '_')}_interview_questions.md",
            mime="text/markdown",
            use_container_width=True,
        )
        
        st.markdown("---")
        
        st.markdown("### 📊 Opportunity Matrix")
        st.caption("Categorized opportunity analysis")
        matrix_content = generate_opportunity_matrix(opportunities)
        st.download_button(
            "⬇️ Download Opportunity Matrix (.md)",
            data=matrix_content,
            file_name=f"{company_name.lower().replace(' ', '_')}_opportunity_matrix.md",
            mime="text/markdown",
            use_container_width=True,
        )
    
    with col2:
        st.markdown("### 📈 Executive Report")
        st.caption("Full audit report with ROI analysis")
        report_content = generate_executive_report(project, roi_data)
        st.download_button(
            "⬇️ Download Executive Report (.md)",
            data=report_content,
            file_name=f"{company_name.lower().replace(' ', '_')}_executive_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        
        st.markdown("---")
        
        st.markdown("### 🎨 Executive Presentation")
        st.caption("Branded PPTX with GVRN-AI styling")
        
        # Generate PPTX in memory
        pptx_buffer = io.BytesIO()
        tmp_path = Path("/tmp/temp_presentation.pptx")
        generate_executive_pptx(project, roi_data, tmp_path)
        with open(tmp_path, "rb") as f:
            pptx_bytes = f.read()
        
        st.download_button(
            "⬇️ Download Executive PPTX",
            data=pptx_bytes,
            file_name=f"{company_name.lower().replace(' ', '_')}_executive_presentation.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )
    
    st.markdown("---")
    
    # Project JSON
    st.markdown("### 💾 Project Data")
    st.caption("Save your audit project for later use")
    from dataclasses import asdict
    project_json = json.dumps(asdict(project), indent=2)
    st.download_button(
        "⬇️ Download Project JSON",
        data=project_json,
        file_name=f"{company_name.lower().replace(' ', '_')}_audit.json",
        mime="application/json",
        use_container_width=True,
    )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 13px;'>"
    "Built by <a href='https://gvrn-ai.com' style='color: #00C97B;'>GVRN-AI</a> "
    "| AI Audit & Automation Services | "
    "<a href='https://github.com/CloudAIX/ai-audit-toolkit' style='color: #00C97B;'>GitHub</a>"
    "</div>",
    unsafe_allow_html=True,
)
