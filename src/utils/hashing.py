"""Deterministic hashing utilities for generating stable IDs"""

import hashlib
from typing import Optional


def generate_stable_id(
    value: str,
    namespace: Optional[str] = None,
    normalize: bool = True,
) -> str:
    """
    Generate a stable, deterministic ID from a string value.

    Args:
        value: Input string to hash
        namespace: Optional namespace prefix
        normalize: Whether to normalize the value before hashing

    Returns:
        SHA1 hash hex string (40 characters)
    """
    if normalize:
        normalized = normalize_string(value)
    else:
        normalized = value

    if namespace:
        combined = f"{namespace}:{normalized}"
    else:
        combined = normalized

    # Generate SHA1 hash
    hash_obj = hashlib.sha1(combined.encode("utf-8"))
    return hash_obj.hexdigest()


def normalize_string(value: str) -> str:
    """
    Normalize a string for consistent hashing.

    - Strip whitespace
    - Collapse multiple spaces to single space
    - Convert to lowercase
    - Remove leading/trailing whitespace

    Args:
        value: Input string

    Returns:
        Normalized string
    """
    if not value or not isinstance(value, str):
        return ""

    # Convert to string, strip, and lowercase
    normalized = str(value).strip().lower()

    # Collapse multiple whitespace to single space
    import re

    normalized = re.sub(r"\s+", " ", normalized)

    return normalized

