"""
src/app.py
PitchPerfect Web Application - Built with Streamlit for ChiEAC Fellowship.
Week 2 / Gate 1: Ingestion, Header Mapping, Privacy Scrubber, and Validation.
"""

import os
import sys

# Ensure local module path is accessible
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import streamlit as st
import pandas as pd
from ingest import (
    load_file_to_df,
    scrub_pii_and_hash_clients,
    auto_map_headers,
    apply_header_mapping,
    validate_class_history,
    validate_survey_responses,
    validate_event_outcomes,
    CANONICAL_SCHEMAS
)
from evidence import (
    compute_all_evidence_cards,
    export_cards_to_json,
    export_cards_to_dataframe
)
from scorecard import (
    calculate_opportunity_scorecard,
    generate_radar_chart_figure,
    export_scorecard_to_excel
)
from pitchkit import (
    generate_pitch_kit,
    generate_all_pitch_kits,
    PitchKit
)
from export_docx import export_pitch_kit_to_docx
from outreach import generate_outreach_sequence
from bio_builder import generate_verified_bios
import zipfile
import io

# Page Configuration
st.set_page_config(
    page_title="PitchPerfect | ChiEAC",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for ChiEAC Fellowship theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #E0F2FE;
        color: #0369A1;
        margin-bottom: 8px;
    }
    .privacy-box {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        color: #166534;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.9rem;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "class_df" not in st.session_state:
    st.session_state["class_df"] = None
if "survey_df" not in st.session_state:
    st.session_state["survey_df"] = None
if "event_df" not in st.session_state:
    st.session_state["event_df"] = None
if "is_demo" not in st.session_state:
    st.session_state["is_demo"] = False
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

# Sidebar - Instructor Profile & Info
with st.sidebar:
    st.markdown("### 🧘 Instructor Profile")
    st.caption("Enter your details to personalize your proposals.")
    
    inst_name = st.text_input("Full Name", value="", placeholder="Enter your full name", key="sb_name")
    inst_disciplines = st.text_input("Disciplines", value="", placeholder="e.g. Vinyasa Yoga, Pilates, Breathwork", key="sb_disciplines")
    inst_years = st.number_input("Years Teaching", min_value=0, max_value=40, value=1, key="sb_years")
    inst_email = st.text_input("Email", value="", placeholder="e.g. you@example.com", key="sb_email")
    inst_phone = st.text_input("Phone", value="", placeholder="e.g. (312) 555-0123", key="sb_phone")
    inst_location = st.text_input("Location / City", value="", placeholder="e.g. Chicago, IL", key="sb_location")
    
    st.markdown("---")
    st.markdown("#### 🛡️ Credentials & Policies")
    inst_insurance = st.checkbox("Liability Insurance on File", value=False, key="sb_insurance")
    inst_bg_check = st.checkbox("Background Check on File (Youth Safe)", value=False, key="sb_bg_check")
    inst_sliding = st.checkbox("Offers Sliding Scale / Community Rate", value=False, key="sb_sliding")
    inst_languages = st.multiselect("Languages", ["English", "Spanish", "French", "American Sign Language", "Other"], default=["English"], key="sb_languages")
    
    st.markdown("---")
    st.caption("PitchPerfect v1.0")

# Centrally construct Instructor Profile from live sidebar inputs
instructor_profile = {
    "name": inst_name.strip() if (inst_name and inst_name.strip()) else "Your Name",
    "disciplines": inst_disciplines.strip() if (inst_disciplines and inst_disciplines.strip()) else "Movement & Mindfulness",
    "years_teaching": int(inst_years) if inst_years is not None else 1,
    "email": inst_email.strip() if (inst_email and inst_email.strip()) else "contact@pitchperfect.org",
    "phone": inst_phone.strip() if (inst_phone and inst_phone.strip()) else "(312) 555-0100",
    "location": inst_location.strip() if (inst_location and inst_location.strip()) else "Chicago, IL",
    "insurance": bool(inst_insurance),
    "background_check": bool(inst_bg_check),
    "sliding_scale": bool(inst_sliding),
    "languages": inst_languages or ["English"]
}
st.session_state["instructor_profile"] = instructor_profile

# App Header
st.markdown('<div class="main-header">PitchPerfect: Turn Teaching Data into Partnership Pitches</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Upload your class history, participant surveys, and event logs. PitchPerfect computes '
    'evidence-backed proof points and generates tailored pitch kits across seven opportunity types.'
    '</div>',
    unsafe_allow_html=True
)

# Demo Mode Quick Toggle
col_demo, col_reset = st.columns([4, 1])
with col_demo:
    if st.button("⚡ Test Drive with 18-Month Demo Data (529 Classes, 150 Surveys, 20 Events)", type="primary", use_container_width=True):
        demo_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
        c_path = os.path.join(demo_dir, "class_history.csv")
        s_path = os.path.join(demo_dir, "survey_responses.csv")
        e_path = os.path.join(demo_dir, "event_outcomes.csv")
        
        if os.path.exists(c_path) and os.path.exists(s_path) and os.path.exists(e_path):
            st.session_state["uploader_key"] += 1
            st.session_state["class_df"] = pd.read_csv(c_path)
            st.session_state["survey_df"] = pd.read_csv(s_path)
            st.session_state["event_df"] = pd.read_csv(e_path)
            st.session_state["is_demo"] = True
            st.rerun()
        else:
            st.error("Demo files not found. Run scripts/generate_demo_data.py first.")

with col_reset:
    if st.button("🔄 Clear Data", use_container_width=True):
        st.session_state["uploader_key"] += 1
        st.session_state["class_df"] = None
        st.session_state["survey_df"] = None
        st.session_state["event_df"] = None
        st.session_state["is_demo"] = False
        st.rerun()

st.markdown("---")

# Centrally compute Evidence Cards for all tabs whenever data is loaded
cards = []
if st.session_state["class_df"] is not None or st.session_state["survey_df"] is not None or st.session_state["event_df"] is not None:
    cards = compute_all_evidence_cards(
        st.session_state["class_df"],
        st.session_state["survey_df"],
        st.session_state["event_df"]
    )
st.session_state["cards"] = cards

# Privacy Notice
st.markdown(
    '<div class="privacy-box">'
    '🔒 <b>Privacy Guard Active:</b> All data is processed client-side in session memory. '
    'Student names and emails are automatically stripped upon ingest, and client IDs are hashed with SHA-256.'
    '</div>',
    unsafe_allow_html=True
)

# Upload Tabs
tab_upload, tab_summary, tab_evidence, tab_scorecard, tab_pitchkit, tab_preview = st.tabs([
    "📂 1. Ingest & Map Spreadsheets",
    "📊 2. Data Quality Summary",
    "📇 3. Evidence Cards (25 Metrics)",
    "🎯 4. Opportunity Scorecards & Gap Plan",
    "📑 5. Tailored Pitch Kits",
    "📋 6. Verified Bios & Data Preview"
])

with tab_upload:
    st.subheader("Upload Your Spreadsheets (CSV or XLSX)")
    st.caption("You can upload one, two, or all three files. Download template files if you need reference formats.")
    
    tmpl_dir = os.path.join(os.path.dirname(__file__), "..", "data", "templates")
    col1, col2, col3 = st.columns(3)
    ukey = st.session_state["uploader_key"]
    
    # ── File 1: Class History ──────────────────────────────────────────────
    with col1:
        st.markdown("#### 1. Class History")
        st.caption("Attendance, capacity, and scheduling logs.")
        uploaded_c = st.file_uploader("Upload class_history", type=["csv", "xlsx"], key=f"up_class_{ukey}")
        
        # Download template button
        c_tmpl_path = os.path.join(tmpl_dir, "class_history_template.csv")
        if os.path.exists(c_tmpl_path):
            with open(c_tmpl_path, "r", encoding="utf-8") as f:
                st.download_button("📥 Download Class Template (.csv)", f.read(), "class_history_template.csv", "text/csv", use_container_width=True)

        if uploaded_c is not None:
            raw_df = load_file_to_df(uploaded_c, uploaded_c.name)
            clean_df, dropped = scrub_pii_and_hash_clients(raw_df)
            mapping = auto_map_headers(clean_df, "class_history")
            mapped_df = apply_header_mapping(clean_df, mapping)
            val = validate_class_history(mapped_df)
            
            if val["valid"]:
                st.session_state["class_df"] = mapped_df
                st.session_state["is_demo"] = False
                st.success(f"✅ Valid: {val['row_count']} classes loaded.")
            else:
                st.error("Validation issues found:")
                for err in val["errors"]:
                    st.write(f"- {err}")
            
            if dropped:
                st.info(f"🛡️ Stripped PII columns: {', '.join(dropped)}")

        elif st.session_state["class_df"] is not None and st.session_state["is_demo"]:
            st.success(f"✅ Demo: {len(st.session_state['class_df'])} classes loaded.")

    # ── File 2: Survey Responses ────────────────────────────────────────────
    with col2:
        st.markdown("#### 2. Participant Surveys")
        st.caption("Post-class ratings, NPS, and stress scores.")
        uploaded_s = st.file_uploader("Upload survey_responses", type=["csv", "xlsx"], key=f"up_survey_{ukey}")
        
        # Download template button
        s_tmpl_path = os.path.join(tmpl_dir, "survey_responses_template.csv")
        if os.path.exists(s_tmpl_path):
            with open(s_tmpl_path, "r", encoding="utf-8") as f:
                st.download_button("📥 Download Survey Template (.csv)", f.read(), "survey_responses_template.csv", "text/csv", use_container_width=True)

        if uploaded_s is not None:
            raw_df = load_file_to_df(uploaded_s, uploaded_s.name)
            clean_df, dropped = scrub_pii_and_hash_clients(raw_df)
            mapping = auto_map_headers(clean_df, "survey_responses")
            mapped_df = apply_header_mapping(clean_df, mapping)
            val = validate_survey_responses(mapped_df)
            
            if val["valid"]:
                st.session_state["survey_df"] = mapped_df
                st.session_state["is_demo"] = False
                st.success(f"✅ Valid: {val['row_count']} surveys loaded.")
            else:
                st.error("Validation issues found:")
                for err in val["errors"]:
                    st.write(f"- {err}")
            
            if dropped:
                st.info(f"🛡️ Stripped PII columns: {', '.join(dropped)}")

        elif st.session_state["survey_df"] is not None and st.session_state["is_demo"]:
            st.success(f"✅ Demo: {len(st.session_state['survey_df'])} surveys loaded.")

    # ── File 3: Event Outcomes ──────────────────────────────────────────────
    with col3:
        st.markdown("#### 3. Event Outcomes")
        st.caption("Pop-ups, festivals, workshops, and retreats.")
        uploaded_e = st.file_uploader("Upload event_outcomes", type=["csv", "xlsx"], key=f"up_event_{ukey}")
        
        # Download template button
        e_tmpl_path = os.path.join(tmpl_dir, "event_outcomes_template.csv")
        if os.path.exists(e_tmpl_path):
            with open(e_tmpl_path, "r", encoding="utf-8") as f:
                st.download_button("📥 Download Event Template (.csv)", f.read(), "event_outcomes_template.csv", "text/csv", use_container_width=True)

        if uploaded_e is not None:
            raw_df = load_file_to_df(uploaded_e, uploaded_e.name)
            clean_df, dropped = scrub_pii_and_hash_clients(raw_df)
            mapping = auto_map_headers(clean_df, "event_outcomes")
            mapped_df = apply_header_mapping(clean_df, mapping)
            val = validate_event_outcomes(mapped_df)
            
            if val["valid"]:
                st.session_state["event_df"] = mapped_df
                st.session_state["is_demo"] = False
                st.success(f"✅ Valid: {val['row_count']} events loaded.")
            else:
                st.error("Validation issues found:")
                for err in val["errors"]:
                    st.write(f"- {err}")
            
            if dropped:
                st.info(f"🛡️ Stripped PII columns: {', '.join(dropped)}")

        elif st.session_state["event_df"] is not None and st.session_state["is_demo"]:
            st.success(f"✅ Demo: {len(st.session_state['event_df'])} events loaded.")

with tab_summary:
    st.subheader("Data Quality & Coverage Summary")
    
    if st.session_state["class_df"] is None and st.session_state["survey_df"] is None and st.session_state["event_df"] is None:
        st.info("No data loaded yet. Upload your files or click 'Test Drive with Demo Data' above.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        
        # Metric 1: Total Classes
        c_df = st.session_state["class_df"]
        with m1:
            if c_df is not None:
                st.metric("Total Classes Analyzed", len(c_df), f"{c_df['class_type'].nunique()} disciplines")
            else:
                st.metric("Total Classes", "0", "Not uploaded")
                
        # Metric 2: Average Fill Rate
        with m2:
            if c_df is not None and "capacity" in c_df.columns and "attended" in c_df.columns:
                fill_rate = round(float((c_df["attended"] / c_df["capacity"]).mean() * 100), 1)
                st.metric("Average Fill Rate", f"{fill_rate}%", "Room utilization")
            else:
                st.metric("Fill Rate", "N/A", "Awaiting class logs")

        # Metric 3: Survey Ratings
        s_df = st.session_state["survey_df"]
        with m3:
            if s_df is not None and "overall_rating" in s_df.columns:
                avg_star = round(float(s_df["overall_rating"].mean()), 2)
                st.metric("Average Student Rating", f"{avg_star} / 5.0", f"{len(s_df)} verified reviews")
            else:
                st.metric("Student Rating", "N/A", "Awaiting survey logs")

        # Metric 4: Event Reach
        e_df = st.session_state["event_df"]
        with m4:
            if e_df is not None and "actual_attendance" in e_df.columns:
                total_event_reach = int(e_df["actual_attendance"].sum())
                st.metric("Total Event Reach", f"{total_event_reach} attendees", f"{len(e_df)} events delivered")
            else:
                st.metric("Event Reach", "N/A", "Awaiting event logs")

        st.markdown("---")
        st.markdown("#### ⏱️ Timeline Coverage & Active Venues")
        if c_df is not None and "class_date" in c_df.columns:
            st.write(f"📅 **Date Span:** {c_df['class_date'].min()} to {c_df['class_date'].max()}")
with tab_evidence:
    st.subheader("Verified Evidence Cards (25 Metrics across 6 Families)")
    st.caption("Each Evidence Card represents an authentic proof point backed by your uploaded spreadsheets.")

    if st.session_state["class_df"] is None and st.session_state["survey_df"] is None and st.session_state["event_df"] is None:
        st.info("No data loaded yet. Upload spreadsheets in Tab 1 or click 'Test Drive with Demo Data' above.")
    else:
        cards = compute_all_evidence_cards(
            st.session_state["class_df"],
            st.session_state["survey_df"],
            st.session_state["event_df"]
        )

        # Export Controls & Family Filter
        col_fil, col_exp_json, col_exp_xlsx = st.columns([3, 1, 1])
        families = ["All Families"] + sorted(list(set(c.family for c in cards)))
        with col_fil:
            selected_fam = st.selectbox("Filter by Metric Family", families)

        filtered_cards = [c for c in cards if selected_fam == "All Families" or c.family == selected_fam]

        with col_exp_json:
            json_data = export_cards_to_json(cards)
            st.download_button(
                "📥 Export JSON",
                json_data,
                "evidence_cards.json",
                "application/json",
                use_container_width=True
            )

        with col_exp_xlsx:
            df_cards = export_cards_to_dataframe(cards)
            import io
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
                df_cards.to_excel(writer, index=False, sheet_name="EvidenceCards")
            st.download_button(
                "📥 Export Excel (.xlsx)",
                xlsx_buffer.getvalue(),
                "evidence_cards.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        st.markdown(f"**Showing {len(filtered_cards)} Verified Evidence Cards**")
        
        # Grid layout (3 cards per row)
        cols_per_row = 3
        for i in range(0, len(filtered_cards), cols_per_row):
            row_cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(filtered_cards):
                    card = filtered_cards[i + j]
                    with row_cols[j]:
                        st.markdown(f"""
                        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin-bottom:14px; min-height:190px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <span style="font-size:0.75rem; font-weight:700; color:#0369A1; background:#E0F2FE; padding:2px 8px; border-radius:6px;">{card.family}</span>
                                <span style="font-size:0.75rem; color:#64748B;">{card.source_file}</span>
                            </div>
                            <div style="font-size:0.9rem; font-weight:600; color:#334155; margin-bottom:4px;">{card.label}</div>
                            <div style="font-size:1.8rem; font-weight:800; color:#0F172A; margin-bottom:8px;">{card.formatted_value}</div>
                            <div style="font-size:0.75rem; color:#64748B; margin-bottom:4px;">📅 {card.date_range} • 👥 Sample: {card.sample_size}</div>
                            <div style="font-size:0.75rem; color:#475569; font-style:italic; border-top:1px dashed #CBD5E1; padding-top:6px; margin-top:6px;">ℹ️ {card.method_note}</div>
                        </div>
                        """, unsafe_allow_html=True)

with tab_scorecard:
    st.subheader("🎯 Opportunity Scorecards & Actionable Gap Plans")
    st.caption("Evaluates your verified Evidence Cards against 7 target buyer decision models to calculate 0–100 readiness scores.")

    if st.session_state["class_df"] is None and st.session_state["survey_df"] is None and st.session_state["event_df"] is None:
        st.info("No data loaded yet. Upload your spreadsheets in Tab 1 or click 'Test Drive with Demo Data' above.")
    else:
        cards = compute_all_evidence_cards(
            st.session_state["class_df"],
            st.session_state["survey_df"],
            st.session_state["event_df"]
        )

        # Ground credentials and experience in actual data & sidebar checkboxes
        c_df = st.session_state["class_df"]
        e_df = st.session_state["event_df"]

        # Check for youth experience in class titles or event types
        has_youth = False
        if c_df is not None and "class_type" in c_df.columns:
            has_youth = bool(c_df["class_type"].astype(str).str.contains(r"youth|teen|kid|student|school", case=False).any())
        if not has_youth and e_df is not None and "event_type" in e_df.columns:
            has_youth = bool(e_df["event_type"].astype(str).str.contains(r"youth|teen|kid|school", case=False).any())

        # Check for community park venues
        has_community_venue = False
        if c_df is not None and "venue_name" in c_df.columns:
            has_community_venue = bool(c_df["venue_name"].astype(str).str.contains(r"park|library|community|center", case=False).any())

        # Check for outdoor event track record
        has_outdoor = False
        if e_df is not None and "event_type" in e_df.columns:
            has_outdoor = bool(e_df["event_type"].astype(str).str.contains(r"outdoor|park|festival", case=False).any())

        policy_overrides = {
            "liability_insurance_on_file": bool(inst_insurance),
            "background_check_on_file": bool(inst_bg_check),
            "sliding_scale_policy": bool(inst_sliding),
            "language_matches": bool(len(inst_languages) > 1),
            "professional_certifications": bool(inst_years >= 1),
            "clear_rate_card_on_file": True,
            "park_community_venue_history": has_community_venue,
            "youth_segment_experience": has_youth,
            "outdoor_event_track_record": has_outdoor,
            "private_event_experience": bool(e_df is not None and len(e_df) >= 2),
        }

        scorecard_res = calculate_opportunity_scorecard(
            cards,
            policy_overrides=policy_overrides
        )

        # Overview Section: Radar Footprint + Ranked Cards
        col_radar, col_rank = st.columns([1.2, 1.1])

        with col_radar:
            st.markdown("#### 📡 7-Opportunity Readiness Footprint")
            st.caption("Hover over any dimension to inspect your verified match against buyer priorities.")
            fig = generate_radar_chart_figure(scorecard_res)
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": "hover",
                    "displaylogo": False,
                    "modeBarButtonsToRemove": [
                        "zoom2d", "pan2d", "select2d", "lasso2d",
                        "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"
                    ],
                    "toImageButtonOptions": {
                        "format": "png",
                        "filename": "pitchperfect_opportunity_radar",
                        "height": 700,
                        "width": 900,
                        "scale": 2
                    },
                    "responsive": True
                }
            )

        with col_rank:
            st.markdown("#### 🏆 Ranked Opportunity Leaderboard")
            top_opp = scorecard_res.opportunity_scores[scorecard_res.top_opportunity_id]
            st.success(f"**#1 Recommendation: {top_opp.opportunity_name}**\n\nReadiness: **{top_opp.total_score} / 100** • {top_opp.tier}")

            for rank_idx, opp_id in enumerate(scorecard_res.ranked_opportunities, 1):
                opp = scorecard_res.opportunity_scores[opp_id]
                badge_bg = "#DCFCE7" if "Pitch-Ready" in opp.tier else ("#FEF3C7" if "Strong" in opp.tier else "#FEE2E2")
                badge_fg = "#15803D" if "Pitch-Ready" in opp.tier else ("#B45309" if "Strong" in opp.tier else "#B91C1C")
                bar_color = "#16A34A" if "Pitch-Ready" in opp.tier else ("#D97706" if "Strong" in opp.tier else "#DC2626")
                
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:10px 14px; margin-bottom:8px; box-shadow:0 1px 2px rgba(0,0,0,0.03);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:700; color:#1E293B; font-size:0.95rem;">#{rank_idx} {opp.opportunity_name}</span>
                            <span style="font-size:0.75rem; color:#64748B; margin-left:6px;">• {opp.buyer}</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-weight:800; font-size:1.05rem; color:{opp.tier_color};">{opp.total_score}</span><span style="font-size:0.75rem; color:#64748B;">/100</span>
                            <span style="font-size:0.7rem; font-weight:700; background:{badge_bg}; color:{badge_fg}; padding:2px 7px; border-radius:999px; margin-left:6px;">{opp.tier.split(' ')[0]}</span>
                        </div>
                    </div>
                    <div style="background:#F1F5F9; border-radius:999px; height:6px; overflow:hidden; margin-top:6px;">
                        <div style="background:{bar_color}; width:{min(opp.total_score, 100.0)}%; height:6px; border-radius:999px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔍 Opportunity Drill-Down & Gap Analysis")

        selected_opp_id = st.selectbox(
            "Select an Opportunity to Inspect Buyer Priorities & Gap Closure Plan:",
            scorecard_res.ranked_opportunities,
            format_func=lambda x: f"{scorecard_res.opportunity_scores[x].opportunity_name} (Score: {scorecard_res.opportunity_scores[x].total_score}/100 — {scorecard_res.opportunity_scores[x].tier})"
        )

        sel_opp = scorecard_res.opportunity_scores[selected_opp_id]

        # Buyer info banner
        st.markdown(f"""
        <div style="background:#EFF6FF; border-left:4px solid #2563EB; padding:12px 16px; border-radius:6px; margin-bottom:16px;">
            <div style="font-weight:700; color:#1E40AF; font-size:0.95rem;">🎯 Target Buyer: {sel_opp.buyer}</div>
            <div style="color:#1E3A8A; font-size:0.85rem; margin-top:2px;"><b>Buyer Priority:</b> {sel_opp.buyer_priority}</div>
            <div style="color:#3B82F6; font-size:0.8rem; margin-top:4px;"><i><b>Pitch Narrative:</b> {sel_opp.narrative_focus}</i></div>
        </div>
        """, unsafe_allow_html=True)

        col_left_break, col_right_gap = st.columns([1.2, 1.0])

        with col_left_break:
            st.markdown("#### 📊 Evidence Weight Breakdown")
            breakdown_data = []
            for b in sel_opp.breakdown:
                status_icon = "🟢" if b.status == "Strong" else ("🟡" if b.status == "Moderate" else "🔴")
                breakdown_data.append({
                    "Priority / Metric": b.label,
                    "Max Weight": f"{int(b.max_score)} pts",
                    "Score Earned": f"{b.score_earned} pts",
                    "Status": f"{status_icon} {b.status}",
                    "Your Value": b.current_value
                })
            st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

        with col_right_gap:
            st.markdown("#### 🛠️ Actionable Gap Closure Plan")
            if sel_opp.total_score >= 85.0:
                st.success("🎉 **Pitch-Ready Status!**\n\nYour verified evidence dossier meets and exceeds all buyer benchmarks for this opportunity. You are ready to generate your pitch proposal!")
            
            if sel_opp.gaps:
                st.markdown("**Steps to unlock a higher score:**")
                for gap_step in sel_opp.gaps:
                    st.markdown(f"- 📌 {gap_step}")
            else:
                st.info("No critical data gaps detected. All primary proof requirements are verified.")

            # Download Reports (Excel and JSON side by side)
            col_d_xlsx, col_d_json = st.columns(2)
            with col_d_xlsx:
                xlsx_bytes = export_scorecard_to_excel(scorecard_res, sel_opp.opportunity_id)
                st.download_button(
                    label="📊 Download Excel (.xlsx)",
                    data=xlsx_bytes,
                    file_name=f"scorecard_{sel_opp.opportunity_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with col_d_json:
                st.download_button(
                    label="📥 Export JSON",
                    data=sel_opp.model_dump_json(indent=2),
                    file_name=f"scorecard_{sel_opp.opportunity_id}.json",
                    mime="application/json",
                    use_container_width=True
                )

with tab_pitchkit:
    st.subheader("📑 Tailored Partnership Pitch Kits & DOCX Exporter")
    st.caption("Generate publication-ready 1-2 page proposals tailored to each decision-maker, backed by your verified Evidence Cards.")

    if st.session_state["class_df"] is None and st.session_state["survey_df"] is None and st.session_state["event_df"] is None:
        st.info("No data loaded yet. Upload your spreadsheets in Tab 1 or click '⚡ Test Drive with Demo Data' above.")
    else:
        cards = compute_all_evidence_cards(
            st.session_state["class_df"],
            st.session_state["survey_df"],
            st.session_state["event_df"]
        )

        # Ground credentials and experience in actual data & sidebar checkboxes
        c_df = st.session_state["class_df"]
        e_df = st.session_state["event_df"]

        has_youth = False
        if c_df is not None and "class_type" in c_df.columns:
            has_youth = bool(c_df["class_type"].astype(str).str.contains(r"youth|teen|kid|student|school", case=False).any())
        if not has_youth and e_df is not None and "event_type" in e_df.columns:
            has_youth = bool(e_df["event_type"].astype(str).str.contains(r"youth|teen|kid|school", case=False).any())

        has_community_venue = False
        if c_df is not None and "venue_name" in c_df.columns:
            has_community_venue = bool(c_df["venue_name"].astype(str).str.contains(r"park|library|community|center", case=False).any())

        has_outdoor = False
        if e_df is not None and "event_type" in e_df.columns:
            has_outdoor = bool(e_df["event_type"].astype(str).str.contains(r"outdoor|park|festival", case=False).any())

        policy_overrides = {
            "liability_insurance_on_file": bool(inst_insurance),
            "background_check_on_file": bool(inst_bg_check),
            "sliding_scale_policy": bool(inst_sliding),
            "language_matches": bool(len(inst_languages) > 1),
            "professional_certifications": bool(inst_years >= 1),
            "clear_rate_card_on_file": True,
            "park_community_venue_history": has_community_venue,
            "youth_segment_experience": has_youth,
            "outdoor_event_track_record": has_outdoor,
            "private_event_experience": bool(e_df is not None and len(e_df) >= 2),
        }

        scorecard_res = calculate_opportunity_scorecard(cards, policy_overrides=policy_overrides)

        instructor_profile = {
            "name": inst_name.strip() if (inst_name and inst_name.strip()) else "Your Name",
            "disciplines": inst_disciplines.strip() if (inst_disciplines and inst_disciplines.strip()) else "Movement & Mindfulness",
            "years_teaching": int(inst_years) if inst_years is not None else 1,
            "email": inst_email.strip() if (inst_email and inst_email.strip()) else "contact@pitchperfect.org",
            "phone": inst_phone.strip() if (inst_phone and inst_phone.strip()) else "(312) 555-0100",
            "location": inst_location.strip() if (inst_location and inst_location.strip()) else "Chicago, IL",
            "insurance": bool(inst_insurance),
            "background_check": bool(inst_bg_check),
            "sliding_scale": bool(inst_sliding),
            "languages": inst_languages or ["English"]
        }

        # Opportunity Selection Controls & Batch Export Bar
        col_sel, col_zip = st.columns([2.5, 1.2])

        with col_sel:
            selected_opp_id = st.selectbox(
                "Select Opportunity Pitch Proposal to Generate:",
                scorecard_res.ranked_opportunities,
                index=0,
                format_func=lambda x: f"{scorecard_res.opportunity_scores[x].opportunity_name} (Score: {scorecard_res.opportunity_scores[x].total_score}/100 — {scorecard_res.opportunity_scores[x].tier.split(' ')[0]})"
            )

        with col_zip:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            # Pre-generate in-memory zip of all 7 pitch kits with effective profile
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                all_kits = generate_all_pitch_kits(cards, scorecard=scorecard_res, instructor_profile=instructor_profile)
                for opp_k, k in all_kits.items():
                    d_bytes = export_pitch_kit_to_docx(k)
                    zf.writestr(f"PitchKit_{opp_k}.docx", d_bytes)
                    zf.writestr(f"PitchKit_{opp_k}.txt", k.rendered_text)
            st.download_button(
                "📦 Download All 7 Kits (.zip)",
                data=zip_buffer.getvalue(),
                file_name="PitchPerfect_All_7_Pitch_Kits.zip",
                mime="application/zip",
                use_container_width=True
            )

        # Generate selected kit
        pitch_kit = generate_pitch_kit(
            selected_opp_id,
            cards,
            scorecard=scorecard_res,
            instructor_profile=instructor_profile
        )

        # Header status banner
        badge_bg = "#DCFCE7" if "Pitch-Ready" in pitch_kit.tier else ("#FEF3C7" if "Strong" in pitch_kit.tier else "#FEE2E2")
        badge_fg = "#15803D" if "Pitch-Ready" in pitch_kit.tier else ("#B45309" if "Strong" in pitch_kit.tier else "#B91C1C")

        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px 20px; margin-bottom:18px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-size:1.3rem; font-weight:800; color:#1E293B;">{pitch_kit.pitch_title}</div>
                    <div style="font-size:0.9rem; color:#475569; margin-top:2px;">
                        <b>Target Decision Maker:</b> {pitch_kit.buyer} • <b>Prepared By:</b> {pitch_kit.instructor_name}
                    </div>
                    <div style="font-size:0.85rem; color:#0369A1; margin-top:4px;">
                        <i><b>Core Priority:</b> {pitch_kit.buyer_priority}</i>
                    </div>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:1.5rem; font-weight:800; color:{pitch_kit.tier_color};">{pitch_kit.total_score}</span><span style="font-size:0.9rem; color:#64748B;">/100</span><br>
                    <span style="font-size:0.75rem; font-weight:700; background:{badge_bg}; color:{badge_fg}; padding:3px 10px; border-radius:999px;">{pitch_kit.tier}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if pitch_kit.total_score >= 85.0:
            st.success("🎉 **Pitch-Ready Proposal!** Your verified evidence dossier meets and exceeds all buyer benchmarks. This proposal is ready to deliver.")
        else:
            st.warning("⚠️ **Evidence Bridge Incorporated:** Readiness score is currently below 85. PitchPerfect has automatically tailored a structured pilot and quality assurance bridge into this proposal.")

        # Sub-tabs: Formal Proposal Document vs. 3-Touch Cold Email Outreach
        subtab_proposal, subtab_outreach = st.tabs(["📄 1-Page Word Proposal", "📧 3-Touch Cold Outreach Emails"])

        with subtab_proposal:
            # Action Buttons (DOCX and TXT download side-by-side)
            col_docx, col_txt, col_space = st.columns([1.5, 1.5, 2.5])
            with col_docx:
                docx_data = export_pitch_kit_to_docx(pitch_kit)
                st.download_button(
                    "📄 Download Word Doc (.docx)",
                    data=docx_data,
                    file_name=f"PitchKit_{selected_opp_id}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True
                )
            with col_txt:
                st.download_button(
                    "📝 Download Text (.txt)",
                    data=pitch_kit.rendered_text,
                    file_name=f"PitchKit_{selected_opp_id}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            st.markdown("---")

            # Layout: Left column for Document Preview, Right column for Top Evidence Highlights
            col_preview, col_ev_side = st.columns([1.5, 1.0])

            with col_preview:
                st.markdown("#### 📄 Document Preview")
                with st.container(border=True):
                    st.markdown(pitch_kit.rendered_text)

            with col_ev_side:
                st.markdown("#### 📇 Top Evidence Dossier Included")
                st.caption("Proof points automatically woven into this buyer-tailored pitch proposal:")
                for ev in pitch_kit.top_evidence:
                    st.markdown(f"""
                    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:12px; margin-bottom:10px;">
                        <div style="font-size:0.75rem; font-weight:700; color:#0369A1; text-transform:uppercase;">{ev.get('source_file', 'Verified Log')}</div>
                        <div style="font-size:0.85rem; font-weight:600; color:#334155; margin-top:2px;">{ev.get('label', '')}</div>
                        <div style="font-size:1.3rem; font-weight:800; color:#0F172A; margin:4px 0;">{ev.get('formatted_value', '')}</div>
                        <div style="font-size:0.75rem; color:#64748B;">📅 {ev.get('date_range', 'N/A')} • 👥 Sample: {ev.get('sample_size', 'N/A')}</div>
                        <div style="font-size:0.72rem; color:#475569; font-style:italic; border-top:1px dashed #CBD5E1; padding-top:4px; margin-top:4px;">ℹ️ {ev.get('method_note', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                if pitch_kit.gap_closure_note:
                    st.markdown("#### 🛠️ Evidence Bridge Status")
                    st.info(f"Because current score is **{pitch_kit.total_score}/100**, the pitch includes a 30-day pilot bridge addressing: {', '.join(pitch_kit.scorecard_summary.get('gaps', ['baseline tracking'])[:2])}.")

        with subtab_outreach:
            outreach_seq = generate_outreach_sequence(
                selected_opp_id,
                cards,
                scorecard=scorecard_res,
                instructor_profile=instructor_profile
            )

            st.markdown(f"#### 🎯 Cold Outreach Campaign: {pitch_kit.opportunity_name}")
            st.markdown(f"**Target Decision Maker:** `{outreach_seq.target_buyer}`")
            st.caption("A structured 3-step sequence engineered for high response rates. Copy and paste directly into Gmail, Outlook, or LinkedIn.")

            for touch in outreach_seq.touches:
                with st.expander(f"✉️ {touch.title} ({touch.timing})", expanded=(touch.touch_number == 1)):
                    st.markdown(f"**Subject:** `{touch.subject}`")
                    st.caption(f"💡 **Evidence Highlighted:** {touch.proof_point_highlighted}")
                    touch_hash = abs(hash(f"{touch.subject}_{touch.body}"))
                    st.text_area(
                        label=f"Email Body - Touch {touch.touch_number}",
                        value=touch.body,
                        height=220,
                        key=f"outreach_body_{selected_opp_id}_{touch.touch_number}_{touch_hash}",
                        label_visibility="collapsed"
                    )

            # Combined outreach text download
            all_emails_text = f"=== 3-TOUCH COLD OUTREACH: {pitch_kit.opportunity_name.upper()} ===\nTarget Buyer: {outreach_seq.target_buyer}\n\n"
            for t in outreach_seq.touches:
                all_emails_text += f"--- {t.title} ({t.timing}) ---\nSubject: {t.subject}\n\n{t.body}\n\n"
            
            st.download_button(
                "📥 Download Outreach Emails (.txt)",
                data=all_emails_text,
                file_name=f"Outreach_Emails_{selected_opp_id}.txt",
                mime="text/plain"
            )

with tab_preview:
    col_btitle, col_bpersp = st.columns([2.2, 1.8])
    with col_btitle:
        st.subheader("Verified Bios & Grant Application Copy")
        st.caption("Evidence-grounded professional bios and impact statements automatically generated from your verified data cards.")
    with col_bpersp:
        bio_perspective_sel = st.radio(
            "Voice & Perspective:",
            ["Third-Person (Studios, Festivals & Grants)", "First-Person (Website & Socials)"],
            index=0,
            horizontal=True,
            key="sb_bio_persp"
        )
        persp_mode = "first_person" if "First-Person" in bio_perspective_sel else "third_person"

    if cards:
        bio_set = generate_verified_bios(cards, instructor_profile=instructor_profile, perspective=persp_mode)

        short_hash = abs(hash(bio_set.short_bio))
        med_hash = abs(hash(bio_set.medium_bio))
        grant_hash = abs(hash(bio_set.grant_statement))

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown(f"##### 🏷️ Short Bio ({bio_set.word_counts['short_bio']} words)")
            st.caption("For studio schedule bios, Instagram, and event flyers:")
            st.text_area("Short Bio", value=bio_set.short_bio, height=120, key=f"bio_short_{short_hash}", label_visibility="collapsed")

        with col_b2:
            st.markdown(f"##### 💼 Medium Bio ({bio_set.word_counts['medium_bio']} words)")
            st.caption("For corporate proposals, conference speaker notes, and festival lineups:")
            st.text_area("Medium Bio", value=bio_set.medium_bio, height=120, key=f"bio_medium_{med_hash}", label_visibility="collapsed")

        st.markdown(f"##### 🏛️ Grant & Fellowship Impact Statement ({bio_set.word_counts['grant_statement']} words)")
        st.caption("For ChiEAC fellowship portfolios, community health grants, and foundation proposals:")
        st.text_area("Grant Statement", value=bio_set.grant_statement, height=220, key=f"bio_grant_{grant_hash}", label_visibility="collapsed")

        all_bios_text = (
            f"=== VERIFIED INSTRUCTOR BIOS: {bio_set.instructor_name} ===\n\n"
            f"--- SHORT BIO ({bio_set.word_counts['short_bio']} words) ---\n"
            f"{bio_set.short_bio}\n\n"
            f"--- MEDIUM BIO ({bio_set.word_counts['medium_bio']} words) ---\n"
            f"{bio_set.medium_bio}\n\n"
            f"--- GRANT & FELLOWSHIP STATEMENT ({bio_set.word_counts['grant_statement']} words) ---\n"
            f"{bio_set.grant_statement}\n"
        )
        st.download_button(
            "📋 Download All Verified Bios (.txt)",
            data=all_bios_text,
            file_name=f"Verified_Bios_{bio_set.instructor_name.replace(' ', '_')}.txt",
            mime="text/plain"
        )
    else:
        st.info("Upload your spreadsheets or click 'Test Drive with Demo Data' to generate verified bios.")

    st.markdown("---")
    st.subheader("Verified Data Preview (PII-Scrubbed)")
    if st.session_state["class_df"] is not None:
        st.markdown("##### 🧘 Class History Sample (First 10 Rows)")
        st.dataframe(st.session_state["class_df"].head(10), use_container_width=True)
    if st.session_state["survey_df"] is not None:
        st.markdown("##### ⭐ Participant Survey Sample (First 10 Rows)")
        st.dataframe(st.session_state["survey_df"].head(10), use_container_width=True)
    if st.session_state["event_df"] is not None:
        st.markdown("##### 🏆 Event Outcomes Sample (First 10 Rows)")
        st.dataframe(st.session_state["event_df"].head(10), use_container_width=True)

# Footer
st.markdown("---")
st.caption("🔒 **Privacy Guarantee:** Your uploaded spreadsheets are processed securely in temporary session memory and are never saved, stored, or shared.")
