"""
test_outreach.py - Tests for Cold Outreach Email Sequence Engine.
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from evidence import compute_all_evidence_cards
from outreach import generate_outreach_sequence, OutreachSequence, EmailTouch


@pytest.fixture(scope="module")
def demo_evidence():
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    c_df = pd.read_csv(os.path.join(demo_dir, "class_history.csv"))
    s_df = pd.read_csv(os.path.join(demo_dir, "survey_responses.csv"))
    e_df = pd.read_csv(os.path.join(demo_dir, "event_outcomes.csv"))
    return compute_all_evidence_cards(c_df, s_df, e_df)


OPPORTUNITIES = [
    "studio_residency",
    "corporate_wellness",
    "community_organization",
    "school",
    "festival",
    "hotel",
    "private_event",
]


def test_generate_outreach_all_7_opportunities(demo_evidence):
    for opp_id in OPPORTUNITIES:
        seq = generate_outreach_sequence(opp_id, demo_evidence)
        assert isinstance(seq, OutreachSequence)
        assert seq.opportunity_id == opp_id
        assert len(seq.touches) == 3
        for idx, touch in enumerate(seq.touches, 1):
            assert isinstance(touch, EmailTouch)
            assert touch.touch_number == idx
            assert len(touch.subject) > 5
            assert len(touch.body) > 50
            assert len(touch.proof_point_highlighted) > 5


def test_outreach_custom_profile_binding(demo_evidence):
    custom_profile = {
        "name": "Mariana Chroez",
        "disciplines": "Vinyasa Yoga & Breathwork",
        "years_teaching": 4,
        "email": "mariana@chieac.com",
        "phone": "(312) 555-0149",
        "location": "Minneapolis, MN",
    }
    seq = generate_outreach_sequence("corporate_wellness", demo_evidence, instructor_profile=custom_profile)
    t1 = seq.touches[0]
    assert "Mariana Chroez" in t1.body
    assert "mariana@chieac.com" in t1.body
    assert "(312) 555-0149" in t1.body
    assert "Minneapolis, MN" in t1.body
    assert "4 years of experience" in t1.body


def test_outreach_evidence_metric_grounding(demo_evidence):
    seq = generate_outreach_sequence("corporate_wellness", demo_evidence)
    body_text = " ".join(t.body for t in seq.touches)
    # Check that stress reduction and recommend rate are referenced
    assert "stress" in body_text.lower()
    assert "recommendation" in body_text.lower()
