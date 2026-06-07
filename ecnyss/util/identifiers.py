"""Identifier generation and validation utilities for ecnyss.

Pure stdlib implementation of UUID, short ID, and ULID generation.
"""

import uuid
import base64
import time
import secrets
import re
from typing import Optional


# Crockford base32 alphabet (no I, L, O, U to avoid ambiguity)
CROCKFORD_BASE32 = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'


def generate_uuid4() -> str:
    """Generate a random UUID4 string.
    
    Returns:
        A 36-character UUID4 string in standard format with hyphens.
    """
    return str(uuid.uuid4())


def generate_uuid5(namespace: uuid.UUID, name: str) -> str:
    """Generate a deterministic UUID5 string.
    
    Args:
        namespace: A UUID namespace (e.g., uuid.NAMESPACE_DNS).
        name: The name to hash within the namespace.
    
    Returns:
        A 36-character UUID5 string in standard format with hyphens.
    """
    return str(uuid.uuid5(namespace, name))


def generate_short_id(length: int = 12) -> str:
    """Generate a short, URL-safe random identifier.
    
    Args:
        length: Desired length of the identifier (default 12).
    
    Returns:
        A URL-safe base64-encoded random string of specified length.
    """
    if length <= 0:
        return ''
    
    # Generate enough random bytes to cover the requested length
    # URL-safe base64 uses 6 bits per character, so we need ceil(length * 6 / 8) bytes
    num_bytes = (length * 6 + 7) // 8
    random_bytes = secrets.token_bytes(num_bytes)
    
    # Encode as URL-safe base64 and remove padding
    encoded = base64.urlsafe_b64encode(random_bytes).decode('ascii').rstrip('=')
    
    # Return exactly the requested length
    return encoded[:length]


def _encode_base32(value: int, length: int) -> str:
    """Encode an integer as Crockford base32 string.
    
    Args:
        value: The integer value to encode.
        length: The desired length of the output string.
    
    Returns:
        A Crockford base32 encoded string of specified length.
    """
    result = []
    for _ in range(length):
        result.append(CROCKFORD_BASE32[value & 0x1F])
        value >>= 5
    return ''.join(reversed(result))


def generate_ulid() -> str:
    """Generate a ULID (Universally Unique Lexicographically Sortable Identifier).
    
    ULID format:
    - 48 bits for timestamp (milliseconds since Unix epoch)
    - 80 bits for random data
    - Total: 128 bits encoded as 26 Crockford base32 characters
    
    Returns:
        A 26-character ULID string.
    """
    # Get current time in milliseconds
    timestamp_ms = int(time.time() * 1000)
    
    # Encode timestamp as 10 base32 characters (48 bits)
    timestamp_part = _encode_base32(timestamp_ms, 10)
    
    # Generate 80 bits (10 bytes) of random data
    random_bytes = secrets.token_bytes(10)
    
    # Encode random data as 16 base32 characters (80 bits)
    random_value = int.from_bytes(random_bytes, 'big')
    random_part = _encode_base32(random_value, 16)
    
    return timestamp_part + random_part


def is_valid_uuid(uuid_str: Optional[str], version: Optional[int] = None) -> bool:
    """Validate a UUID string.
    
    Args:
        uuid_str: The UUID string to validate.
        version: Optional version number to check (1-5).
    
    Returns:
        True if the string is a valid UUID, False otherwise.
    """
    if uuid_str is None or not isinstance(uuid_str, str):
        return False
    
    # Remove hyphens for validation
    uuid_clean = uuid_str.replace('-', '')
    
    # Check length (32 hex characters)
    if len(uuid_clean) != 32:
        return False
    
    # Check all characters are valid hex
    if not re.match(r'^[0-9a-fA-F]{32}$', uuid_clean):
        return False
    
    # If version check requested, parse and verify
    if version is not None:
        try:
            u = uuid.UUID(uuid_str)
            return u.version == version
        except (ValueError, AttributeError):
            return False
    
    return True


def shorten_uuid(uuid_str: str, length: int = 8) -> str:
    """Shorten a UUID to a specified length.
    
    Args:
        uuid_str: The UUID string to shorten.
        length: The desired length of the output (default 8).
    
    Returns:
        The shortened UUID string without hyphens.
    
    Raises:
        ValueError: If the input is not a valid UUID.
    """
    if not is_valid_uuid(uuid_str):
        raise ValueError(f"Invalid UUID: {uuid_str}")
    
    # Remove hyphens
    uuid_clean = uuid_str.replace('-', '')
    
    # Return the prefix of specified length
    return uuid_clean[:length]
