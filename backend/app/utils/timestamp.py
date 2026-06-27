"""Timestamp formatting helpers for transcripts and reports."""

from __future__ import annotations


def format_timestamp(seconds: float) -> str:
    """Format seconds as ``MM:SS`` (or ``HH:MM:SS`` past one hour)."""
    seconds = max(0.0, float(seconds))
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_range(start: float, end: float) -> str:
    """Format a span as ``[MM:SS - MM:SS]``."""
    return f"[{format_timestamp(start)} - {format_timestamp(end)}]"
