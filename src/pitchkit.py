"""
src/pitchkit.py
Core Pitch Kit Generator Engine for PitchPerfect (ChiEAC Fellowship Week 5).
Combines verified Evidence Cards, Opportunity Scorecards, and Jinja2 templates
to generate tailored 1-2 page partnership pitch proposals for all 7 buyer types.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import jinja2
from pydantic import BaseModel, Field

from evidence import EvidenceCard
from scorecard import (
    ScorecardResult,
    OpportunityScore,
    calculate_opportunity_scorecard,
    load_taxonomy
)

# ── Pydantic Schema for Pitch Kit ──────────────────────────────────────────

class PitchKit(BaseModel):
    opportunity_id: str
    opportunity_name: str
    buyer: str
    buyer_priority: str
    narrative_focus: str
    instructor_name: str
    total_score: float
    tier: str
    tier_color: str
    pitch_title: str
    rendered_text: str
    top_evidence: List[Dict[str, Any]]
    scorecard_summary: Dict[str, Any]
    gap_closure_note: Optional[str] = None
    profile: Dict[str, Any] = Field(default_factory=dict)
    generated_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def export_text(self) -> str:
        return self.rendered_text


# ── Directory & Template Resolution Helpers ─────────────────────────────────

def get_templates_dir(custom_path: Optional[str] = None) -> str:
    """Resolves templates directory path across varied working directories."""
    if custom_path and os.path.isdir(custom_path):
        return custom_path

    # Try standard project root / templates
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tmpl_dir = os.path.join(base_dir, "templates")
    if os.path.isdir(tmpl_dir):
        return tmpl_dir

    # Try current directory / templates
    curr_tmpl = os.path.join(os.getcwd(), "templates")
    if os.path.isdir(curr_tmpl):
        return curr_tmpl

    return tmpl_dir


def load_template(opportunity_id: str, templates_dir: Optional[str] = None) -> jinja2.Template:
    """
    Loads and compiles the Jinja2 template for a specific opportunity type.
    Supports .j2, .jinja2, and .txt extensions.
    """
    tmpl_dir = get_templates_dir(templates_dir)
    loader = jinja2.FileSystemLoader(tmpl_dir)
    env = jinja2.Environment(
        loader=loader,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True
    )

    possible_filenames = [
        f"{opportunity_id}.j2",
        f"{opportunity_id}.jinja2",
        f"{opportunity_id}.txt",
        f"{opportunity_id}.md",
    ]

    for fname in possible_filenames:
        if os.path.exists(os.path.join(tmpl_dir, fname)):
            return env.get_template(fname)

    # If file not found in directory, raise clear error
    raise FileNotFoundError(
        f"Template for opportunity '{opportunity_id}' not found in '{tmpl_dir}'. "
        f"Looked for: {', '.join(possible_filenames)}"
    )


# ── Evidence Mapping & Selection ───────────────────────────────────────────

METRIC_ALIAS_MAP = {
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


def build_evidence_map(evidence_cards: List[EvidenceCard]) -> Dict[str, str]:
    """
    Creates a comprehensive lookup mapping metric IDs and aliases
    to their human-readable formatted_value.
    """
    res = {}
    card_dict = {c.id: c for c in evidence_cards}

    for card in evidence_cards:
        res[card.id] = card.formatted_value

    # Cross-populate aliases
    for alias_key, target_id in METRIC_ALIAS_MAP.items():
        if target_id in res and alias_key not in res:
            res[alias_key] = res[target_id]
        elif alias_key in res and target_id not in res:
            res[target_id] = res[alias_key]

    return res


def get_top_evidence_for_opportunity(
    opportunity_id: str,
    evidence_cards: List[EvidenceCard],
    opp_score: Optional[OpportunityScore] = None,
    limit: int = 4
) -> List[Dict[str, Any]]:
    """
    Extracts the highest-impact evidence cards for a given opportunity type,
    prioritizing metrics weighted heavily in taxonomy and with strong scores.
    """
    taxonomy = load_taxonomy()
    opp_spec = taxonomy.get(opportunity_id, {})
    weights = opp_spec.get("evidence_weights", {})

    card_map = {c.id: c for c in evidence_cards}
    # Also index cards by possible alias keys
    for alias_key, target_id in METRIC_ALIAS_MAP.items():
        if target_id in card_map and alias_key not in card_map:
            card_map[alias_key] = card_map[target_id]

    items = []
    seen_ids = set()

    # 1. First, check taxonomy weights ordered by weight descending
    sorted_weights = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    for metric_key, weight in sorted_weights:
        card = card_map.get(metric_key)
        if not card and metric_key in METRIC_ALIAS_MAP:
            card = card_map.get(METRIC_ALIAS_MAP[metric_key])

        if card and card.id not in seen_ids:
            seen_ids.add(card.id)
            items.append({
                "id": card.id,
                "label": card.label,
                "formatted_value": card.formatted_value,
                "sample_size": card.sample_size,
                "date_range": card.date_range,
                "source_file": card.source_file,
                "method_note": card.method_note,
                "weight": weight
            })
            if len(items) >= limit:
                break

    # 2. If fewer than limit, fill with remaining highest sample-size cards
    if len(items) < limit:
        remaining_cards = sorted(
            [c for c in evidence_cards if c.id not in seen_ids],
            key=lambda c: c.sample_size,
            reverse=True
        )
        for c in remaining_cards:
            items.append({
                "id": c.id,
                "label": c.label,
                "formatted_value": c.formatted_value,
                "sample_size": c.sample_size,
                "date_range": c.date_range,
                "source_file": c.source_file,
                "method_note": c.method_note,
                "weight": 10.0
            })
            if len(items) >= limit:
                break

    return items


# ── Gap Closure Note Generator ──────────────────────────────────────────────

def generate_gap_closure_note(opp_score: OpportunityScore) -> Optional[str]:
    """
    Generates a constructive, confident 'Evidence Bridge & Quality Assurance' note
    if the opportunity readiness score is under 85.
    If the score is >= 85, returns None (since the instructor is Pitch-Ready).
    """
    if opp_score.total_score >= 85.0:
        return None

    bullets = []
    if opp_score.gaps:
        for g in opp_score.gaps[:3]:
            bullets.append(f"- **Target Focus:** {g}")
    else:
        bullets.append("- **Target Focus:** Establishing pilot-specific baseline survey metrics and attendance tracking.")

    bullets_text = "\n".join(bullets)

    note = (
        f"**Evidence Bridge & Quality Assurance (Current Readiness: {opp_score.total_score}/100 — {opp_score.tier}):**\n"
        f"While our verified portfolio already demonstrates strong foundational outcomes across primary movement metrics, "
        f"we recognize this partnership prioritizes specific verification criteria. We have structured a proactive bridge plan:\n\n"
        f"{bullets_text}\n\n"
        f"To ensure mutual confidence, we propose a structured 30-day introductory pilot with milestone review points "
        f"to confirm complete satisfaction and measure participant progress firsthand."
    )
    return note


# ── Core Generator Functions ────────────────────────────────────────────────

DEFAULT_PROFILE = {
    "name": "Your Name",
    "disciplines": "Movement & Mindfulness",
    "years_teaching": 3,
    "email": "contact@pitchperfect.org",
    "phone": "(312) 555-0100",
    "location": "Chicago, IL",
    "insurance": True,
    "background_check": True,
    "sliding_scale": True,
    "languages": ["English"]
}


def generate_pitch_kit(
    opportunity_id: str,
    evidence_cards: List[EvidenceCard],
    scorecard: Optional[Union[ScorecardResult, OpportunityScore]] = None,
    instructor_profile: Optional[Dict[str, Any]] = None,
    templates_dir: Optional[str] = None
) -> PitchKit:
    """
    Generates a complete, tailored Pitch Kit for a single opportunity type.
    Renders Jinja2 template with verified evidence cards and scorecard data.
    """
    # 1. Resolve scorecard data
    if scorecard is None:
        scorecard_res = calculate_opportunity_scorecard(evidence_cards)
        opp_score = scorecard_res.opportunity_scores.get(opportunity_id)
        if opp_score is None:
            raise ValueError(f"Unknown opportunity_id: {opportunity_id}")
    elif isinstance(scorecard, ScorecardResult):
        if opportunity_id not in scorecard.opportunity_scores:
            raise ValueError(f"Opportunity '{opportunity_id}' not found in scorecard result.")
        opp_score = scorecard.opportunity_scores[opportunity_id]
    elif isinstance(scorecard, OpportunityScore):
        opp_score = scorecard
        opportunity_id = opp_score.opportunity_id
    else:
        raise TypeError(f"Unsupported scorecard type: {type(scorecard)}")

    # 2. Merge instructor profile
    profile = dict(DEFAULT_PROFILE)
    if instructor_profile:
        for k, v in instructor_profile.items():
            if v is not None and str(v).strip() != "":
                profile[k] = v

    inst_name = str(profile.get("name") or "Your Name").strip()
    if not inst_name:
        inst_name = "Your Name"

    # 3. Build top evidence and evidence mapping
    evidence_map = build_evidence_map(evidence_cards)
    top_evidence = get_top_evidence_for_opportunity(opportunity_id, evidence_cards, opp_score)

    # 4. Generate gap closure note if score < 85
    gap_note = generate_gap_closure_note(opp_score)

    # 5. Load and render template
    template = load_template(opportunity_id, templates_dir)
    custom_date = profile.get("proposal_date")
    if custom_date and str(custom_date).strip():
        gen_date = str(custom_date).strip()
    else:
        gen_date = datetime.now().strftime("%B %d, %Y")

    context = {
        "opportunity_id": opportunity_id,
        "opportunity_name": opp_score.opportunity_name,
        "buyer": opp_score.buyer,
        "buyer_priority": opp_score.buyer_priority,
        "narrative_focus": opp_score.narrative_focus,
        "instructor_name": inst_name,
        "disciplines": profile.get("disciplines", "Movement & Mindfulness"),
        "years_teaching": profile.get("years_teaching", 3),
        "total_score": opp_score.total_score,
        "tier": opp_score.tier,
        "tier_color": opp_score.tier_color,
        "top_evidence": top_evidence,
        "evidence_map": evidence_map,
        "strengths": opp_score.strengths,
        "gaps": opp_score.gaps,
        "gap_closure_note": gap_note,
        "profile": profile,
        "generated_date": gen_date,
        "breakdown": [b.model_dump() for b in opp_score.breakdown],
    }

    rendered = template.render(**context).strip()

    pitch_title = f"{opp_score.opportunity_name} Partnership Proposal — {inst_name}"

    return PitchKit(
        opportunity_id=opportunity_id,
        opportunity_name=opp_score.opportunity_name,
        buyer=opp_score.buyer,
        buyer_priority=opp_score.buyer_priority,
        narrative_focus=opp_score.narrative_focus,
        instructor_name=inst_name,
        total_score=opp_score.total_score,
        tier=opp_score.tier,
        tier_color=opp_score.tier_color,
        pitch_title=pitch_title,
        rendered_text=rendered,
        top_evidence=top_evidence,
        scorecard_summary=opp_score.model_dump(),
        gap_closure_note=gap_note,
        profile=profile,
        generated_date=gen_date
    )


def generate_all_pitch_kits(
    evidence_cards: List[EvidenceCard],
    scorecard: Optional[ScorecardResult] = None,
    instructor_profile: Optional[Dict[str, Any]] = None,
    templates_dir: Optional[str] = None
) -> Dict[str, PitchKit]:
    """
    Generates tailored Pitch Kits for all 7 opportunity types in taxonomy.
    Returns a dictionary of {opportunity_id: PitchKit}.
    """
    if scorecard is None:
        scorecard = calculate_opportunity_scorecard(evidence_cards)

    kits: Dict[str, PitchKit] = {}
    for opp_id in scorecard.ranked_opportunities:
        kits[opp_id] = generate_pitch_kit(
            opportunity_id=opp_id,
            evidence_cards=evidence_cards,
            scorecard=scorecard,
            instructor_profile=instructor_profile,
            templates_dir=templates_dir
        )

    return kits


def export_pitch_kit_to_text(pitch_kit: PitchKit) -> str:
    """Exports pitch kit rendered content as formatted plain text."""
    return pitch_kit.rendered_text


def export_pitch_kit_to_markdown(pitch_kit: PitchKit) -> str:
    """Exports pitch kit as standard markdown."""
    return pitch_kit.rendered_text
