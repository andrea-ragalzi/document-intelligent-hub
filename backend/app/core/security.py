"""
Security Utilities - File Handling and Input Sanitization

Provides helper functions for secure file handling and input validation.
"""

import os
import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.

    Security protections:
    - Removes path components (e.g., ../../etc/passwd.pdf → passwd.pdf)
    - Removes dangerous characters (.., /, \\, null bytes)
    - Limits filename length to 255 characters
    - Preserves file extension

    Args:
        filename: Original filename from user upload

    Returns:
        str: Sanitized filename safe for storage

    Examples:
        >>> sanitize_filename("../../../../etc/passwd.pdf")
        'passwd.pdf'
        >>> sanitize_filename("invoice..pdf")
        'invoice.pdf'
        >>> sanitize_filename("file/with\\slashes.pdf")
        'filewithslashes.pdf'
    """
    if not filename:
        return "unnamed_file"

    # 1. Get basename only (removes path traversal like ../../)
    safe_name = os.path.basename(filename)

    # 2. Remove null bytes (potential binary injection)
    safe_name = safe_name.replace("\x00", "")

    # 3. Remove dangerous path sequences
    safe_name = safe_name.replace("..", "")
    safe_name = safe_name.replace("/", "")
    safe_name = safe_name.replace("\\", "")

    # 4. Remove control characters and other dangerous chars
    safe_name = re.sub(r'[<>:"|?*\x00-\x1f]', "", safe_name)

    # 5. Ensure it's not empty after sanitization
    if not safe_name or safe_name in (".", "..", ""):
        return "unnamed_file"

    # 6. Limit length (filesystem limit is usually 255 bytes)
    if len(safe_name) > 255:
        # Preserve extension if possible
        name_parts = safe_name.rsplit(".", 1)
        if len(name_parts) == 2:
            name, ext = name_parts
            max_name_length = 255 - len(ext) - 1  # -1 for the dot
            safe_name = f"{name[:max_name_length]}.{ext}"
        else:
            safe_name = safe_name[:255]

    return safe_name


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """
    Validate file has an allowed extension.

    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.jpg'])

    Returns:
        bool: True if extension is allowed

    Examples:
        >>> validate_file_extension("doc.pdf", [".pdf"])
        True
        >>> validate_file_extension("doc.exe", [".pdf"])
        False
    """
    if not filename:
        return False

    file_ext = Path(filename).suffix.lower()
    return file_ext in [ext.lower() for ext in allowed_extensions]


def get_safe_file_size_mb(size_bytes: int) -> float:
    """
    Convert bytes to megabytes with 2 decimal precision.

    Args:
        size_bytes: File size in bytes

    Returns:
        float: Size in MB (rounded to 2 decimals)
    """
    return round(size_bytes / (1024 * 1024), 2)
