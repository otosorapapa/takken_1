from __future__ import annotations

import datetime as dt

import streamlit as st


def _format_seconds(total_seconds: int) -> str:
    minutes, seconds = divmod(max(total_seconds, 0), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def render_countdown(key: str, total_seconds: int, label: str) -> int:
    """Render a countdown timer and return remaining seconds."""

    state_key = f"{key}_end"
    if state_key not in st.session_state:
        st.session_state[state_key] = dt.datetime.utcnow() + dt.timedelta(seconds=total_seconds)

    remaining = int((st.session_state[state_key] - dt.datetime.utcnow()).total_seconds())
    remaining = max(0, remaining)
    st.metric(label, _format_seconds(remaining))

    return remaining


def reset_countdown(key: str) -> None:
    if f"{key}_end" in st.session_state:
        del st.session_state[f"{key}_end"]
