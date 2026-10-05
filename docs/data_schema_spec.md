# PitchPerfect: Data Schema Specification (v1.0)
**Chicago Education Advocacy Cooperative (ChiEAC) Fellowship**  
*Author:* ChiEAC Fellow  
*Date:* October 5, 2026  

---

## 1. Overview
PitchPerfect ingests up to three user-uploaded tabular files (`.csv` or `.xlsx`) and one in-app profile form to compute evidence cards and pitch kits. All files are processed client-side/in session memory. No personally identifiable information (PII) is stored.

---

## 2. File Specifications

### 2.1 File 1: `class_history`
Tracks regular class offerings, attendance, capacity, and scheduling consistency.

| Column Name | Required / Optional | Data Type | Description & Allowed Values | Example |
| :--- | :--- | :--- | :--- | :--- |
| `class_date` | **Required** | Date (`YYYY-MM-DD`) | Date the class was held or scheduled. | `2026-05-12` |
| `class_time` | **Required** | Time (`HH:MM` 24h or 12h) | Scheduled start time of the class. | `12:00` or `07:30 AM` |
| `class_type` | **Required** | String | Discipline or format (e.g., Vinyasa, Yin, HIIT, Breathwork, Mat Pilates). | `Vinyasa Yoga` |
| `capacity` | **Required** | Integer | Room/session maximum capacity ($> 0$). | `25` |
| `attended` | **Required** | Integer | Actual checked-in participant count ($\ge 0$). | `22` |
| `price` | **Required** | Float | Drop-in or listed single-class ticket price ($\ge 0$). | `20.00` |
| `format` | Optional | String | `In-person`, `Online`, `Hybrid`. Defaults to `In-person`. | `In-person` |
| `venue_type` | Optional | String | `Studio`, `Park District`, `Corporate`, `Gym`, `Community Center`, `Home`. | `Studio` |
| `venue_name` | Optional | String | Name of studio or location. | `Bloom Yoga Studio` |
| `membership_type` | Optional | String | `Drop-in`, `Monthly Member`, `ClassPass`, `Scholarship/Sliding Scale`. | `Drop-in` |
| `client_id` | Optional | String / Hash | Anonymized user identifier (hashed on ingestion to preserve streaks). | `usr_a89f3b` |
| `first_visit` | Optional | Boolean / String | `Y`/`N` or `True`/`False`. Denotes if this was the attendee's first class. | `Y` |
| `zip` | Optional | String | ZIP code of venue for geography analysis. | `60647` |

---

### 2.2 File 2: `survey_responses`
Participant post-class feedback capturing satisfaction, psychological outcomes, and quotes.

| Column Name | Required / Optional | Data Type | Description & Allowed Values | Example |
| :--- | :--- | :--- | :--- | :--- |
| `response_date` | **Required** | Date (`YYYY-MM-DD`) | Date survey was submitted. | `2026-06-15` |
| `overall_rating` | **Required** | Integer (1 to 5) | Overall class experience (Likert scale 1–5). | `5` |
| `likelihood_to_return`| **Required** | Integer (0 to 10) | Net Promoter Score question: Likelihood to return/recommend (0–10). | `10` |
| `class_type` | Optional | String | Style of class attended. | `Sound Bath & Flow` |
| `felt_welcomed` | Optional | Integer (1 to 5) | Accessibility and inclusion indicator (1 = Not at all, 5 = Extremely). | `5` |
| `stress_before` | Optional | Integer (1 to 10) | Self-reported stress level upon arrival (1 = Calm, 10 = High stress). | `8` |
| `stress_after` | Optional | Integer (1 to 10) | Self-reported stress level upon departure (1 = Calm, 10 = High stress). | `3` |
| `would_recommend` | Optional | Boolean / String | `Y`/`N` or `True`/`False`. Would recommend instructor to peers. | `Y` |
| `comment` | Optional | Text | Qualitative participant reflection or feedback. | *"Mariana's cues made me feel completely at ease."* |
| `consent_to_quote` | Optional | Boolean / String | `Y`/`N`. User gave explicit consent for quote to appear in pitches. | `Y` |
| `audience_segment` | Optional | String | `Beginner`, `Intermediate`, `Desk Worker`, `Youth`, `Senior`, `Athlete`. | `Desk Worker` |

---

### 2.3 File 3: `event_outcomes`
Workshops, retreats, corporate pop-ups, festivals, and special single-day events.

| Column Name | Required / Optional | Data Type | Description & Allowed Values | Example |
| :--- | :--- | :--- | :--- | :--- |
| `event_date` | **Required** | Date (`YYYY-MM-DD`) | Date event was held. | `2026-08-20` |
| `event_name` | **Required** | String | Name or title of event. | `Mindful Mobility Lunch & Learn` |
| `event_type` | **Required** | String | `Corporate Wellness`, `Festival`, `Hotel Residency`, `School Workshop`, `Retreat`. | `Corporate Wellness` |
| `expected_attendance`| **Required** | Integer | Headcount committed or targeted by host. | `30` |
| `actual_attendance` | **Required** | Integer | Actual participants engaged. | `38` |
| `host_organization_type` | Optional | String | `Tech Company`, `Non-Profit`, `Public School`, `Boutique Hotel`, `Park District`. | `Tech Company` |
| `revenue` | Optional | Float | Total gross pay for event. | `350.00` |
| `cost` | Optional | Float | Associated direct costs (rent, materials). | `25.00` |
| `repeat_booking` | Optional | Boolean / String | `Y`/`N`. Host booked a subsequent session. | `Y` |
| `host_rating` | Optional | Integer (1 to 5) | Host organizer evaluation of the instructor. | `5` |
| `notes` | Optional | Text | General observations or logistical takeaways. | `Contract extended for Q4.` |

---

## 3. Instructor Profile Form (In-App Fields)
Captured via an in-app form (not a CSV upload):
* `name`: Instructor full name as it should appear in pitch headers.
* `disciplines`: Primary disciplines taught (e.g., *Hatha Yoga, Breathwork, Yin*).
* `years_teaching`: Total years of active teaching.
* `certifications`: Professional credentials (e.g., *RYT-500, NASM-CPT, Trauma-Informed Yoga*).
* `liability_insurance`: `True` / `False` (insurance on file).
* `background_check`: `True` / `False` (active background check on file).
* `languages`: Languages instruction is available in (e.g., *English, Spanish*).
* `availability_windows`: General availability tags (`Early Morning (6-9 AM)`, `Lunchtime (11 AM-1 PM)`, `Evening (5-8 PM)`, `Weekend Mornings`).
* `service_radius`: Travel distance in miles from home ZIP code.
* `sliding_scale_policy`: `True` / `False` (offers equitable or community pricing).

---

## 4. Built-in Participant Survey Template
Instructors who lack survey data can deploy this 7-question survey via Google Forms or Typeform:

1. **Date of class:** [Date picker]
2. **Class style/session:** [Short answer or dropdown]
3. **How would you rate today's overall class experience?** (1 = Poor, 5 = Exceptional)
4. **How likely are you to attend another class with this instructor?** (0 = Not likely, 10 = Extremely likely)
5. **How did you feel your stress level change?**
   - Stress before class (1 = Completely relaxed, 10 = Maximum stress)
   - Stress after class (1 = Completely relaxed, 10 = Maximum stress)
6. **Did you feel welcomed, included, and safe in the space?** (1 = Strongly disagree, 5 = Strongly agree)
7. **What is one thing you appreciated most about the instructor?** [Paragraph text]
8. **May we quote your feedback anonymously in future program proposals?** [Yes / No]

---

## 5. Vendor Header Mapping Dictionary
The Header Mapper normalizes common vendor export column headers into PitchPerfect canonical columns:

```json
{
  "class_history": {
    "class_date": ["date", "class date", "session date", "booking date", "event date"],
    "class_time": ["time", "start time", "class time", "session time"],
    "class_type": ["class name", "service", "class", "session type", "discipline", "item name"],
    "capacity": ["capacity", "max capacity", "max attendees", "limit", "room capacity"],
    "attended": ["attendance", "checked in", "attended", "booked", "actual attendees", "total students", "headcount"],
    "price": ["price", "rate", "fee", "ticket price", "drop-in rate", "amount"]
  },
  "survey_responses": {
    "response_date": ["timestamp", "submission date", "date", "created at"],
    "overall_rating": ["overall rating", "rating", "score", "experience rating", "how was class"],
    "likelihood_to_return": ["nps", "likelihood to return", "recommend score", "return likelihood", "how likely"],
    "stress_before": ["stress before", "arrival stress", "pre stress"],
    "stress_after": ["stress after", "departure stress", "post stress"],
    "felt_welcomed": ["welcomed", "felt welcomed", "inclusion score", "belonging"],
    "comment": ["comment", "feedback", "testimonial", "thoughts", "what did you appreciate"],
    "consent_to_quote": ["consent", "permission to quote", "may we quote", "quote consent"]
  },
  "event_outcomes": {
    "event_date": ["date", "event date", "date held"],
    "event_name": ["event", "event title", "workshop name", "program name"],
    "event_type": ["type", "event category", "category"],
    "expected_attendance": ["expected", "target attendance", "committed headcount", "rsvp count"],
    "actual_attendance": ["actual", "total attendance", "turnout", "attended"],
    "host_organization_type": ["client type", "host type", "organization", "industry"]
  }
}
```
