"""Encoding/decoding utilities for ecnyss.

Provides pure-stdlib implementations of common encoding schemes:
- Base64 (standard and URL-safe)
- Hexadecimal
- Percent-encoding (RFC 3986)

All functions are deterministic, side-effect free, and use only stdlib.
"""

import base64
import binascii


# =============================================================================
# Base64 Encoding/Decoding
# =============================================================================

def b64_encode(data: bytes) -> str:
    """Encode bytes to standard base64 string.
    
    Args:
        data: Bytes to encode.
        
    Returns:
        Base64 encoded string with padding.
    """
    return base64.b64encode(data).decode('ascii')


def b64_decode(encoded: str) -> bytes:
    """Decode standard base64 string to bytes.
    
    Args:
        encoded: Base64 encoded string.
        
    Returns:
        Decoded bytes.
        
    Raises:
        ValueError: If the input is not valid base64.
    """
    try:
        return base64.b64decode(encoded, validate=True)
    except binascii.Error as e:
        raise ValueError(f"Invalid base64: {e}") from e


def b64url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string (no padding).
    
    Uses '-' instead of '+' and '_' instead of '/'.
    Padding characters '=' are removed.
    
    Args:
        data: Bytes to encode.
        
    Returns:
        URL-safe base64 encoded string without padding.
    """
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def b64url_decode(encoded: str) -> bytes:
    """Decode URL-safe base64 string to bytes.
    
    Handles missing padding by adding it back as needed.
    
    Args:
        encoded: URL-safe base64 encoded string (with or without padding).
        
    Returns:
        Decoded bytes.
        
    Raises:
        ValueError: If the input is not valid URL-safe base64.
    """
    # Add padding if needed
    padding_needed = 4 - (len(encoded) % 4)
    if padding_needed != 4:
        encoded += '=' * padding_needed
    
    try:
        return base64.urlsafe_b64decode(encoded)
    except binascii.Error as e:
        raise ValueError(f"Invalid URL-safe base64: {e}") from e


# =============================================================================
# Hexadecimal Encoding/Decoding
# =============================================================================

def hex_encode(data: bytes) -> str:
    """Encode bytes to lowercase hexadecimal string.
    
    Args:
        data: Bytes to encode.
        
    Returns:
        Lowercase hexadecimal string.
    """
    return data.hex()


def hex_decode(encoded: str) -> bytes:
    """Decode hexadecimal string to bytes.
    
    Args:
        encoded: Hexadecimal string (case-insensitive).
        
    Returns:
        Decoded bytes.
        
    Raises:
        ValueError: If the input is not valid hex or has odd length.
    """
    # Check for odd length
    if len(encoded) % 2 != 0:
        raise ValueError("Odd-length hex string")
    
    try:
        return bytes.fromhex(encoded)
    except ValueError as e:
        raise ValueError(f"Invalid hex: {e}") from e


# =============================================================================
# Percent-Encoding (RFC 3986)
# =============================================================================

# Unreserved characters per RFC 3986 that should NOT be encoded
_UNRESERVED = frozenset(
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~'
)


def percent_encode(data: str) -> str:
    """Encode string using percent-encoding per RFC 3986.
    
    Unreserved characters (A-Z a-z 0-9 - . _ ~) are left as-is.
    All other characters are percent-encoded using UTF-8 byte values.
    
    Args:
        data: String to encode.
        
    Returns:
        Percent-encoded string.
    """
    result = []
    for char in data:
        if char in _UNRESERVED:
            result.append(char)
        else:
            # Encode each byte of the UTF-8 representation
            for byte in char.encode('utf-8'):
                result.append(f'%{byte:02X}')
    return ''.join(result)


def percent_decode(encoded: str) -> str:
    """Decode percent-encoded string per RFC 3986.
    
    Args:
        encoded: Percent-encoded string.
        
    Returns:
        Decoded string.
        
    Raises:
        ValueError: If the input contains invalid or incomplete percent sequences.
    """
    result = []
    i = 0
    while i < len(encoded):
        if encoded[i] == '%':
            # Need at least 2 more characters for a valid percent sequence
            if i + 2 >= len(encoded):
                raise ValueError("Incomplete percent sequence")
            
            hex_chars = encoded[i + 1:i + 3]
            
            # Validate hex characters
            try:
                byte_val = int(hex_chars, 16)
            except ValueError:
                raise ValueError(f"Invalid percent sequence: %{hex_chars}") from None
            
            result.append(byte_val)
            i += 3
        else:
            # Regular character - encode to get its byte value
            result.append(ord(encoded[i]))
            i += 1
    
    # Decode the byte sequence as UTF-8
    try:
        return bytes(result).decode('utf-8')
    except UnicodeDecodeError as e:
        raise ValueError(f"Invalid UTF-8 sequence: {e}") from e
