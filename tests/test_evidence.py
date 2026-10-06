"""
tests/test_evidence.py
Unit tests covering all 25 metric functions across the 6 families,
Pydantic EvidenceCard schema validation, and export functions.
Run with: pytest tests/
"""

import os
import sys
import json
import pandas as pd
import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from evidence import (
    EvidenceCard,
    compute_all_evidence_cards,
    export_cards_to_json,
    export_cards_to_dataframe,
    # Family 1
    metric_classes_taught_12m,
    metric_classes_held_ratio,
    metric_avg_attendance,
    metric_unique_participants,
    metric_attendance_growth_qoq,
    # Family 2
    metric_first_to_second_conv,
    metric_return_rate_30d,
    metric_return_rate_60d,
    metric_repeat_attendance_share,
    metric_max_client_streak,
    # Family 3
    metric_fill_rate_avg,
    metric_high_capacity_share,
    metric_sell_out_count,
    metric_peak_class_size,
    metric_evening_fill_rate,
    # Family 4
    metric_overall_rating_avg,
    metric_net_promoter_score,
    metric_stress_reduction_delta,
    metric_felt_welcomed_score,
    metric_recommend_rate,
    # Family 5
    metric_events_delivered_count,
    metric_event_turnout_ratio,
    metric_repeat_booking_rate,
    # Family 6
    metric_lunchtime_flexibility,
    metric_quotable_comments_count
)

@pytest.fixture
def sample_class_df():
    return pd.DataFrame({
        "class_date": ["2026-05-01", "2026-05-08", "2026-05-15", "2026-05-22", "2026-05-29"],
        "class_time": ["18:30", "12:00", "19:00", "07:30", "18:30"],
        "class_type": ["Vinyasa Flow", "Desk Mobility", "Yin", "Morning Flow", "Vinyasa Flow"],
        "capacity": [20, 25, 20, 20, 20],
        "attended": [18, 25, 20, 12, 19],
        "price": [20.0, 20.0, 25.0, 20.0, 20.0],
        "client_id": ["u1", "u1", "u2", "u3", "u1"],
        "venue_name": ["Bloom Studio", "Loop Office", "Bloom Studio", "Bloom Studio", "Bloom Studio"]
    })

@pytest.fixture
def sample_survey_df():
    return pd.DataFrame({
        "response_date": ["2026-05-01", "2026-05-08", "2026-05-15"],
        "overall_rating": [5, 4, 5],
        "likelihood_to_return": [10, 8, 10],
        "stress_before": [8, 7, 9],
        "stress_after": [3, 4, 2],
        "felt_welcomed": [5, 5, 4],
        "would_recommend": ["Y", "Y", "Y"],
        "comment": ["Amazing class!", "Great reset.", "Loved the cues."],
        "consent_to_quote": ["Y", "Y", "N"]
    })

@pytest.fixture
def sample_event_df():
    return pd.DataFrame({
        "event_date": ["2026-06-01", "2026-07-01"],
        "event_name": ["Corporate Reset", "Hotel Morning"],
        "event_type": ["Corporate Wellness", "Hotel Residency"],
        "expected_attendance": [20, 15],
        "actual_attendance": [25, 18],
        "repeat_booking": ["Y", "N"],
        "host_rating": [5, 5]
    })

# ── Tests for Family 1 ───────────────────────────────────────────────────────

def test_family_1_consistency_metrics(sample_class_df):
    c1 = metric_classes_taught_12m(sample_class_df)
    assert c1 is not None and c1.value == 5

    c2 = metric_classes_held_ratio(sample_class_df)
    assert c2 is not None and c2.value > 90

    c3 = metric_avg_attendance(sample_class_df)
    assert c3 is not None and c3.value == 18.8

    c4 = metric_unique_participants(sample_class_df)
    assert c4 is not None and c4.value == 3

# ── Tests for Family 2 ───────────────────────────────────────────────────────

def test_family_2_retention_metrics(sample_class_df):
    c6 = metric_first_to_second_conv(sample_class_df)
    assert c6 is not None and c6.value > 0

    c7 = metric_return_rate_30d(sample_class_df)
    assert c7 is not None and c7.value > 0

    c8 = metric_repeat_attendance_share(sample_class_df)
    assert c8 is not None and c8.value > 0

    c9 = metric_max_client_streak(sample_class_df)
    assert c9 is not None and c9.value >= 1

# ── Tests for Family 3 ───────────────────────────────────────────────────────

def test_family_3_demand_metrics(sample_class_df):
    c11 = metric_fill_rate_avg(sample_class_df)
    assert c11 is not None and 80 < c11.value < 100

    c12 = metric_high_capacity_share(sample_class_df)
    assert c12 is not None and c12.value >= 60

    c13 = metric_sell_out_count(sample_class_df)
    assert c13 is not None and c13.value >= 2  # 25/25 and 20/20

    c14 = metric_peak_class_size(sample_class_df)
    assert c14 is not None and c14.value == 25

    c15 = metric_evening_fill_rate(sample_class_df)
    assert c15 is not None and c15.value > 80

# ── Tests for Family 4 ───────────────────────────────────────────────────────

def test_family_4_outcome_metrics(sample_survey_df):
    c16 = metric_overall_rating_avg(sample_survey_df)
    assert c16 is not None and round(c16.value, 1) == 4.7

    c17 = metric_net_promoter_score(sample_survey_df)
    assert c17 is not None and c17.value > 50

    c18 = metric_stress_reduction_delta(sample_survey_df)
    assert c18 is not None and c18.value == 5.0  # (8-3 + 7-4 + 9-2)/3 = (5 + 3 + 7)/3 = 5.0

    c19 = metric_felt_welcomed_score(sample_survey_df)
    assert c19 is not None and c19.value > 4.5

    c20 = metric_recommend_rate(sample_survey_df)
    assert c20 is not None and c20.value == 100.0

# ── Tests for Family 5 ───────────────────────────────────────────────────────

def test_family_5_event_metrics(sample_event_df):
    c21 = metric_events_delivered_count(sample_event_df)
    assert c21 is not None and c21.value == 2

    c22 = metric_event_turnout_ratio(sample_event_df)
    assert c22 is not None and c22.value > 100  # 43 / 35 > 100%

    c23 = metric_repeat_booking_rate(sample_event_df)
    assert c23 is not None and c23.value == 50.0

# ── Tests for Family 6 ───────────────────────────────────────────────────────

def test_family_6_fit_signals(sample_class_df, sample_survey_df):
    c24 = metric_lunchtime_flexibility(sample_class_df)
    assert c24 is not None and c24.value == 1

    c25 = metric_quotable_comments_count(sample_survey_df)
    assert c25 is not None and c25.value == 2

# ── Master Engine & Demo Data Integration ───────────────────────────────────

def test_demo_dataset_produces_full_evidence_cards():
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    df_c = pd.read_csv(os.path.join(demo_dir, "class_history.csv"))
    df_s = pd.read_csv(os.path.join(demo_dir, "survey_responses.csv"))
    df_e = pd.read_csv(os.path.join(demo_dir, "event_outcomes.csv"))

    cards = compute_all_evidence_cards(df_c, df_s, df_e)
    assert len(cards) >= 24

    # Validate Pydantic schema serialization
    json_str = export_cards_to_json(cards)
    data = json.loads(json_str)
    assert len(data) == len(cards)
    assert all("id" in item and "value" in item and "method_note" in item for item in data)

    # Validate DataFrame export
    df_cards = export_cards_to_dataframe(cards)
    assert len(df_cards) == len(cards)
    assert "formatted_value" in df_cards.columns
