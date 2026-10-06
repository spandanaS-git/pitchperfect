"""
src/scorecard.py
Opportunity Scorecard & Gap Analysis Engine for PitchPerfect (ChiEAC Fellowship).
Evaluates verified Evidence Cards against the 7 Opportunity Taxonomy types (0–100 score).
Produces actionable Gap Closure Plans and Plotly radar visual data.
"""

import os
import yaml
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import pandas as pd

from evidence import EvidenceCard

# Load taxonomy
def load_taxonomy(yaml_path: Optional[str] = None) -> Dict[str, Any]:
    if yaml_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        yaml_path = os.path.join(base_dir, "config", "taxonomy.yaml")
    
    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("opportunities", {})
    return {}

# ── Pydantic Schemas ─────────────────────────────────────────────────────────

class EvidenceBreakdown(BaseModel):
    metric_key: str
    label: str
    weight: float
    score_earned: float
    max_score: float
    status: str  # "Strong", "Moderate", "Gap"
    current_value: str
    gap_recommendation: Optional[str] = None

class OpportunityScore(BaseModel):
    opportunity_id: str
    opportunity_name: str
    buyer: str
    buyer_priority: str
    narrative_focus: str
    total_score: float
    tier: str  # "Pitch-Ready (85–100)", "Strong Contender (65–84)", "Evidence Gap (<65)"
    tier_color: str  # "#16A34A", "#D97706", "#DC2626"
    breakdown: List[EvidenceBreakdown]
    strengths: List[str]
    gaps: List[str]

class ScorecardResult(BaseModel):
    opportunity_scores: Dict[str, OpportunityScore]
    ranked_opportunities: List[str]
    top_opportunity_id: str

# ── Scoring Evaluation Helpers ──────────────────────────────────────────────

def _score_single_metric(
    metric_key: str,
    weight: float,
    card_map: Dict[str, EvidenceCard],
    policy_overrides: Dict[str, bool]
) -> tuple[float, str, str, Optional[str]]:
    """
    Computes (score_earned, status, current_value, gap_recommendation)
    for a given taxonomy metric requirement.
    """
    # 1. Policy / Checkbox items (e.g. liability insurance, background check, rate card)
    policy_defaults = {
        "liability_insurance_on_file": ("Liability Insurance", "Upload certificate of general liability insurance to unlock corporate & school deals."),
        "background_check_on_file": ("Background Check", "Complete verified state/FBI background check to qualify for K-12 school programs."),
        "sliding_scale_policy": ("Sliding-Scale Pricing", "Document a clear sliding-scale tier to demonstrate community equity access."),
        "language_matches": ("Multilingual Access", "Add secondary language cues or bilingual descriptions to expand community reach."),
        "professional_certifications": ("Accredited Credentials", "List verified 200/500hr RYT or NASM/ACE certifications on your profile."),
        "clear_rate_card_on_file": ("Transparent Rate Card", "Publish a standard private booking rate sheet with travel and cancellation terms."),
        "park_community_venue_history": ("Community Venues", "Teach or partner with 1+ local parks, libraries, or community centers."),
        "youth_segment_experience": ("Youth Group Experience", "Log classes or workshops specifically designed for teens or school-age youth."),
        "outdoor_event_track_record": ("Outdoor Event Experience", "Log outdoor park, rooftop, or festival sessions."),
        "private_event_experience": ("Private Group Experience", "Deliver and log 2+ custom corporate or private client sessions.")
    }

    if metric_key in policy_defaults:
        label, rec = policy_defaults[metric_key]
        is_active = policy_overrides.get(metric_key, True)  # default True for demo/fellowship testing
        if is_active:
            return round(weight, 1), "Strong", "Verified on file", None
        else:
            return 0.0, "Gap", "Missing / Not on file", rec

    # 2. Metric mapping from Evidence Cards
    metric_alias = {
        "fill_rate_avg": "avg_fill_rate",
        "first_to_second_conversion": "first_to_second_conv",
        "attendance_trend_positive": "attendance_growth_qoq",
        "unique_participant_count": "unique_participants",
        "lunchtime_availability": "lunchtime_flexibility",
        "quotable_community_comments": "quotable_comments_count",
        "classroom_group_size_handled": "peak_class_size",
        "school_host_rating_avg": "overall_rating_avg",
        "peak_class_size_delivered": "peak_class_size",
        "event_attendance_ratio": "event_turnout_ratio",
        "high_energy_comments_count": "quotable_comments_count",
        "early_morning_availability": "classes_held_ratio",
        "drop_in_experience_rate": "first_to_second_conv",
        "guest_style_comments": "quotable_comments_count",
        "host_rating_avg": "overall_rating_avg",
        "quotable_testimonials_count": "quotable_comments_count",
    }
    actual_id = metric_alias.get(metric_key, metric_key)
    card = card_map.get(actual_id)

    if card is None:
        return round(weight * 0.2, 1), "Gap", "No data uploaded", f"Upload spreadsheet logs containing {metric_key.replace('_', ' ')}."

    val = card.value
    formatted = card.formatted_value

    # Performance thresholds based on domain benchmarks
    if "fill_rate" in actual_id:
        if val >= 75.0: return weight, "Strong", formatted, None
        elif val >= 55.0: return round(weight * 0.75, 1), "Moderate", formatted, f"Boost average fill rate toward 75% (currently {formatted})."
        else: return round(weight * 0.4, 1), "Gap", formatted, f"Fill rate is currently {formatted}. Focus on high-demand time slots."

    elif "return_rate" in actual_id or "conversion" in actual_id:
        if val >= 60.0: return weight, "Strong", formatted, None
        elif val >= 40.0: return round(weight * 0.75, 1), "Moderate", formatted, f"Aim for 60%+ student re-attendance (currently {formatted})."
        else: return round(weight * 0.4, 1), "Gap", formatted, f"Low repeat conversion ({formatted}). Implement post-class follow-ups."

    elif "stress_reduction" in actual_id:
        if val >= 3.0: return weight, "Strong", formatted, None
        elif val >= 1.5: return round(weight * 0.75, 1), "Moderate", formatted, "Stress reduction is positive but moderate. Collect more survey responses."
        else: return round(weight * 0.3, 1), "Gap", formatted, "Stress reduction delta is low or unrecorded."

    elif "overall_rating" in actual_id or "welcomed" in actual_id:
        if val >= 4.7: return weight, "Strong", formatted, None
        elif val >= 4.3: return round(weight * 0.8, 1), "Moderate", formatted, f"Strong satisfaction ({formatted}), aim for 4.7+ to stand out."
        else: return round(weight * 0.4, 1), "Gap", formatted, f"Rating is {formatted}. Gather targeted qualitative student feedback."

    elif "recommend_rate" in actual_id or "classes_held" in actual_id or "repeat_booking" in actual_id:
        if val >= 90.0: return weight, "Strong", formatted, None
        elif val >= 75.0: return round(weight * 0.75, 1), "Moderate", formatted, f"Good reliability ({formatted}), target 90%+."
        else: return round(weight * 0.4, 1), "Gap", formatted, f"Currently {formatted}. Aim for consistent host/attendee re-engagement."

    elif "growth" in actual_id:
        if val >= 0: return weight, "Strong", formatted, None
        elif val >= -10.0: return round(weight * 0.7, 1), "Moderate", formatted, "Slight quarterly dip (-3% to -10%). Highlight stable core base."
        else: return round(weight * 0.3, 1), "Gap", formatted, "Notable attendance drop. Re-align class scheduling."

    elif "peak" in actual_id or "size" in actual_id:
        if val >= 25: return weight, "Strong", formatted, None
        elif val >= 15: return round(weight * 0.75, 1), "Moderate", formatted, f"Peak crowd size is {formatted}. Aim to headline a 25+ student session."
        else: return round(weight * 0.4, 1), "Gap", formatted, f"Peak size is {formatted}. Pitch smaller boutique offerings first."

    # Default fallback: proportional score
    return round(weight * 0.85, 1), "Strong", formatted, None

# ── Master Scorecard Generator ──────────────────────────────────────────────

def calculate_opportunity_scorecard(
    evidence_cards: List[EvidenceCard],
    policy_overrides: Optional[Dict[str, bool]] = None,
    taxonomy_dict: Optional[Dict[str, Any]] = None
) -> ScorecardResult:
    """
    Evaluates evidence cards against all 7 Opportunity types in taxonomy.
    Returns full ScorecardResult with ranked opportunities, scores, and gaps.
    """
    if taxonomy_dict is None:
        taxonomy_dict = load_taxonomy()

    if policy_overrides is None:
        # Default policies active for demo experience
        policy_overrides = {
            "liability_insurance_on_file": True,
            "background_check_on_file": True,
            "sliding_scale_policy": True,
            "language_matches": True,
            "professional_certifications": True,
            "clear_rate_card_on_file": True,
            "park_community_venue_history": True,
            "youth_segment_experience": True,
            "outdoor_event_track_record": True,
            "private_event_experience": True,
        }

    card_map = {c.id: c for c in evidence_cards}
    opp_scores: Dict[str, OpportunityScore] = {}

    for opp_id, opp_spec in taxonomy_dict.items():
        name = opp_spec.get("name", opp_id.replace("_", " ").title())
        buyer = opp_spec.get("buyer", "Decision Maker")
        buyer_priority = opp_spec.get("buyer_priority", "")
        narrative_focus = opp_spec.get("narrative_focus", "")
        weights = opp_spec.get("evidence_weights", {})

        breakdown: List[EvidenceBreakdown] = []
        total_score = 0.0
        strengths: List[str] = []
        gaps: List[str] = []

        for metric_key, weight in weights.items():
            earned, status, cur_val, rec = _score_single_metric(
                metric_key, float(weight), card_map, policy_overrides
            )
            total_score += earned
            
            clean_label = metric_key.replace("_", " ").title()
            breakdown.append(EvidenceBreakdown(
                metric_key=metric_key,
                label=clean_label,
                weight=float(weight),
                score_earned=earned,
                max_score=float(weight),
                status=status,
                current_value=cur_val,
                gap_recommendation=rec
            ))

            if status == "Strong":
                strengths.append(f"{clean_label}: {cur_val}")
            elif rec:
                gaps.append(rec)

        final_score = min(round(total_score, 1), 100.0)

        # Tier assignment
        if final_score >= 85.0:
            tier = "Pitch-Ready (85–100)"
            tier_color = "#16A34A"  # Green
        elif final_score >= 65.0:
            tier = "Strong Contender (65–84)"
            tier_color = "#D97706"  # Amber
        else:
            tier = "Evidence Gap (<65)"
            tier_color = "#DC2626"  # Red

        opp_scores[opp_id] = OpportunityScore(
            opportunity_id=opp_id,
            opportunity_name=name,
            buyer=buyer,
            buyer_priority=buyer_priority,
            narrative_focus=narrative_focus,
            total_score=final_score,
            tier=tier,
            tier_color=tier_color,
            breakdown=breakdown,
            strengths=strengths,
            gaps=gaps
        )

    # Rank by score descending
    ranked = sorted(opp_scores.keys(), key=lambda k: opp_scores[k].total_score, reverse=True)
    top_opp = ranked[0] if ranked else ""

    return ScorecardResult(
        opportunity_scores=opp_scores,
        ranked_opportunities=ranked,
        top_opportunity_id=top_opp
    )

# ── Visual Generator: Plotly Radar Chart ────────────────────────────────────

def generate_radar_chart_figure(scorecard: ScorecardResult):
    """
    Creates an interactive Plotly Radar / Spider chart
    visualizing the 0-100 scores across all 7 opportunity types.
    """
    import plotly.graph_objects as go

    categories = []
    scores = []

    for opp_id in scorecard.ranked_opportunities:
        opp = scorecard.opportunity_scores[opp_id]
        categories.append(opp.opportunity_name)
        scores.append(opp.total_score)

    # Close the radar loop
    if categories:
        categories.append(categories[0])
        scores.append(scores[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill="toself",
        fillcolor="rgba(37, 99, 235, 0.25)",
        line=dict(color="#1D4ED8", width=2.5),
        marker=dict(size=7, color="#1E40AF"),
        name="Readiness Score"
    ))

    fig.update_layout(
        uirevision="radar_zoom",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#64748B"),
                gridcolor="#E2E8F0"
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#1E293B", family="sans-serif"),
                gridcolor="#E2E8F0"
            )
        ),
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig

def generate_bar_chart_figure(scorecard: ScorecardResult):
    """
    Creates an interactive horizontal bar chart supporting full Cartesian
    box zoom, pan, hover tooltips, and axis scaling across all 7 opportunities.
    """
    import plotly.graph_objects as go

    # Invert order so top ranked appears at top of horizontal chart
    opp_ids = list(reversed(scorecard.ranked_opportunities))
    names = [scorecard.opportunity_scores[oid].opportunity_name for oid in opp_ids]
    scores = [scorecard.opportunity_scores[oid].total_score for oid in opp_ids]
    colors = [scorecard.opportunity_scores[oid].tier_color for oid in opp_ids]
    tiers = [scorecard.opportunity_scores[oid].tier for oid in opp_ids]

    fig = go.Figure(go.Bar(
        x=scores,
        y=names,
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(color="#1E293B", width=1)
        ),
        text=[f"  <b>{s}</b>/100" for s in scores],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Readiness Score: %{x}/100<br><extra></extra>"
    ))

    fig.update_layout(
        uirevision="bar_zoom",
        xaxis=dict(
            range=[0, 105],
            title="Readiness Score (0–100)",
            gridcolor="#E2E8F0"
        ),
        yaxis=dict(
            tickfont=dict(size=11, color="#1E293B")
        ),
        margin=dict(l=40, r=40, t=20, b=40),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig
