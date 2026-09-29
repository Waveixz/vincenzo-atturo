import html
from datetime import date, datetime

import streamlit as st


def module_header(title: str, description: str, eyebrow: str = "AREA OPERATIVA") -> None:
    st.markdown(
        f"""
        <div class="module-header">
            <div class="module-eyebrow">{html.escape(eyebrow)}</div>
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state compact-empty">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(text)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_date(value):
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def euro(value) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {formatted}"


def rerun_notice(message: str) -> None:
    st.toast(message, icon=":material/check_circle:")
    st.rerun()
