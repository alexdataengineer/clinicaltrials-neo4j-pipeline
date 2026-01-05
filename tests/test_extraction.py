"""Tests for route and dosage form extraction"""

import pytest

from src.pipeline.extract import (
    extract_route_and_dosage,
    normalize_dosage_form,
    normalize_route,
)


class TestNormalizeRoute:
    """Tests for route normalization."""

    def test_oral_route(self):
        """Test oral route detection."""
        assert normalize_route("oral administration") == "oral"
        assert normalize_route("PO") == "oral"
        assert normalize_route("by mouth") == "oral"

    def test_intravenous_route(self):
        """Test IV route detection."""
        assert normalize_route("intravenous injection") == "intravenous"
        assert normalize_route("IV") == "intravenous"
        assert normalize_route("i.v.") == "intravenous"

    def test_subcutaneous_route(self):
        """Test subcutaneous route detection."""
        assert normalize_route("subcutaneous injection") == "subcutaneous"
        assert normalize_route("SC") == "subcutaneous"
        assert normalize_route("sub-q") == "subcutaneous"

    def test_intramuscular_route(self):
        """Test intramuscular route detection."""
        assert normalize_route("intramuscular") == "intramuscular"
        assert normalize_route("IM") == "intramuscular"

    def test_topical_route(self):
        """Test topical route detection."""
        assert normalize_route("topical application") == "topical"
        assert normalize_route("topically") == "topical"

    def test_inhalation_route(self):
        """Test inhalation route detection."""
        assert normalize_route("inhalation") == "inhalation"
        assert normalize_route("inhaled") == "inhalation"
        assert normalize_route("inhaler") == "inhalation"

    def test_no_match(self):
        """Test cases with no route match."""
        assert normalize_route("unknown method") is None
        assert normalize_route("") is None
        assert normalize_route(None) is None

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert normalize_route("ORAL") == "oral"
        assert normalize_route("Intravenous") == "intravenous"


class TestNormalizeDosageForm:
    """Tests for dosage form normalization."""

    def test_tablet(self):
        """Test tablet detection."""
        assert normalize_dosage_form("tablet") == "tablet"
        assert normalize_dosage_form("tab") == "tablet"
        assert normalize_dosage_form("tablets") == "tablet"

    def test_capsule(self):
        """Test capsule detection."""
        assert normalize_dosage_form("capsule") == "capsule"
        assert normalize_dosage_form("cap") == "capsule"

    def test_solution(self):
        """Test solution detection."""
        assert normalize_dosage_form("solution") == "solution"
        assert normalize_dosage_form("sol") == "solution"

    def test_injection(self):
        """Test injection detection."""
        assert normalize_dosage_form("injection") == "injection"
        assert normalize_dosage_form("injectable") == "injection"

    def test_patch(self):
        """Test patch detection."""
        assert normalize_dosage_form("patch") == "patch"
        assert normalize_dosage_form("transdermal patch") == "patch"

    def test_no_match(self):
        """Test cases with no dosage form match."""
        assert normalize_dosage_form("unknown form") is None
        assert normalize_dosage_form("") is None
        assert normalize_dosage_form(None) is None


class TestExtractRouteAndDosage:
    """Tests for combined route and dosage extraction."""

    def test_both_present(self):
        """Test extraction when both route and dosage form are present."""
        route, dosage = extract_route_and_dosage("oral tablet")
        assert route == "oral"
        assert dosage == "tablet"

    def test_route_only(self):
        """Test extraction when only route is present."""
        route, dosage = extract_route_and_dosage("intravenous injection")
        assert route == "intravenous"
        assert dosage == "injection"

    def test_dosage_only(self):
        """Test extraction when only dosage form is present."""
        route, dosage = extract_route_and_dosage("capsule formulation")
        assert route is None
        assert dosage == "capsule"

    def test_neither_present(self):
        """Test extraction when neither is present."""
        route, dosage = extract_route_and_dosage("unknown intervention")
        assert route is None
        assert dosage is None

    def test_with_intervention_type(self):
        """Test extraction with intervention type."""
        route, dosage = extract_route_and_dosage(
            "oral tablet", intervention_type="Drug"
        )
        assert route == "oral"
        assert dosage == "tablet"

    def test_complex_description(self):
        """Test extraction from complex descriptions."""
        route, dosage = extract_route_and_dosage(
            "subcutaneous injection of monoclonal antibody"
        )
        assert route == "subcutaneous"
        assert dosage == "injection"

