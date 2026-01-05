"""Tests for normalization functions"""

import pytest

from src.utils.hashing import generate_stable_id, normalize_string


class TestNormalizeString:
    """Tests for string normalization."""

    def test_basic_normalization(self):
        """Test basic normalization."""
        assert normalize_string("  Hello World  ") == "hello world"
        assert normalize_string("HELLO   WORLD") == "hello world"
        assert normalize_string("Hello\t\nWorld") == "hello world"

    def test_empty_strings(self):
        """Test empty and None inputs."""
        assert normalize_string("") == ""
        assert normalize_string("   ") == ""
        assert normalize_string(None) == ""

    def test_special_characters(self):
        """Test handling of special characters."""
        assert normalize_string("Test-String") == "test-string"
        assert normalize_string("Test_String") == "test_string"
        assert normalize_string("Test.String") == "test.string"

    def test_case_insensitive(self):
        """Test case normalization."""
        assert normalize_string("Pfizer") == "pfizer"
        assert normalize_string("PFIZER") == "pfizer"
        assert normalize_string("PfIzEr") == "pfizer"


class TestGenerateStableId:
    """Tests for stable ID generation."""

    def test_deterministic(self):
        """Test that same input produces same ID."""
        id1 = generate_stable_id("Test Organization")
        id2 = generate_stable_id("Test Organization")
        assert id1 == id2

    def test_different_inputs(self):
        """Test that different inputs produce different IDs."""
        id1 = generate_stable_id("Organization A")
        id2 = generate_stable_id("Organization B")
        assert id1 != id2

    def test_namespace(self):
        """Test namespace affects ID."""
        id1 = generate_stable_id("Test", namespace="org")
        id2 = generate_stable_id("Test", namespace="drug")
        assert id1 != id2

    def test_normalization(self):
        """Test that normalization is applied by default."""
        id1 = generate_stable_id("  Test  ")
        id2 = generate_stable_id("test")
        assert id1 == id2

    def test_without_normalization(self):
        """Test ID generation without normalization."""
        id1 = generate_stable_id("  Test  ", normalize=False)
        id2 = generate_stable_id("test", normalize=False)
        assert id1 != id2

    def test_hash_length(self):
        """Test that IDs are SHA1 hashes (40 chars)."""
        id1 = generate_stable_id("Test")
        assert len(id1) == 40
        assert all(c in "0123456789abcdef" for c in id1)

