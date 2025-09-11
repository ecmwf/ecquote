"""Compatibility helpers for Python versions.

Exports:
- `UTC`: timezone for UTC across Python versions.
"""

import datetime

UTC = getattr(datetime, "UTC", datetime.timezone.utc)
