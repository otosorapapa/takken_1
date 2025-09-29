from __future__ import annotations

import streamlit as st

THEMES = {
    "light": {
        "background": "#FFFFFF",
        "text": "#111827",
        "accent": "#2563EB",
        "muted": "#F3F4F6",
        "border": "#E5E7EB",
    },
    "dark": {
        "background": "#0B1020",
        "text": "#E5E7EB",
        "accent": "#60A5FA",
        "muted": "#1F2937",
        "border": "#374151",
    },
    "sepia": {
        "background": "#F6F1E4",
        "text": "#3F3A34",
        "accent": "#A8763E",
        "muted": "#E6D9C8",
        "border": "#D8C4A6",
    },
}

FONT_FAMILY = "'Noto Sans JP', sans-serif"


def apply_theme(theme_key: str = "light") -> None:
    theme = THEMES.get(theme_key, THEMES["light"])
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
    body, .stApp {{
        background-color: {theme['background']} !important;
        color: {theme['text']} !important;
        font-family: {FONT_FAMILY};
    }}
    .stButton>button {{
        background-color: {theme['accent']} !important;
        color: #fff !important;
        border-radius: 6px;
        border: none;
        transition: transform 0.1s ease;
    }}
    .stButton>button:hover {{
        transform: translateY(-1px);
    }}
    .stButton>button:focus {{
        outline: 3px solid {theme['border']};
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3);
    }}
    .question-meta {{
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }}
    .question-meta .badge {{
        background: {theme['muted']};
        padding: 0.25rem 0.5rem;
        border-radius: 999px;
        font-size: 0.8rem;
    }}
    .stRadio > label, .stCheckbox > label {{
        font-size: 1rem;
    }}
    .css-ocqkz7, .st-emotion-cache-1ekf6i8 {{
        color: {theme['text']} !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
