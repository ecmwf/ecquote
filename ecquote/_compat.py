"""Compatibility helpers for older Python versions.

Currently provides:
- UTC: timezone info compatible with Python < 3.11 (datetime.UTC).
"""

try:  # Python 3.11+
    from datetime import UTC  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - fallback for older Python
    from datetime import timezone as _timezone

    UTC = _timezone.utc  # type: ignore[assignment]

