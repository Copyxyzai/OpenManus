"""
Input Sanitizer for Security

Sanitizes user input to prevent injection attacks and ensure data quality.
"""

import re
from typing import List

from app.logger import logger


class InputSanitizer:
    """Sanitize user input for security and quality"""

    # Patterns that could indicate prompt injection or malicious input
    DANGEROUS_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"ignore\s+all\s+previous",
        r"system\s*:",
        r"assistant\s*:",
        r"<script>",
        r"</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onclick\s*=",
    ]

    @classmethod
    def sanitize_query(cls, query: str, max_length: int = 500) -> str:
        """
        Sanitize search query

        Args:
            query: User input query
            max_length: Maximum allowed length

        Returns:
            Sanitized query string
        """
        if not query:
            return ""

        original_query = query

        # Remove control characters
        query = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", query)

        # Limit length
        if len(query) > max_length:
            logger.warning(f"Query truncated from {len(query)} to {max_length} chars")
            query = query[:max_length]

        # Remove dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            matches = re.findall(pattern, query, flags=re.IGNORECASE)
            if matches:
                logger.warning(f"⚠️ Removed dangerous pattern: {pattern}")
                query = re.sub(pattern, "", query, flags=re.IGNORECASE)

        # Normalize whitespace
        query = " ".join(query.split())

        # Strip and validate
        query = query.strip()

        if query != original_query:
            logger.info(
                f"Query sanitized: '{original_query[:50]}...' -> '{query[:50]}...'"
            )

        return query

    @classmethod
    def validate_query(cls, query: str, min_length: int = 2) -> bool:
        """
        Validate that query meets minimum requirements

        Args:
            query: Query to validate
            min_length: Minimum required length

        Returns:
            True if valid, False otherwise
        """
        if not query or len(query) < min_length:
            return False

        # Check if query is not just special characters
        if not re.search(r"[a-zA-Z0-9]", query):
            return False

        return True
