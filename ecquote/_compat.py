"""Compatibility helpers for older Python versions.

Currently provides:
- UTC: timezone info compatible with Python < 3.11 (datetime.UTC).
"""

try:  # Python 3.11+
    from datetime import UTC
except ImportError:  # Python < 3.11
    from datetime import timezone as _timezone
    UTC = _timezone.utc
