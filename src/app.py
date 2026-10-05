"""
src/app.py
PitchPerfect Web Application - Built with Streamlit for ChiEAC Fellowship.
Week 2 / Gate 1: Ingestion, Header Mapping, Privacy Scrubber, and Validation.
"""

import os
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

# Sidebar - Instructor Profile & Info
with st.sidebar:
    st.markdown("### 🧘 Instructor Profile")
    st.caption("Enter your details to personalize your proposals.")
    
    inst_name = st.text_input("Full Name", value="", placeholder="Enter your full name")
    inst_disciplines = st.text_input("Disciplines", value="", placeholder="e.g. Vinyasa Yoga, Pilates, Breathwork")
    inst_years = st.number_input("Years Teaching", min_value=0, max_value=40, value=1)
    
    st.markdown("---")
    st.markdown("#### 🛡️ Credentials & Policies")
    inst_insurance = st.checkbox("Liability Insurance on File", value=False)
    inst_bg_check = st.checkbox("Background Check on File (Youth Safe)", value=False)
    inst_sliding = st.checkbox("Offers Sliding Scale / Community Rate", value=False)
    inst_languages = st.multiselect("Languages", ["English", "Spanish", "French", "American Sign Language", "Other"], default=["English"])
    
    st.markdown("---")
    st.caption("PitchPerfect v1.0")

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
            st.session_state["class_df"] = pd.read_csv(c_path)
            st.session_state["survey_df"] = pd.read_csv(s_path)
            st.session_state["event_df"] = pd.read_csv(e_path)
            st.session_state["is_demo"] = True
            st.success("Loaded 18-month demo dataset successfully!")
        else:
            st.error("Demo files not found. Run scripts/generate_demo_data.py first.")

with col_reset:
    if st.button("🔄 Clear Data", use_container_width=True):
        st.session_state["class_df"] = None
        st.session_state["survey_df"] = None
        st.session_state["event_df"] = None
        st.session_state["is_demo"] = False
        st.rerun()

st.markdown("---")

# Privacy Notice
st.markdown(
    '<div class="privacy-box">'
    '🔒 <b>Privacy Guard Active:</b> All data is processed client-side in session memory. '
    'Student names and emails are automatically stripped upon ingest, and client IDs are hashed with SHA-256.'
    '</div>',
    unsafe_allow_html=True
)

# Upload Tabs
tab_upload, tab_summary, tab_preview = st.tabs(["📂 1. Ingest & Map Spreadsheets", "📊 2. Data Quality Summary", "👀 3. Verified Data Preview"])

with tab_upload:
    st.subheader("Upload Your Spreadsheets (CSV or XLSX)")
    st.caption("You can upload one, two, or all three files. Download template files if you need reference formats.")
    
    tmpl_dir = os.path.join(os.path.dirname(__file__), "..", "data", "templates")
    col1, col2, col3 = st.columns(3)
    
    # ── File 1: Class History ──────────────────────────────────────────────
    with col1:
        st.markdown("#### 1. Class History")
        st.caption("Attendance, capacity, and scheduling logs.")
        uploaded_c = st.file_uploader("Upload class_history", type=["csv", "xlsx"], key="up_class")
        
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
        uploaded_s = st.file_uploader("Upload survey_responses", type=["csv", "xlsx"], key="up_survey")
        
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
        uploaded_e = st.file_uploader("Upload event_outcomes", type=["csv", "xlsx"], key="up_event")
        
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
            if "venue_name" in c_df.columns:
                venues = c_df["venue_name"].dropna().unique().tolist()
                st.write(f"📍 **Documented Venues:** {', '.join(venues)}")

with tab_preview:
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
st.caption("PitchPerfect | Chicago Education Advocacy Cooperative (ChiEAC) Fellowship | Zero data persistence guarantee.")
