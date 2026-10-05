# PitchPerfect: Turn Teaching Data into Partnership Pitches

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Framework: Streamlit](https://img.shields.io/badge/framework-Streamlit-red.svg)](https://streamlit.io)
[![Organization: ChiEAC](https://img.shields.io/badge/fellowship-ChiEAC-green.svg)](https://chieac.org)

> **A free-to-try web app where yoga, fitness, dance, meditation, and wellness instructors upload their class history, survey results, and event outcomes, and receive customized, evidence-backed pitch kits for seven opportunity types.**

---

## 🎯 The Core Problem
Instead of an instructor sending a cold email saying *"I teach yoga,"* how can they show a decision-maker exactly what they offer, who has responded to it, and why it fits this specific opportunity?

Most movement and wellness instructors are independent contractors piecing together work across multiple studios, corporate offices, and community centers. The teachers who win residencies and corporate contracts are often those with marketing budgets or sales experience—not necessarily the most effective teachers. 

**PitchPerfect closes that gap.** It reads the data an instructor already has (attendance logs, survey feedback, workshop outcomes), computes proof points decision-makers care about, and assembles tailored, evidence-backed pitch kits. Every claim traces directly back to an **Evidence Card**, never from invention.

---

## 🏛️ The 7 Opportunity Types

| Opportunity | What the Decision-Maker Cares About | Evidence PitchPerfect Leads With |
| :--- | :--- | :--- |
| **Studio Residency** | Fill rates, recurring attendance, following | Fill rate, 30-day retention curve, first-to-second class conversion, class volume. |
| **Corporate Wellness** | Measurable employee stress reduction, workday fit | Pre/post stress delta, recommend rate, lunchtime availability, liability insurance. |
| **Community Organization** | Inclusivity, affordability, cultural trust | "Felt welcomed" score, sliding-scale policy, repeat participation, local venue history. |
| **School / Youth** | Safety, trauma-informed care, group management | Background check, liability insurance, youth experience, classroom group sizes. |
| **Festival / Pop-up** | Commanding large outdoor crowds, draw | Peak class sizes handled, attendance vs. expectations, energy ratings. |
| **Hotel / Luxury Resort** | Guest elevation, early-morning flexibility | Early morning availability, 5-star guest reviews, drop-in engagement. |
| **Private Event / Retreat** | Memorable customization, clear rates | Repeat bookings, host ratings, customizable offerings, transparent pricing card. |

---

## 📦 What the App Outputs
1. **Pitch Strength Scorecard (0–100):** Rates how ready the instructor is to pitch each of the 7 opportunity types.
2. **Gap Plan:** Tells the instructor what data to collect next (e.g., *"Collect 15 more surveys to unlock corporate wellness"*).
3. **Pitch Kits:** A 1-page proposal (DOCX and PDF), a tailored cold email draft, and an evidence appendix with interactive Plotly charts.
4. **Evidence Card Export:** Downloadable JSON and Excel file containing all verified stats for bios and grant applications.

---

## 🛡️ Guardrails & Privacy
* **Evidence-Traceability Rule:** The narrative generator is strictly constrained. An automated numeric validator matches every figure against the Evidence Card set; unverified claims are rejected and revert to a safe template.
* **Zero PII (Privacy):** No client names required. Client IDs are hashed upon ingestion.
* **No Persistence:** Files live in session memory only and are discarded after use.
* **No Web Scraping:** Only user-uploaded files or canonical public demo datasets are processed.

---

## 🚀 Quickstart

### 1. Clone & Install
```bash
git clone https://github.com/spandanaS-git/pitchperfect.git
cd pitchperfect
pip install -r requirements.txt
```

### 2. Generate Synthetic Demo Data (18 Months)
```bash
python scripts/generate_demo_data.py
```
This generates reproducible demo files in `data/demo/`:
* `class_history.csv` (~600 classes)
* `survey_responses.csv` (150 responses)
* `event_outcomes.csv` (20 events)

### 3. Run the App
```bash
streamlit run src/app.py
```

---

## 📂 Repository Structure
```
pitchperfect/
├── config/
│   └── taxonomy.yaml             # Definitions, weights, and criteria for 7 opportunity types
├── data/
│   ├── demo/                     # Generated 18-month synthetic dataset
│   └── templates/                # Downloadable CSV templates for instructors
├── docs/
│   ├── data_schema_spec.md       # Input column specifications & vendor header mapping
│   └── discovery_interviews.md   # Week 1 discovery interview synthesis
├── scripts/
│   └── generate_demo_data.py     # Reproducible Faker + NumPy demo data generator
├── src/                          # Application source code (Streamlit, evidence engine, validator)
├── tests/                        # Automated unit tests with pytest
├── LICENSE                       # MIT License
├── README.md
└── requirements.txt              # Project dependencies
```

---

## 👥 Fellowship Acknowledgments
Prepared for the **Chicago Education Advocacy Cooperative (ChiEAC)**  
Supervisor: **Dr. Benjamin M. Drury**, Founder & Executive Director (`benjamin@chieac.org`)  
Fellow: **ChiEAC Fellow**  
Project Window: October 2026 – November 2026
