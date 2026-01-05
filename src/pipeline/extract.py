"""Extraction utilities for route of administration and dosage form"""

import re
from typing import Dict, List, Optional, Tuple

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Route keywords (case-insensitive matching)
ROUTE_KEYWORDS = {
    "oral": ["oral", "po", "by mouth", "per os"],
    "intravenous": ["intravenous", "iv", "i.v.", "intra-venous"],
    "subcutaneous": ["subcutaneous", "sc", "s.c.", "sub-q", "subq"],
    "intramuscular": ["intramuscular", "im", "i.m."],
    "topical": ["topical", "topically"],
    "inhalation": ["inhalation", "inhaled", "inhaler", "nebulized"],
    "intranasal": ["intranasal", "nasal", "intra-nasal"],
    "ophthalmic": ["ophthalmic", "eye", "ocular", "ophthalmically"],
    "rectal": ["rectal", "rectally"],
    "transdermal": ["transdermal", "patch", "dermal"],
    "intraperitoneal": ["intraperitoneal", "ip", "i.p."],
    "intraarterial": ["intraarterial", "ia", "i.a."],
}

# Dosage form keywords
DOSAGE_FORM_KEYWORDS = {
    "tablet": ["tablet", "tab", "tablets"],
    "capsule": ["capsule", "cap", "capsules"],
    "solution": ["solution", "sol", "solutions"],
    "injection": ["injection", "injectable", "injections"],
    "suspension": ["suspension", "susp", "suspensions"],
    "patch": ["patch", "patches", "transdermal patch"],
    "cream": ["cream", "creams"],
    "gel": ["gel", "gels"],
    "spray": ["spray", "sprays"],
    "inhaler": ["inhaler", "inhalers", "puffer"],
    "drops": ["drops", "eye drops", "ear drops"],
    "powder": ["powder", "powders"],
    "lozenge": ["lozenge", "lozenges"],
    "suppository": ["suppository", "suppositories"],
}


def normalize_route(route: str) -> Optional[str]:
    """
    Normalize route of administration from text.

    Args:
        route: Input text containing route information

    Returns:
        Normalized route name or None if not found
    """
    if not route or not isinstance(route, str):
        return None

    route_lower = route.lower()

    # Check each route category
    for normalized_route, keywords in ROUTE_KEYWORDS.items():
        for keyword in keywords:
            # Handle abbreviations with periods specially (word boundaries don't work well with periods)
            if "." in keyword:
                # Match the abbreviation with optional period
                keyword_no_period = keyword.replace(".", "")
                # Pattern: word boundary, then the letters, then optional period, then word boundary or end
                pattern = r"\b" + re.escape(keyword_no_period) + r"\.?\b"
                if re.search(pattern, route_lower):
                    return normalized_route
                # Also try exact match
                if keyword == route_lower or keyword in route_lower.split():
                    return normalized_route
            else:
                # Standard word boundary match for keywords without periods
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, route_lower):
                    return normalized_route

    return None


def normalize_dosage_form(text: str) -> Optional[str]:
    """
    Normalize dosage form from text.

    Args:
        text: Input text containing dosage form information

    Returns:
        Normalized dosage form name or None if not found
    """
    if not text or not isinstance(text, str):
        return None

    text_lower = text.lower()

    # Check each dosage form category
    for normalized_form, keywords in DOSAGE_FORM_KEYWORDS.items():
        for keyword in keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, text_lower):
                return normalized_form

    return None


def extract_route_and_dosage(
    intervention_name: str, intervention_type: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract route of administration and dosage form from intervention data.

    This function uses heuristics to extract route and dosage form from
    intervention names and types. It's not perfect but provides reasonable
    coverage for common cases.

    Limitations:
    - May miss complex or uncommon routes/dosage forms
    - May produce false positives for partial word matches
    - Does not handle multi-route or multi-dosage form interventions
    - Trial-level aggregation (not arm-specific)

    Args:
        intervention_name: Name of the intervention
        intervention_type: Type of intervention (e.g., "Drug", "Biological")

    Returns:
        Tuple of (route, dosage_form) or (None, None) if not found
    """
    if not intervention_name:
        return None, None

    # Combine all text for extraction
    text = str(intervention_name)
    if intervention_type:
        text += " " + str(intervention_type)

    route = normalize_route(text)
    dosage_form = normalize_dosage_form(text)

    return route, dosage_form


def aggregate_trial_route_dosage(
    interventions_df, nct_id: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Aggregate route and dosage form for a trial from all its interventions.

    Takes the first non-null route and dosage form found across interventions.
    This is a pragmatic trial-level approach.

    Args:
        interventions_df: DataFrame with intervention data
        nct_id: NCT ID of the trial

    Returns:
        Tuple of (route, dosage_form) for the trial
    """
    trial_interventions = interventions_df[
        interventions_df["nct_id"] == nct_id
    ]

    routes = []
    dosage_forms = []

    for _, row in trial_interventions.iterrows():
        route, dosage_form = extract_route_and_dosage(
            row.get("intervention_name", ""),
            row.get("intervention_type", ""),
        )
        if route:
            routes.append(route)
        if dosage_form:
            dosage_forms.append(dosage_form)

    # Return first found (or None)
    trial_route = routes[0] if routes else None
    trial_dosage_form = dosage_forms[0] if dosage_forms else None

    return trial_route, trial_dosage_form

