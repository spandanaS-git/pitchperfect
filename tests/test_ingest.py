"""
tests/test_ingest.py
Unit tests for PitchPerfect ingestion, header mapping, PII scrubbing, and validation.
Run with: pytest tests/
"""

import os
import sys
import pandas as pd
import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ingest import (
    scrub_pii_and_hash_clients,
    auto_map_headers,
    apply_header_mapping,
    validate_class_history,
    validate_survey_responses,
    validate_event_outcomes
)

def test_pii_scrubbing_and_client_hashing():
    raw_data = {
        "student_name": ["Alice Smith", "Bob Jones"],
        "email": ["alice@example.com", "bob@example.com"],
        "client_id": ["user_123", "user_456"],
        "class_type": ["Vinyasa", "Yin"],
        "attended": [15, 20]
    }
    df = pd.DataFrame(raw_data)
    clean_df, dropped = scrub_pii_and_hash_clients(df)

    # Student name and email must be dropped
    assert "student_name" not in clean_df.columns
    assert "email" not in clean_df.columns
    assert "student_name" in dropped
    assert "email" in dropped

    # client_id must be hashed with usr_ prefix, not raw string
    assert clean_df["client_id"].iloc[0].startswith("usr_")
    assert clean_df["client_id"].iloc[0] != "user_123"

def test_mindbody_header_mapping():
    # Mindbody export style headers
    mb_data = {
        "Session Date": ["2026-05-01"],
        "Start Time": ["18:00"],
        "Service": ["Vinyasa Flow"],
        "Limit": [25],
        "Total Students": [22],
        "Price ($)": [20.00]
    }
    df = pd.DataFrame(mb_data)
    mapping = auto_map_headers(df, "class_history")
    mapped_df = apply_header_mapping(df, mapping)

    assert "class_date" in mapped_df.columns
    assert "class_time" in mapped_df.columns
    assert "class_type" in mapped_df.columns
    assert "capacity" in mapped_df.columns
    assert "attended" in mapped_df.columns
    assert "price" in mapped_df.columns

def test_validation_class_history_missing_required():
    # Missing required 'attended' column
    invalid_data = {
        "class_date": ["2026-05-01"],
        "class_time": ["18:00"],
        "class_type": ["Vinyasa Flow"],
        "capacity": [25],
        "price": [20.00]
    }
    df = pd.DataFrame(invalid_data)
    val = validate_class_history(df)
    assert val["valid"] is False
    assert any("attended" in err for err in val["errors"])

def test_validation_survey_responses_out_of_bounds():
    # Overall rating 6 out of 5 scale
    invalid_data = {
        "response_date": ["2026-05-01"],
        "overall_rating": [6],
        "likelihood_to_return": [12]
    }
    df = pd.DataFrame(invalid_data)
    val = validate_survey_responses(df)
    assert val["valid"] is False

def test_validation_event_outcomes():
    event_data = {
        "event_date": ["2026-06-01"],
        "event_name": ["Corporate Wellness Day"],
        "event_type": ["Corporate Wellness"],
        "expected_attendance": [30],
        "actual_attendance": [35]
    }
    df = pd.DataFrame(event_data)
    val = validate_event_outcomes(df)
    assert val["valid"] is True
    assert val["total_actual_attendees"] == 35

def test_demo_datasets_pass_validation():
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    df_c = pd.read_csv(os.path.join(demo_dir, "class_history.csv"))
    df_s = pd.read_csv(os.path.join(demo_dir, "survey_responses.csv"))
    df_e = pd.read_csv(os.path.join(demo_dir, "event_outcomes.csv"))

    val_c = validate_class_history(df_c)
    val_s = validate_survey_responses(df_s)
    val_e = validate_event_outcomes(df_e)

    assert val_c["valid"] is True
    assert val_s["valid"] is True
    assert val_e["valid"] is True
