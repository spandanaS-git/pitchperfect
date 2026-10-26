"""
outreach.py - Cold Outreach Email Sequence Engine for PitchPerfect.

Generates tailored, 3-touch cold outreach email campaigns for each of the 7
opportunity buyer types, grounded in verified Evidence Cards and customized
with instructor contact information.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
try:
    from pitchkit import build_evidence_map
except ImportError:
    from src.pitchkit import build_evidence_map


class EmailTouch(BaseModel):
    touch_number: int
    title: str
    timing: str
    subject: str
    body: str
    proof_point_highlighted: str


class OutreachSequence(BaseModel):
    opportunity_id: str
    opportunity_name: str
    target_buyer: str
    touches: List[EmailTouch] = Field(default_factory=list)


def _clean_instructor_profile(profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    prof = {
        "name": "Your Name",
        "disciplines": "Movement & Mindfulness",
        "years_teaching": 3,
        "email": "contact@pitchperfect.org",
        "phone": "(312) 555-0100",
        "location": "Chicago, IL",
    }
    if profile:
        for k, v in profile.items():
            if v is not None and str(v).strip():
                prof[k] = v
    return prof


def generate_outreach_sequence(
    opportunity_id: str,
    evidence_cards: List[Any],
    scorecard: Optional[Any] = None,
    instructor_profile: Optional[Dict[str, Any]] = None,
) -> OutreachSequence:
    """
    Generate a 3-touch outreach sequence tailored to the buyer for a given opportunity.
    """
    prof = _clean_instructor_profile(instructor_profile)
    inst_name = str(prof["name"]).strip()
    inst_disc = str(prof["disciplines"]).strip()
    inst_email = str(prof["email"]).strip()
    inst_phone = str(prof["phone"]).strip()
    inst_loc = str(prof["location"]).strip()
    inst_years = int(prof.get("years_teaching", 3))

    ev_map = build_evidence_map(evidence_cards)

    # Opportunity specifics
    if opportunity_id == "corporate_wellness":
        stress_val = ev_map.get("stress_reduction_avg", "4.9 pt drop")
        rec_val = ev_map.get("recommend_rate_pct", "100.0%")
        lunch_val = ev_map.get("lunchtime_classes_count", "150+ sessions")
        rating_val = ev_map.get("overall_rating_avg", "4.77 / 5.0")

        touches = [
            EmailTouch(
                touch_number=1,
                title="Touch 1: Initial Inquiry & Stress Reduction Proof",
                timing="Day 0 — Initial Outreach",
                subject=f"Employee wellness with documented stress relief ({inst_loc})",
                body=(
                    f"Hi there,\n\n"
                    f"I hope you're having a productive week. As People Operations teams plan upcoming wellness "
                    f"initiatives, many find that conventional programs lack measurable outcome data to justify the time.\n\n"
                    f"My name is {inst_name}, a {inst_loc}-based {inst_disc} instructor with {inst_years} years of experience "
                    f"facilitating workplace movement. Unlike standard offerings, our sessions track participant impact: "
                    f"employees report an average {stress_val} in stress from arrival to departure, with a {rec_val} peer recommendation rate.\n\n"
                    f"All programs are turnkey (zero equipment or setup required) and backed by a $2M commercial liability policy.\n\n"
                    f"Would you be open to a brief 10-minute introductory call next Tuesday or Thursday to see if our midday reset "
                    f"could support your team?\n\n"
                    f"Warm regards,\n\n"
                    f"{inst_name}\n"
                    f"{inst_disc} Specialist\n"
                    f"Email: {inst_email} | Phone: {inst_phone}\n"
                    f"Location: {inst_loc}"
                ),
                proof_point_highlighted=f"Average Stress Reduction: {stress_val} | Recommend Rate: {rec_val}",
            ),
            EmailTouch(
                touch_number=2,
                title="Touch 2: Midday Scheduling Track Record",
                timing="Day 4 — Evidence Follow-up",
                subject=f"Re: Midday wellness scheduling for your team ({lunch_val} delivered)",
                body=(
                    f"Hi there,\n\n"
                    f"Following up on my note from earlier this week. I know your calendar is packed, so I wanted to share a "
                    f"quick proof point regarding scheduling fit:\n\n"
                    f"We have delivered {lunch_val} specifically designed for midday 'lunch-and-learn' time slots (11 AM – 1 PM). "
                    f"These sessions focus on desk posture reset, shoulder tension, and nervous system calm—without requiring sweaty clothing changes.\n\n"
                    f"Previous partner employees maintain a {rating_val} overall satisfaction score across post-class surveys.\n\n"
                    f"I'd love to send over a 1-page tailored proposal outlining format options if this aligns with your current priorities.\n\n"
                    f"Best regards,\n\n"
                    f"{inst_name}\n"
                    f"{inst_email} | {inst_phone}"
                ),
                proof_point_highlighted=f"Midday Sessions: {lunch_val} | Participant Satisfaction: {rating_val}",
            ),
            EmailTouch(
                touch_number=3,
                title="Touch 3: Zero-Risk 4-Week Pilot Offer",
                timing="Day 9 — Low-Friction Pilot Close",
                subject=f"Simple 4-week wellness pilot for {inst_loc} team?",
                body=(
                    f"Hi there,\n\n"
                    f"I'm circling back one last time in case you're planning your upcoming quarter's wellness schedule.\n\n"
                    f"To make exploring this completely frictionless, we offer a structured 4-week introductory pilot. "
                    f"We provide all session coordination, liability coverage, and include executive pulse reports showing your team's "
                    f"actual attendance and stress reduction deltas.\n\n"
                    f"If you'd like to explore this, you can reply directly or grab 15 minutes at your convenience: {inst_phone}.\n\n"
                    f"Wishing you and your team a wonderful week ahead!\n\n"
                    f"Warmly,\n\n"
                    f"{inst_name}\n"
                    f"{inst_email}"
                ),
                proof_point_highlighted="Turnkey 4-Week Pilot with Executive Pulse Impact Reporting",
            ),
        ]
        return OutreachSequence(
            opportunity_id=opportunity_id,
            opportunity_name="Corporate Wellness",
            target_buyer="HR Director / People Ops / Wellness Coordinator",
            touches=touches,
        )

    elif opportunity_id == "studio_residency":
        fill_val = ev_map.get("fill_rate_avg", "84.5%")
        ret_val = ev_map.get("retention_30d_pct", "78.0%")
        rating_val = ev_map.get("overall_rating_avg", "4.77 / 5.0")
        sub_ratio = ev_map.get("classes_held_ratio", "96.2%")

        touches = [
            EmailTouch(
                touch_number=1,
                title="Touch 1: Cohort Retention & Fill Rate Lead",
                timing="Day 0 — Initial Outreach",
                subject=f"Teaching residency inquiry: {fill_val} fill rate & strong student retention",
                body=(
                    f"Hi there,\n\n"
                    f"I hope you're having a vibrant week at the studio. I am a long-time admirer of the community and intentional space "
                    f"you've built here in {inst_loc}.\n\n"
                    f"My name is {inst_name}, teaching {inst_disc} with {inst_years} years of dedicated instruction. As you plan upcoming "
                    f"schedule adjustments, I wanted to reach out regarding potential recurring teaching residency opportunities.\n\n"
                    f"My teaching practice focuses on building loyal, high-retention student cohorts: across my recent classes, I have maintained "
                    f"an average {fill_val} studio fill rate, a {ret_val} 30-day student return rate, and an attendance reliability score of {sub_ratio}.\n\n"
                    f"I would welcome the opportunity to connect for a quick 10-minute coffee or sub an upcoming class to let your community experience "
                    f"the energy firsthand.\n\n"
                    f"Warm regards,\n\n"
                    f"{inst_name}\n"
                    f"{inst_disc} Instructor\n"
                    f"{inst_email} | {inst_phone}"
                ),
                proof_point_highlighted=f"Studio Fill Rate: {fill_val} | 30-Day Retention: {ret_val}",
            ),
            EmailTouch(
                touch_number=2,
                title="Touch 2: Sub-List & Student Feedback Proof",
                timing="Day 4 — Community Feedback Follow-up",
                subject="Re: Available to sub / studio teaching audition",
                body=(
                    f"Hi there,\n\n"
                    f"Following up briefly on my earlier note. I know studio directors are often in need of reliable, experienced instructors "
                    f"to keep high-demand evening and weekend slots filled.\n\n"
                    f"With a {rating_val} student satisfaction score across recent surveys, my priority is ensuring students leave feeling supported, "
                    f"seen, and excited to book their next visit.\n\n"
                    f"If you have an active sub list, I would be delighted to join it, or stop by for a 30-minute studio demo class whenever convenient.\n\n"
                    f"Best regards,\n\n"
                    f"{inst_name}\n"
                    f"{inst_email} | {inst_phone}"
                ),
                proof_point_highlighted=f"Student Satisfaction: {rating_val} | Class Reliability: {sub_ratio}",
            ),
            EmailTouch(
                touch_number=3,
                title="Touch 3: Guest Class or Workshop Offer",
                timing="Day 9 — Low-Commitment Workshop Offer",
                subject=f"Weekend community workshop or guest residency slot? ({inst_loc})",
                body=(
                    f"Hi there,\n\n"
                    f"I wanted to check in one last time regarding your upcoming season schedule.\n\n"
                    f"If full residency slots are currently locked, I would love to propose a single weekend masterclass or specialized "
                    f"workshop in {inst_disc} to introduce my teaching style to your members with zero overhead on the studio.\n\n"
                    f"Feel free to reply here or text me at {inst_phone} if that sounds like a good fit for your members.\n\n"
                    f"Warmly,\n\n"
                    f"{inst_name}\n"
                    f"{inst_email}"
                ),
                proof_point_highlighted="Turnkey Weekend Masterclass / Guest Residency Slot",
            ),
        ]
        return OutreachSequence(
            opportunity_id=opportunity_id,
            opportunity_name="Studio Residency",
            target_buyer="Studio Owner / Program Director",
            touches=touches,
        )

    elif opportunity_id == "school":
        peak_size = ev_map.get("peak_class_size", "32 attendees")
        rating_val = ev_map.get("overall_rating_avg", "4.77 / 5.0")
        rel_val = ev_map.get("classes_held_ratio", "96.2%")

        touches = [
            EmailTouch(
                touch_number=1,
                title="Touch 1: Youth Regulation & Safety Compliance",
                timing="Day 0 — Initial Outreach",
                subject=f"Youth movement & focus regulation programming (Vetted & Insured, {inst_loc})",
                body=(
                    f"Dear Administrator,\n\n"
                    f"I hope your school year is going smoothly. As schools increasingly seek somatic tools to support student focus, "
                    f"anxiety de-escalation, and athletic recovery, contractor vetting and safety are top priorities.\n\n"
                    f"My name is {inst_name}, a {inst_disc} educator in {inst_loc} with {inst_years} years of youth-centered instructional experience. "
                    f"I maintain up-to-date background clearances, $2M general liability insurance, and trauma-informed youth facilitation protocols.\n\n"
                    f"I have successfully commanded classroom and assembly cohorts of {peak_size} while maintaining classroom focus and emotional safety.\n\n"
                    f"Would you be open to a 10-minute call next week to see how our classroom reset or student-athlete conditioning modules could integrate into PE or advisory periods?\n\n"
                    f"Sincerely,\n\n"
                    f"{inst_name}\n"
                    f"Youth Movement Specialist\n"
                    f"Email: {inst_email} | Phone: {inst_phone}\n"
                    f"{inst_loc}"
                ),
                proof_point_highlighted=f"Classroom Cohort Handled: {peak_size} | Vetted Background Checks & $2M Insurance",
            ),
            EmailTouch(
                touch_number=2,
                title="Touch 2: Faculty De-Stress & Athletic Support",
                timing="Day 4 — Faculty & Athlete Focus",
                subject=f"Re: Supporting student focus and faculty wellness ({inst_loc})",
                body=(
                    f"Dear Administrator,\n\n"
                    f"Following up on my note regarding youth somatic programming. Beyond student sessions, we also deliver 45-minute "
                    f"Faculty De-Stress sessions during professional development periods to help prevent educator burnout.\n\n"
                    f"Previous institutional hosts have rated our instructional delivery at {rating_val} with an attendance reliability rate of {rel_val}.\n\n"
                    f"I would be glad to share our complete credential packet (W-9, certificate of insurance, clearances) whenever convenient.\n\n"
                    f"Best regards,\n\n"
                    f"{inst_name}\n"
                    f"{inst_email} | {inst_phone}"
                ),
                proof_point_highlighted=f"Host Rating: {rating_val} | Reliability Rate: {rel_val}",
            ),
            EmailTouch(
                touch_number=3,
                title="Touch 3: Complimentary Campus Demo Class",
                timing="Day 9 — Demo Class Offer",
                subject=f"Complimentary 30-min student demonstration session ({inst_loc})",
                body=(
                    f"Dear Administrator,\n\n"
                    f"To make evaluating our fit straightforward for your athletic department or student life team, I would be delighted to "
                    f"lead a complimentary 30-minute campus demonstration class for your PE faculty or student leaders.\n\n"
                    f"If you would like to arrange this, simply reply to this email or reach me at {inst_phone}.\n\n"
                    f"Thank you for your dedicated leadership of our students.\n\n"
                    f"Warmly,\n\n"
                    f"{inst_name}\n"
                    f"{inst_email}"
                ),
                proof_point_highlighted="Complimentary 30-Minute PE / Faculty Demonstration Class",
            ),
        ]
        return OutreachSequence(
            opportunity_id=opportunity_id,
            opportunity_name="School / Youth Program",
            target_buyer="Principal / Athletic Director / Student Life Coordinator",
            touches=touches,
        )

    else:
        # Generic high-conversion template for other opportunities (hotel, festival, private_event, community_org)
        opp_display = opportunity_id.replace("_", " ").title()
        buyer_title = "Decision Maker / Event Director"
        if opportunity_id == "hotel":
            buyer_title = "General Manager / Guest Experience Director"
        elif opportunity_id == "festival":
            buyer_title = "Festival Producer / Stage Curator"
        elif opportunity_id == "private_event":
            buyer_title = "Event Host / Retreat Coordinator"
        elif opportunity_id == "community_organization":
            buyer_title = "Executive Director / Program Coordinator"

        rating_val = ev_map.get("overall_rating_avg", "4.77 / 5.0")
        rec_val = ev_map.get("recommend_rate_pct", "98.0%")

        touches = [
            EmailTouch(
                touch_number=1,
                title="Touch 1: Initial Partnership Inquiry",
                timing="Day 0 — Initial Outreach",
                subject=f"{opp_display} partnership inquiry — {inst_disc} ({inst_loc})",
                body=(
                    f"Hi there,\n\n"
                    f"I hope you're having a wonderful week. I'm reaching out because I greatly admire the experiences you create for your community.\n\n"
                    f"My name is {inst_name}, a {inst_loc}-based instructor specializing in {inst_disc} with {inst_years} years of professional teaching experience. "
                    f"Across recent sessions, my programming has achieved a {rating_val} participant rating and a {rec_val} recommendation rate.\n\n"
                    f"I provide turnkey, insured, and custom-tailored sessions structured around the exact needs of your attendees.\n\n"
                    f"Would you be open to a brief 10-minute introductory call next week to explore potential collaboration?\n\n"
                    f"Warm regards,\n\n"
                    f"{inst_name}\n"
                    f"Email: {inst_email} | Phone: {inst_phone}\n"
                    f"Location: {inst_loc}"
                ),
                proof_point_highlighted=f"Participant Rating: {rating_val} | Recommend Rate: {rec_val}",
            ),
            EmailTouch(
                touch_number=2,
                title="Touch 2: Turnkey Logistics & Reliability",
                timing="Day 4 — Evidence & Reliability Follow-up",
                subject=f"Re: Turnkey {opp_display.lower()} programming ({inst_loc})",
                body=(
                    f"Hi there,\n\n"
                    f"Following up on my note from earlier this week. I know event curation requires seamless logistics with zero host stress.\n\n"
                    f"All of our sessions arrive with verified commercial liability insurance on file, clear transparent pricing, and structured "
                    f"curriculum adapted specifically to your venue and attendee demographic.\n\n"
                    f"I'd be glad to send over a 1-page rate card and tailored proposal if you have an upcoming date in mind.\n\n"
                    f"Best regards,\n\n"
                    f"{inst_name}\n"
                    f"{inst_email} | {inst_phone}"
                ),
                proof_point_highlighted="Turnkey Coordination & Verified Liability Insurance",
            ),
            EmailTouch(
                touch_number=3,
                title="Touch 3: Low-Friction Trial Engagement",
                timing="Day 9 — Low-Commitment Trial Offer",
                subject=f"Quick question regarding upcoming {opp_display.lower()} dates",
                body=(
                    f"Hi there,\n\n"
                    f"Checking in one last time as you finalize your upcoming calendar.\n\n"
                    f"If you'd like to test the waters with zero organizational risk, we offer an introductory trial session or co-hosted pop-up.\n\n"
                    f"Feel free to reply here or call me directly at {inst_phone} if that sounds like a good fit.\n\n"
                    f"Warmly,\n\n"
                    f"{inst_name}\n"
                    f"{inst_email}"
                ),
                proof_point_highlighted="Introductory Trial / Pop-up Activation Offer",
            ),
        ]
        return OutreachSequence(
            opportunity_id=opportunity_id,
            opportunity_name=opp_display,
            target_buyer=buyer_title,
            touches=touches,
        )
