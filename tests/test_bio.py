"""
test_bio.py - Tests for Verified Bio & Grant Narrative Builder.
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from evidence import compute_all_evidence_cards
from bio_builder import generate_verified_bios, VerifiedBioSet


@pytest.fixture(scope="module")
def demo_evidence():
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    c_df = pd.read_csv(os.path.join(demo_dir, "class_history.csv"))
    s_df = pd.read_csv(os.path.join(demo_dir, "survey_responses.csv"))
    e_df = pd.read_csv(os.path.join(demo_dir, "event_outcomes.csv"))
    return compute_all_evidence_cards(c_df, s_df, e_df)


def test_generate_verified_bios_structure(demo_evidence):
    bios = generate_verified_bios(demo_evidence)
    assert isinstance(bios, VerifiedBioSet)
    assert bios.instructor_name == "Your Name"
    assert len(bios.short_bio) > 50
    assert len(bios.medium_bio) > 100
    assert len(bios.grant_statement) > 200

    # Check word counts
    assert 25 <= bios.word_counts["short_bio"] <= 85
    assert 65 <= bios.word_counts["medium_bio"] <= 150
    assert 170 <= bios.word_counts["grant_statement"] <= 350
    assert len(bios.metrics_cited) >= 4


def test_custom_profile_in_bios(demo_evidence):
    custom_profile = {
        "name": "Mariana Chroez",
        "disciplines": "Restorative Yoga & Breathwork",
        "years_teaching": 5,
        "location": "Minneapolis, MN",
    }
    bios = generate_verified_bios(demo_evidence, instructor_profile=custom_profile)
    assert bios.instructor_name == "Mariana Chroez"
    for text in [bios.short_bio, bios.medium_bio, bios.grant_statement]:
        assert "Mariana" in text
        assert "Minneapolis, MN" in text
        assert "5 years" in text


def test_metric_citations_in_grant_statement(demo_evidence):
    bios = generate_verified_bios(demo_evidence)
    # Check that ratings and stress stats appear in the grant statement
    assert "4.77" in bios.grant_statement or "rating" in bios.grant_statement.lower()
    assert "stress" in bios.grant_statement.lower()


def test_first_person_perspective(demo_evidence):
    bios_1st = generate_verified_bios(demo_evidence, perspective="first_person")
    assert bios_1st.short_bio.startswith("I am")
    assert bios_1st.medium_bio.startswith("I am")
    assert "I specialize" in bios_1st.short_bio
    assert "I design" in bios_1st.medium_bio
    assert "Community Impact & Fellowship Statement" in bios_1st.grant_statement

