"""Shared timezone-normalization helper."""
from __future__ import annotations


def to_naive_utc(value):
    """Normalize a tz-aware or tz-naive pandas Timestamp/DatetimeIndex to tz-naive UTC calendar dates."""
    if value.tz is not None:
        value = value.tz_convert("UTC").tz_localize(None)
    return value.normalize()
