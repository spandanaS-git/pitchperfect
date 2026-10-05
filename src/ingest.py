"""
src/ingest.py
Core Ingestion, Header Mapping, PII Scrubbing, and Validation Engine for PitchPerfect.
Meets ChiEAC Fellowship Week 2 / Gate 1 requirements.
"""

import hashlib
import io
import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Canonical schemas as defined in docs/data_schema_spec.md
CANONICAL_SCHEMAS = {
    "class_history": {
        "required": ["class_date", "class_time", "class_type", "capacity", "attended", "price"],
        "optional": ["format", "venue_type", "venue_name", "membership_type", "client_id", "first_visit", "zip"]
    },
    "survey_responses": {
        "required": ["response_date", "overall_rating", "likelihood_to_return"],
        "optional": ["class_type", "felt_welcomed", "stress_before", "stress_after", "would_recommend", "comment", "consent_to_quote", "audience_segment"]
    },
    "event_outcomes": {
        "required": ["event_date", "event_name", "event_type", "expected_attendance", "actual_attendance"],
        "optional": ["host_organization_type", "revenue", "cost", "repeat_booking", "host_rating", "notes"]
    }
}

# Vendor presets for automated header mapping
VENDOR_PRESETS: Dict[str, Dict[str, List[str]]] = {
    "class_history": {
        "class_date": ["date", "class date", "session date", "booking date", "event date", "start date", "day"],
        "class_time": ["time", "start time", "class time", "session time", "hour"],
        "class_type": ["class name", "service", "class", "session type", "discipline", "item name", "activity", "title"],
        "capacity": ["capacity", "max capacity", "max attendees", "limit", "room capacity", "max students"],
        "attended": ["attendance", "checked in", "attended", "booked", "actual attendees", "total students", "headcount", "signed in", "clients"],
        "price": ["price", "rate", "fee", "ticket price", "drop-in rate", "amount", "cost per class", "price ($)"],
        "venue_type": ["venue type", "location type", "category", "setting"],
        "venue_name": ["venue", "location", "studio", "facility", "room", "venue name"],
        "format": ["format", "delivery", "class format"],
        "client_id": ["client id", "member id", "customer id", "user id", "student id", "attendee id"],
        "first_visit": ["first visit", "is new", "first time", "new student", "first visit (y/n)"]
    },
    "survey_responses": {
        "response_date": ["timestamp", "submission date", "date", "created at", "submitted on", "time submitted"],
        "overall_rating": ["overall rating", "rating", "score", "experience rating", "how was class", "satisfaction", "overall experience"],
        "likelihood_to_return": ["nps", "likelihood to return", "recommend score", "return likelihood", "how likely", "net promoter"],
        "stress_before": ["stress before", "arrival stress", "pre stress", "stress level before", "starting stress"],
        "stress_after": ["stress after", "departure stress", "post stress", "stress level after", "ending stress"],
        "felt_welcomed": ["welcomed", "felt welcomed", "inclusion score", "belonging", "did you feel welcomed", "inclusive"],
        "comment": ["comment", "feedback", "testimonial", "thoughts", "what did you appreciate", "notes", "review"],
        "consent_to_quote": ["consent", "permission to quote", "may we quote", "quote consent", "allow quote", "permission"]
    },
    "event_outcomes": {
        "event_date": ["date", "event date", "date held", "start date"],
        "event_name": ["event", "event title", "workshop name", "program name", "workshop", "title"],
        "event_type": ["type", "event category", "category", "event type"],
        "expected_attendance": ["expected", "target attendance", "committed headcount", "rsvp count", "target"],
        "actual_attendance": ["actual", "total attendance", "turnout", "attended", "actual attendees"],
        "host_organization_type": ["client type", "host type", "organization", "industry", "host category"],
        "revenue": ["revenue", "gross revenue", "payment", "total pay", "earnings"],
        "repeat_booking": ["repeat", "repeat booking", "booked again", "rebooked", "follow up contract"],
        "host_rating": ["host rating", "organizer rating", "client satisfaction", "host score"]
    }
}

# Known PII column patterns to immediately drop
PII_COLUMN_PATTERNS = [
    r".*(?:student|client|customer|attendee|user|member|participant|person).*(?:name).*",
    r".*(?:first|last|full|sur).?name.*",
    r"^name$",
    r".*email.*",
    r".*phone.*",
    r".*telephone.*",
    r".*mobile.*",
    r".*address.*",
    r".*street.*",
    r".*credit.?card.*",
    r".*ssn.*",
    r".*(?:birth.?date|dob).*"
]

def load_file_to_df(file_bytes_or_path: Any, filename: str) -> pd.DataFrame:
    """Loads a CSV or Excel file safely into a Pandas DataFrame."""
    try:
        if filename.endswith(".csv"):
            if hasattr(file_bytes_or_path, "read"):
                file_bytes_or_path.seek(0)
            return pd.read_csv(file_bytes_or_path)
        elif filename.endswith((".xlsx", ".xls")):
            if hasattr(file_bytes_or_path, "read"):
                file_bytes_or_path.seek(0)
            return pd.read_excel(file_bytes_or_path)
        else:
            raise ValueError(f"Unsupported file format: {filename}. Please upload a .csv or .xlsx file.")
    except Exception as e:
        raise ValueError(f"Error reading file '{filename}': {str(e)}")

def scrub_pii_and_hash_clients(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Strips any detected PII columns and hashes client_id values with SHA-256.
    Returns cleaned DataFrame and list of dropped PII column names.
    """
    df_clean = df.copy()
    dropped_columns = []

    # Identify and drop PII columns (preserving business names like venue_name, event_name, class_type)
    preserve_exceptions = {"client_id", "venue_name", "event_name", "class_name", "item_name", "workshop_name", "class_type"}
    for col in list(df_clean.columns):
        col_normalized = str(col).strip().lower().replace(" ", "_")
        if col_normalized in preserve_exceptions:
            continue
        for pattern in PII_COLUMN_PATTERNS:
            if re.fullmatch(pattern, col_normalized):
                df_clean.drop(columns=[col], inplace=True)
                dropped_columns.append(str(col))
                break

    # Anonymize / Hash client_id if present
    if "client_id" in df_clean.columns:
        def hash_id(val):
            if pd.isna(val) or val is None or str(val).strip() == "":
                return "usr_anon"
            s = str(val).strip().encode("utf-8")
            h = hashlib.sha256(s).hexdigest()[:8]
            return f"usr_{h}"
        df_clean["client_id"] = df_clean["client_id"].apply(hash_id)

    return df_clean, dropped_columns

def auto_map_headers(df: pd.DataFrame, file_type: str) -> Dict[str, str]:
    """
    Maps uploaded headers to canonical schema names using vendor presets.
    Returns a dict of {canonical_column: uploaded_column}.
    """
    mapping = {}
    preset = VENDOR_PRESETS.get(file_type, {})
    col_lookup = {str(c).strip().lower().replace("_", " "): str(c) for c in df.columns}

    for canonical, variations in preset.items():
        # Exact match first
        if canonical in df.columns:
            mapping[canonical] = canonical
            continue
        
        # Check variations
        found = False
        for var in variations:
            if var in col_lookup:
                mapping[canonical] = col_lookup[var]
                found = True
                break
        if not found:
            # Substring match fallback
            for col_clean, original_col in col_lookup.items():
                if any(var == col_clean or var in col_clean for var in variations):
                    mapping[canonical] = original_col
                    break

    return mapping

def apply_header_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """Renames uploaded columns to canonical column names."""
    # Invert mapping: {uploaded_col: canonical_col}
    reverse_map = {v: k for k, v in mapping.items() if v in df.columns}
    return df.rename(columns=reverse_map)

def validate_class_history(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates class_history DataFrame against schema and business rules."""
    errors = []
    warnings = []
    required = CANONICAL_SCHEMAS["class_history"]["required"]

    # 1. Required column check
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return {"valid": False, "errors": errors, "warnings": warnings, "row_count": len(df)}

    # 2. Row count check
    if len(df) == 0:
        errors.append("File is empty (0 rows).")
        return {"valid": False, "errors": errors, "warnings": warnings, "row_count": 0}

    # 3. Numeric conversions & value checks
    try:
        df["capacity"] = pd.to_numeric(df["capacity"], errors="coerce")
        df["attended"] = pd.to_numeric(df["attended"], errors="coerce")
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
    except Exception as e:
        errors.append(f"Numeric conversion error: {str(e)}")

    invalid_cap = df[df["capacity"] <= 0]
    if len(invalid_cap) > 0:
        errors.append(f"{len(invalid_cap)} rows have invalid capacity (must be > 0).")

    invalid_att = df[df["attended"] < 0]
    if len(invalid_att) > 0:
        errors.append(f"{len(invalid_att)} rows have negative attendance.")

    # Overcapacity warnings (allowed for standing room/outdoor, but flagged)
    overcap = df[df["attended"] > df["capacity"]]
    if len(overcap) > 0:
        warnings.append(f"{len(overcap)} classes exceeded room capacity (standing room / overflow).")

    # Date parsing check
    try:
        dates = pd.to_datetime(df["class_date"], errors="coerce")
        null_dates = dates.isna().sum()
        if null_dates > 0:
            errors.append(f"{null_dates} rows have invalid or unreadable dates.")
    except Exception:
        errors.append("Could not parse 'class_date' column as dates.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(df),
        "unique_venues": df["venue_name"].nunique() if "venue_name" in df.columns else None,
        "date_min": df["class_date"].min(),
        "date_max": df["class_date"].max()
    }

def validate_survey_responses(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates survey_responses DataFrame against schema and business rules."""
    errors = []
    warnings = []
    required = CANONICAL_SCHEMAS["survey_responses"]["required"]

    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return {"valid": False, "errors": errors, "warnings": warnings, "row_count": len(df)}

    if len(df) == 0:
        errors.append("File is empty (0 rows).")
        return {"valid": False, "errors": errors, "warnings": warnings, "row_count": 0}

    # Range checks
    df["overall_rating"] = pd.to_numeric(df["overall_rating"], errors="coerce")
    df["likelihood_to_return"] = pd.to_numeric(df["likelihood_to_return"], errors="coerce")

    out_of_bounds_ratings = df[(df["overall_rating"] < 1) | (df["overall_rating"] > 5)]
    if len(out_of_bounds_ratings) > 0:
        errors.append(f"{len(out_of_bounds_ratings)} ratings outside 1-5 scale.")

    out_of_bounds_nps = df[(df["likelihood_to_return"] < 0) | (df["likelihood_to_return"] > 10)]
    if len(out_of_bounds_nps) > 0:
        errors.append(f"{len(out_of_bounds_nps)} likelihood scores outside 0-10 scale.")

    # Stress delta check (if present)
    if "stress_before" in df.columns and "stress_after" in df.columns:
        df["stress_before"] = pd.to_numeric(df["stress_before"], errors="coerce")
        df["stress_after"] = pd.to_numeric(df["stress_after"], errors="coerce")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(df),
        "avg_rating": round(float(df["overall_rating"].mean()), 2) if "overall_rating" in df.columns else None,
        "consent_to_quote_count": int((df["consent_to_quote"].str.upper() == "Y").sum()) if "consent_to_quote" in df.columns else 0
    }

def validate_event_outcomes(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates event_outcomes DataFrame against schema and business rules."""
    errors = []
    warnings = []
    required = CANONICAL_SCHEMAS["event_outcomes"]["required"]

    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return {"valid": False, "errors": errors, "warnings": warnings, "row_count": len(df)}

    if len(df) == 0:
        errors.append("File is empty (0 rows).")
        return {"valid": False, "errors": errors, "warnings": warnings, "row_count": 0}

    df["expected_attendance"] = pd.to_numeric(df["expected_attendance"], errors="coerce")
    df["actual_attendance"] = pd.to_numeric(df["actual_attendance"], errors="coerce")

    invalid_att = df[(df["expected_attendance"] < 0) | (df["actual_attendance"] < 0)]
    if len(invalid_att) > 0:
        errors.append("Event attendance numbers cannot be negative.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(df),
        "total_actual_attendees": int(df["actual_attendance"].sum()),
        "event_types": df["event_type"].unique().tolist() if "event_type" in df.columns else []
    }
