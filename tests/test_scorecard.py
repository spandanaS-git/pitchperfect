"""
tests/test_scorecard.py
Unit tests for PitchPerfect Week 4: Opportunity Scorecard & Gap Analysis Engine.
"""

import pytest
import os
import sys
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from evidence import compute_all_evidence_cards
from scorecard import (
    load_taxonomy,
    calculate_opportunity_scorecard,
    generate_radar_chart_figure,
    export_scorecard_to_excel,
    ScorecardResult
)

@pytest.fixture
def taxonomy():
    return load_taxonomy()

@pytest.fixture
def demo_evidence_cards():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    demo_dir = os.path.join(base_dir, "data", "demo")
    
    c_df = pd.read_csv(os.path.join(demo_dir, "class_history.csv"))
    s_df = pd.read_csv(os.path.join(demo_dir, "survey_responses.csv"))
    e_df = pd.read_csv(os.path.join(demo_dir, "event_outcomes.csv"))
    
    return compute_all_evidence_cards(c_df, s_df, e_df)

def test_taxonomy_loads_all_7_opportunities(taxonomy):
    expected_keys = [
        "studio_residency", "corporate_wellness", "community_organization",
        "school", "festival", "hotel", "private_event"
    ]
    for key in expected_keys:
        assert key in taxonomy, f"Missing {key} in taxonomy.yaml"
        opp = taxonomy[key]
        weights = opp.get("evidence_weights", {})
        total_weight = sum(weights.values())
        assert total_weight == 100, f"Weights for {key} sum to {total_weight}, expected 100"

def test_scorecard_calculation_with_demo_cards(demo_evidence_cards, taxonomy):
    result = calculate_opportunity_scorecard(demo_evidence_cards, taxonomy_dict=taxonomy)
    assert isinstance(result, ScorecardResult)
    assert len(result.opportunity_scores) == 7
    assert len(result.ranked_opportunities) == 7
    assert result.top_opportunity_id != ""

    for opp_id, opp in result.opportunity_scores.items():
        assert 0.0 <= opp.total_score <= 100.0
        assert opp.tier in ["Pitch-Ready (85–100)", "Strong Contender (65–84)", "Evidence Gap (<65)"]
        assert len(opp.breakdown) > 0

def test_policy_overrides_impact_scores(demo_evidence_cards, taxonomy):
    # Corporate wellness requires liability insurance (10 pts)
    active_result = calculate_opportunity_scorecard(
        demo_evidence_cards,
        policy_overrides={"liability_insurance_on_file": True},
        taxonomy_dict=taxonomy
    )
    inactive_result = calculate_opportunity_scorecard(
        demo_evidence_cards,
        policy_overrides={"liability_insurance_on_file": False},
        taxonomy_dict=taxonomy
    )

    score_active = active_result.opportunity_scores["corporate_wellness"].total_score
    score_inactive = inactive_result.opportunity_scores["corporate_wellness"].total_score

    assert score_active > score_inactive
    assert score_active - score_inactive == pytest.approx(10.0, rel=1e-1)
    
    # Inactive result should have gap recommendation for liability insurance
    gaps = inactive_result.opportunity_scores["corporate_wellness"].gaps
    assert any("insurance" in g.lower() for g in gaps)

def test_empty_cards_graceful_handling(taxonomy):
    # When no cards and all policies are inactive
    all_false_policies = {
        "liability_insurance_on_file": False,
        "background_check_on_file": False,
        "sliding_scale_policy": False,
        "language_matches": False,
        "professional_certifications": False,
        "clear_rate_card_on_file": False,
        "park_community_venue_history": False,
        "youth_segment_experience": False,
        "outdoor_event_track_record": False,
        "private_event_experience": False,
    }
    empty_result = calculate_opportunity_scorecard(
        [],
        policy_overrides=all_false_policies,
        taxonomy_dict=taxonomy
    )
    assert isinstance(empty_result, ScorecardResult)
    assert len(empty_result.opportunity_scores) == 7
    for opp in empty_result.opportunity_scores.values():
        assert opp.total_score <= 35.0
        assert len(opp.gaps) > 0

def test_radar_chart_figure_generation(demo_evidence_cards, taxonomy):
    result = calculate_opportunity_scorecard(demo_evidence_cards, taxonomy_dict=taxonomy)
    fig = generate_radar_chart_figure(result)
    assert fig is not None
    assert len(fig.data) > 0
    # Radar chart closes loop (7 categories + 1 duplicate = 8 points)
    assert len(fig.data[0].r) == 8

def test_export_scorecard_to_excel(demo_evidence_cards, taxonomy):
    result = calculate_opportunity_scorecard(demo_evidence_cards, taxonomy_dict=taxonomy)
    excel_bytes = export_scorecard_to_excel(result, "corporate_wellness")
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 1000
    
    # Read back with pandas to verify valid Excel structure
    import io
    excel_file = pd.ExcelFile(io.BytesIO(excel_bytes))
    assert "All 7 Opportunities" in excel_file.sheet_names
    assert "Corporate Wellness Breakdown" in excel_file.sheet_names
    # Verify Sheet 1 is the primary detailed breakdown
    assert excel_file.sheet_names[0] == "Corporate Wellness Breakdown"
    df_break = pd.read_excel(excel_file, sheet_name=excel_file.sheet_names[0])
    assert "Priority / Metric" in df_break.columns
    assert "Max Weight (pts)" in df_break.columns
    assert "Score Earned (pts)" in df_break.columns
