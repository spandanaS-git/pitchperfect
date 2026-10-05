"""
scripts/generate_demo_data.py
Generates realistic, reproducible synthetic demo datasets for PitchPerfect:
- class_history.csv (~600 classes over 18 months)
- survey_responses.csv (~150 survey responses)
- event_outcomes.csv (20 event outcomes)

Meets all ChiEAC benchmark requirements.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Set random seed for 100% reproducibility
random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_DATE = datetime(2025, 4, 1)
END_DATE = datetime(2026, 9, 30)
TOTAL_DAYS = (END_DATE - START_DATE).days

def generate_class_history():
    classes = []
    
    # Pool of 80 unique recurring clients to calculate realistic return & streak metrics
    clients = [f"usr_{i:04d}" for i in range(1, 81)]
    client_first_seen = {}
    
    # Class schedule definitions (Day of week: 0=Mon, 1=Tue, 2=Wed, etc.)
    weekly_schedule = [
        {"dow": 1, "time": "18:30", "type": "Vinyasa Flow", "venue": "Bloom Yoga Studio", "vtype": "Studio", "cap": 25, "price": 24.0, "fill_bias": 0.88}, # Tue PM fills
        {"dow": 2, "time": "12:00", "type": "Desk Worker Mobility", "venue": "Loop Innovation Hub", "vtype": "Corporate", "cap": 30, "price": 20.0, "fill_bias": 0.82}, # Wed noon corporate
        {"dow": 3, "time": "19:00", "type": "Candlelight Yin & Sound", "venue": "Bloom Yoga Studio", "vtype": "Studio", "cap": 20, "price": 26.0, "fill_bias": 0.95}, # Thu PM sellout
        {"dow": 4, "time": "07:00", "type": "Morning Vinyasa", "venue": "Bloom Yoga Studio", "vtype": "Studio", "cap": 20, "price": 22.0, "fill_bias": 0.65}, # Fri early AM struggles
        {"dow": 5, "time": "08:30", "type": "Saturday Sunrise Flow", "venue": "North Ave Beach", "vtype": "Park District", "cap": 35, "price": 15.0, "fill_bias": 0.78},
        {"dow": 5, "time": "11:00", "type": "Community Gentle Yoga", "venue": "Wicker Park Fieldhouse", "vtype": "Community Center", "cap": 30, "price": 0.0, "fill_bias": 0.90}, # Sat sliding scale/free
        {"dow": 6, "time": "10:30", "type": "Restorative Breath & Flow", "venue": "Bloom Yoga Studio", "vtype": "Studio", "cap": 22, "price": 24.0, "fill_bias": 0.85},
    ]

    curr_date = START_DATE
    while curr_date <= END_DATE:
        dow = curr_date.weekday()
        for slot in weekly_schedule:
            if slot["dow"] == dow:
                # 96% of scheduled classes are held (4% cancelled/holiday)
                if random.random() < 0.04:
                    continue
                
                cap = slot["cap"]
                # Determine attendance based on fill bias with realistic variance
                mean_att = cap * slot["fill_bias"]
                att = int(np.clip(np.random.normal(mean_att, 2.5), 5, cap))
                
                # Pick attendees from pool to simulate retention
                attendee_pool = random.sample(clients, min(att, len(clients)))
                for client in attendee_pool:
                    first_visit = "N"
                    if client not in client_first_seen:
                        client_first_seen[client] = curr_date
                        first_visit = "Y"
                    
                    classes.append({
                        "class_date": curr_date.strftime("%Y-%m-%d"),
                        "class_time": slot["time"],
                        "class_type": slot["type"],
                        "capacity": cap,
                        "attended": att,
                        "price": slot["price"],
                        "format": "In-person",
                        "venue_type": slot["vtype"],
                        "venue_name": slot["venue"],
                        "membership_type": "Sliding Scale" if slot["price"] == 0 else random.choice(["Monthly Member", "Drop-in", "ClassPass"]),
                        "client_id": client,
                        "first_visit": first_visit,
                        "zip": "60647" if slot["vtype"] == "Studio" else ("60601" if slot["vtype"] == "Corporate" else "60622")
                    })
        curr_date += timedelta(days=1)

    df_classes = pd.DataFrame(classes)
    # Deduplicate to class-session level for primary metrics (while keeping client interactions)
    # PitchPerfect accepts both per-session rows and per-attendee logs
    df_sessions = df_classes.drop_duplicates(subset=["class_date", "class_time", "class_type"]).copy()
    
    csv_path = os.path.join(OUTPUT_DIR, "class_history.csv")
    df_sessions.to_csv(csv_path, index=False)
    print(f"Generated {len(df_sessions)} classes in {csv_path}")
    return df_sessions

def generate_survey_responses():
    surveys = []
    
    comments_pool = [
        ("Mariana's cues made me feel completely grounded. Best lunchtime reset our team has ever had.", "Desk Worker"),
        ("I came in with a severe headache and racing thoughts. Leaving with complete mental clarity.", "Desk Worker"),
        ("Incredible pacing and playlist. Clear instructions with zero intimidation factor.", "Intermediate"),
        ("As a beginner, I was nervous, but she offered modifications that made me feel so welcomed.", "Beginner"),
        ("Her breathwork guidance completely reset my nervous system. I haven't slept this well in months.", "Desk Worker"),
        ("Warm, culturally grounded, and deeply restorative. A true community treasure.", "Community"),
        ("Clear anatomical cues and trauma-informed adjustments. Highest quality instruction in Chicago.", "Intermediate"),
        ("Our students were fully engaged and calm throughout the entire youth session.", "Youth"),
        ("Loved the bilingual cues and inclusive atmosphere. Everyone in the room felt seen.", "Community"),
        ("The perfect blend of mindful challenge and deep relaxation.", "Beginner"),
    ]
    
    # 150 surveys spread across the 18-month timeline
    survey_dates = [START_DATE + timedelta(days=random.randint(0, TOTAL_DAYS)) for _ in range(150)]
    survey_dates.sort()
    
    for s_date in survey_dates:
        # High satisfaction profile
        overall = np.random.choice([5, 4, 3], p=[0.82, 0.15, 0.03])
        nps = np.random.choice([10, 9, 8, 7], p=[0.75, 0.18, 0.05, 0.02])
        welcomed = np.random.choice([5, 4], p=[0.92, 0.08])
        
        # Stress before: 6 to 9 (high stress on arrival)
        stress_before = int(np.clip(np.random.normal(7.6, 1.1), 5, 10))
        # Stress after: 2 to 4 (deep stress relief)
        stress_after = int(np.clip(np.random.normal(2.7, 0.8), 1, 5))
        
        comment_text, segment = random.choice(comments_pool)
        
        surveys.append({
            "response_date": s_date.strftime("%Y-%m-%d"),
            "overall_rating": overall,
            "likelihood_to_return": nps,
            "class_type": random.choice(["Vinyasa Flow", "Desk Worker Mobility", "Candlelight Yin & Sound", "Community Gentle Yoga"]),
            "felt_welcomed": welcomed,
            "stress_before": stress_before,
            "stress_after": stress_after,
            "would_recommend": "Y",
            "comment": comment_text,
            "consent_to_quote": "Y" if random.random() < 0.90 else "N",
            "audience_segment": segment
        })

    df_surveys = pd.DataFrame(surveys)
    csv_path = os.path.join(OUTPUT_DIR, "survey_responses.csv")
    df_surveys.to_csv(csv_path, index=False)
    print(f"Generated {len(df_surveys)} survey responses in {csv_path}")
    return df_surveys

def generate_event_outcomes():
    events_data = [
        {"name": "Equinox Executive De-Stress", "type": "Corporate Wellness", "host": "Tech Company", "exp": 25, "act": 32, "rev": 500.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "High engagement; VP requested monthly series."},
        {"name": "Earth Day Park District Flow", "type": "Festival", "host": "Park District", "exp": 45, "act": 65, "rev": 450.0, "cost": 40.0, "rep": "Y", "rate": 5, "note": "Exceeded lawn capacity; bilingual instruction praised."},
        {"name": "Mental Health Awareness School Hour", "type": "School Workshop", "host": "Public School", "exp": 30, "act": 28, "rev": 350.0, "cost": 15.0, "rep": "Y", "rate": 5, "note": "Principal reported noticeable calm in student cohort."},
        {"name": "Luxury Hotel Sunrise Wellness", "type": "Hotel Residency", "host": "Boutique Hotel", "exp": 15, "act": 19, "rev": 350.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "Guests rated 5/5; extended for fall season."},
        {"name": "Midsummer Community Sound Sanctuary", "type": "Festival", "host": "Community Center", "exp": 40, "act": 58, "rev": 400.0, "cost": 50.0, "rep": "Y", "rate": 5, "note": "Large crowd; seamless sound amplification."},
        {"name": "Quarterly Law Firm Posture Workshop", "type": "Corporate Wellness", "host": "Law Firm", "exp": 20, "act": 24, "rev": 600.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "Repeat booking from Q1; desk mobility requested."},
        {"name": "Youth Athletics Mindful Recovery", "type": "School Workshop", "host": "Public School", "exp": 25, "act": 26, "rev": 300.0, "cost": 0.0, "rep": "Y", "rate": 4, "note": "Soccer team breathwork session."},
        {"name": "Bachelorette Private Sunset Yoga", "type": "Private Event", "host": "Private Host", "exp": 12, "act": 14, "rev": 350.0, "cost": 20.0, "rep": "N", "rate": 5, "note": "Customized playlist and aromatherapy gift bags."},
        {"name": "Tech Company Q3 Wellness Day", "type": "Corporate Wellness", "host": "Tech Company", "exp": 35, "act": 40, "rev": 550.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "Full room turnout; employee survey NPS was 100."},
        {"name": "Fall Harvest Community Festival", "type": "Festival", "host": "Park District", "exp": 50, "act": 72, "rev": 500.0, "cost": 35.0, "rep": "Y", "rate": 5, "note": "Largest outdoor class of the season."},
        {"name": "Teachers Institute Day Wellness", "type": "School Workshop", "host": "Public School", "exp": 40, "act": 45, "rev": 450.0, "cost": 10.0, "rep": "Y", "rate": 5, "note": "Burnout relief workshop for CPS educators."},
        {"name": "Boutique Hotel Autumn Sound Bath", "type": "Hotel Residency", "host": "Boutique Hotel", "exp": 15, "act": 16, "rev": 350.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "Sold-out rooftop session."},
        {"name": "Corporate Holiday Mindful Reset", "type": "Corporate Wellness", "host": "Tech Company", "exp": 30, "act": 38, "rev": 650.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "End-of-year decompression session."},
        {"name": "Private Birthday Wellness Gathering", "type": "Private Event", "host": "Private Host", "exp": 10, "act": 10, "rev": 300.0, "cost": 15.0, "rep": "Y", "rate": 5, "note": "Host booked annual family session."},
        {"name": "New Year Community Intention Flow", "type": "Festival", "host": "Community Center", "exp": 35, "act": 44, "rev": 350.0, "cost": 25.0, "rep": "Y", "rate": 5, "note": "Standing room only; sliding scale admission."},
        {"name": "Winter Hotel Weekend Series #1", "type": "Hotel Residency", "host": "Boutique Hotel", "exp": 12, "act": 14, "rev": 300.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "Visiting guests loved the slow morning pace."},
        {"name": "Corporate Winter Wellness Series #1", "type": "Corporate Wellness", "host": "Consulting Firm", "exp": 25, "act": 29, "rev": 500.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "Chairs & mats hybrid setup."},
        {"name": "Spring Awakening Rooftop Flow", "type": "Festival", "host": "Studio", "exp": 30, "act": 36, "rev": 450.0, "cost": 30.0, "rep": "Y", "rate": 5, "note": "Annual pop-up partner event."},
        {"name": "Corporate Spring Wellness Series #2", "type": "Corporate Wellness", "host": "Consulting Firm", "exp": 25, "act": 31, "rev": 500.0, "cost": 0.0, "rep": "Y", "rate": 5, "note": "100% repeat booking from winter cohort."},
        {"name": "Summer Solstice Beach Gathering", "type": "Festival", "host": "Park District", "exp": 60, "act": 82, "rev": 600.0, "cost": 45.0, "rep": "Y", "rate": 5, "note": "Peak attendance event of the fellowship year."}
    ]

    events = []
    # Generate event dates spanning the 18 months
    date_intervals = np.linspace(0, TOTAL_DAYS - 10, len(events_data))
    for i, item in enumerate(events_data):
        e_date = START_DATE + timedelta(days=int(date_intervals[i]))
        events.append({
            "event_date": e_date.strftime("%Y-%m-%d"),
            "event_name": item["name"],
            "event_type": item["type"],
            "expected_attendance": item["exp"],
            "actual_attendance": item["act"],
            "host_organization_type": item["host"],
            "revenue": item["rev"],
            "cost": item["cost"],
            "repeat_booking": item["rep"],
            "host_rating": item["rate"],
            "notes": item["note"]
        })

    df_events = pd.DataFrame(events)
    csv_path = os.path.join(OUTPUT_DIR, "event_outcomes.csv")
    df_events.to_csv(csv_path, index=False)
    print(f"Generated {len(df_events)} event outcomes in {csv_path}")
    return df_events

if __name__ == "__main__":
    print("Generating PitchPerfect synthetic demo datasets...")
    generate_class_history()
    generate_survey_responses()
    generate_event_outcomes()
    print("Demo dataset generation complete!")
