import html
import calendar
from datetime import date, datetime
from urllib.parse import urlencode

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


def hub_url(**params) -> str:
    clean = {key: value for key, value in params.items() if value not in (None, "")}
    return f"?{urlencode(clean)}"


def record_link(label: str, **params) -> str:
    return f'<a class="record-link" href="{html.escape(hub_url(**params), quote=True)}">{html.escape(str(label))}</a>'


def month_calendar(selected_month: date, events: list[dict]) -> str:
    month_names = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    grouped = {}
    for event in events:
        event_date = parse_date(event.get("date"))
        if event_date and event_date.year == selected_month.year and event_date.month == selected_month.month:
            grouped.setdefault(event_date.day, []).append(event)

    headers = "".join(f"<div class='calendar-weekday'>{day}</div>" for day in ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"])
    cells = []
    for day in calendar.Calendar(firstweekday=0).itermonthdays(selected_month.year, selected_month.month):
        if day == 0:
            cells.append("<div class='calendar-day is-empty'></div>")
            continue
        entries = []
        for event in grouped.get(day, [])[:4]:
            label = html.escape(str(event.get("label", "")))
            href = html.escape(str(event.get("href", "#")), quote=True)
            kind = html.escape(str(event.get("kind", "appointment")))
            entries.append(f"<a class='calendar-event kind-{kind}' href='{href}'>{label}</a>")
        cells.append(f"<div class='calendar-day'><b>{day}</b>{''.join(entries)}</div>")

    title = f"{month_names[selected_month.month]} {selected_month.year}"
    return f"<div class='va-calendar'><div class='calendar-title'>{title}</div><div class='calendar-grid'>{headers}{''.join(cells)}</div></div>"
