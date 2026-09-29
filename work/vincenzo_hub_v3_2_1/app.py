import html
import hmac
import os
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from core.module_loader import render_module
from core.module_registry import enabled_modules
from core.storage import load_data
from core.ui import euro, hub_url, month_calendar, parse_date, record_link
from settings.module_manager import render as render_settings

APP_VERSION = "5.1.0"
BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="VA Digital Hub",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "sidebar_compact" not in st.session_state:
    # La Hub parte volutamente in modalità compatta.
    st.session_state.sidebar_compact = True

sidebar_mode = "compact" if st.session_state.sidebar_compact else "expanded"

base_css = (BASE_DIR / "assets" / "va_style.css").read_text(encoding="utf-8")
st.markdown(
    f"<style>{base_css}</style><style>body{{}}</style>",
    unsafe_allow_html=True,
)


def configured_password() -> str:
    password = os.getenv("VA_HUB_PASSWORD", "")
    if password:
        return password
    try:
        return str(st.secrets.get("VA_HUB_PASSWORD", ""))
    except Exception:
        return ""


def require_access() -> None:
    password = configured_password()
    if not password or st.session_state.get("authenticated"):
        return
    st.markdown(
        """
        <div class="login-brand">
            <div class="hub-logo">VA</div>
            <div><strong>VA Digital Hub</strong><br><span>Accesso riservato</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("access_form"):
        entered = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Accedi", icon=":material/login:")
    if submitted:
        if hmac.compare_digest(entered, password):
            st.session_state.authenticated = True
            st.rerun()
        st.error("Password non corretta.")
    st.stop()


require_access()

# Classe di stato applicata tramite una variabile CSS globale.
if st.session_state.sidebar_compact:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"]{
            min-width:86px!important;
            max-width:86px!important;
            width:86px!important;
        }
        [data-testid="stSidebarContent"]{
            padding:14px 10px 18px!important;
        }
        .block-container{
            padding-left:114px!important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"]{
            min-width:310px!important;
            max-width:310px!important;
            width:310px!important;
        }
        [data-testid="stSidebarContent"]{
            padding:20px 24px 24px!important;
        }
        .block-container{
            padding-left:338px!important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

modules = enabled_modules()
module_by_id = {module["id"]: module for module in modules}

if "page" not in st.session_state:
    st.session_state.page = "home"

requested_module = st.query_params.get("module")
if requested_module in module_by_id:
    st.session_state.page = requested_module

def navigate(page_name: str) -> None:
    st.session_state.page = page_name
    if page_name in module_by_id:
        st.query_params["module"] = page_name
    else:
        st.query_params.clear()

def toggle_sidebar() -> None:
    st.session_state.sidebar_compact = not st.session_state.sidebar_compact

page = st.session_state.page
valid_pages = {"home", "settings", *module_by_id.keys()}
if page not in valid_pages:
    page = "home"
    st.session_state.page = "home"

MODULE_ICONS = {
    "gis": ":material/map:",
    "social_analytics": ":material/bar_chart:",
    "documenti": ":material/description:",
    "it_tecnologia": ":material/computer:",
    "clienti_progetti": ":material/group:",
    "utility": ":material/build:",
}

with st.sidebar:
    if st.session_state.sidebar_compact:
        # Rail compatta: solo icone, sempre visibile.
        if st.button(
            "",
            icon=":material/keyboard_double_arrow_right:",
            key="sidebar_expand",
            help="Espandi menu",
            width="stretch",
        ):
            toggle_sidebar()
            st.rerun()

        st.markdown('<div class="compact-logo">VA</div>', unsafe_allow_html=True)

        if st.button(
            "",
            icon=":material/home:",
            key="compact_home",
            help="Dashboard",
            type="primary" if page == "home" else "secondary",
            width="stretch",
        ):
            navigate("home")
            st.rerun()

        st.markdown('<div class="compact-separator"></div>', unsafe_allow_html=True)

        for module in modules:
            icon = MODULE_ICONS.get(module["id"], ":material/widgets:")
            if module.get("open_mode") == "external":
                st.link_button(
                    "",
                    module.get("url") or "#",
                    icon=icon,
                    help=module["name"],
                    width="stretch",
                )
            else:
                if st.button(
                    "",
                    icon=icon,
                    key=f"compact_{module['id']}",
                    help=module["name"],
                    type="primary" if page == module["id"] else "secondary",
                    width="stretch",
                ):
                    navigate(module["id"])
                    st.rerun()

        st.markdown('<div class="compact-separator compact-system-gap"></div>', unsafe_allow_html=True)

        if st.button(
            "",
            icon=":material/settings:",
            key="compact_settings",
            help="Impostazioni",
            type="primary" if page == "settings" else "secondary",
            width="stretch",
        ):
            navigate("settings")
            st.rerun()

    else:
        # Sidebar estesa.
        top_left, top_right = st.columns([5, 1], gap="small")
        with top_left:
            st.markdown(
                """
                <div class="hub-brand">
                    <div class="hub-logo">VA</div>
                    <div class="hub-brand-copy">
                        <div class="hub-brand-title">VA Digital Hub</div>
                        <div class="hub-brand-subtitle">Workspace operativo</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with top_right:
            if st.button(
                "",
                icon=":material/keyboard_double_arrow_left:",
                key="sidebar_collapse",
                help="Riduci menu",
                width="stretch",
            ):
                toggle_sidebar()
                st.rerun()

        if st.button(
            "Dashboard",
            icon=":material/home:",
            key="nav_home",
            type="primary" if page == "home" else "secondary",
            width="stretch",
        ):
            navigate("home")
            st.rerun()

        st.markdown('<div class="hub-divider"></div>', unsafe_allow_html=True)

        with st.expander("Moduli", icon=":material/deployed_code:", expanded=True):
            for module in modules:
                icon = MODULE_ICONS.get(module["id"], ":material/widgets:")
                if module.get("open_mode") == "external":
                    st.link_button(
                        module["name"],
                        module.get("url") or "#",
                        icon=icon,
                        width="stretch",
                    )
                else:
                    if st.button(
                        module["name"],
                        icon=icon,
                        key=f"nav_{module['id']}",
                        type="primary" if page == module["id"] else "secondary",
                        width="stretch",
                    ):
                        navigate(module["id"])
                        st.rerun()

        with st.expander("Sistema", icon=":material/settings:", expanded=page == "settings"):
            if st.button(
                "Impostazioni",
                icon=":material/tune:",
                key="nav_settings",
                type="primary" if page == "settings" else "secondary",
                width="stretch",
            ):
                navigate("settings")
                st.rerun()

        st.markdown(
            f"""
            <div class="hub-info">
                <div class="hub-info-icon">ⓘ</div>
                <div>
                    <div class="hub-info-title">VA Digital Hub</div>
                    <div class="hub-info-version">v{APP_VERSION}</div>
                    <div class="hub-info-text">
                        {len(modules)} moduli caricati<br>
                        Dati salvati localmente<br>
                        <b>va-digital.it</b>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

page_title = (
    "Dashboard"
    if page == "home"
    else "Impostazioni"
    if page == "settings"
    else module_by_id.get(page, {}).get("name", "VA Digital Hub")
)

now = datetime.now().strftime("%d/%m/%Y · %H:%M")
st.markdown(
    f"""
    <div class="hub-topbar">
        <div>
            <div class="hub-topbar-title">{html.escape(page_title)}</div>
            <div class="hub-topbar-subtitle">VA Digital · workspace operativo</div>
        </div>
        <div class="hub-chip">{now}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "home":
    if not modules:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-icon">＋</div>
                <h2>Dashboard pronta</h2>
                <p>Non ci sono moduli attivi. Apri Sistema → Impostazioni per configurarli.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        data = load_data()
        clients_by_id = {item["id"]: item for item in data["clients"]}
        projects_by_id = {item["id"]: item for item in data["projects"]}
        active_projects = [item for item in data["projects"] if item.get("status") != "Concluso"]
        open_tasks = [item for item in data["tasks"] if item.get("status") != "Completata"]
        expected_payments = [item for item in data["payments"] if item.get("status", "Previsto") == "Previsto"]
        collected = sum(float(item.get("amount") or 0) for item in data["payments"] if item.get("status") == "Incassato")
        expenses = sum(float(item.get("amount") or 0) for item in data["expenses"])
        expected = sum(float(item.get("amount") or 0) for item in expected_payments)
        overdue_payments = [item for item in expected_payments if parse_date(item.get("due_date")) and parse_date(item.get("due_date")) < date.today()]
        upcoming_appointments = [item for item in data["appointments"] if parse_date(item.get("date")) and parse_date(item.get("date")) >= date.today() and item.get("status") != "Annullato"]

        st.markdown(
            """
            <div class="home-intro">
                <div class="module-eyebrow">VA DIGITAL CONTROL ROOM</div>
                <h1>Agenda, clienti e conti sotto controllo.</h1>
                <p>Il quadro operativo della giornata: appuntamenti, commesse, attività e scadenze economiche collegate alle rispettive anagrafiche.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        metrics = st.columns(5)
        metrics[0].metric("Clienti", len(data["clients"]))
        metrics[1].metric("Progetti aperti", len(active_projects))
        metrics[2].metric("Da incassare", euro(expected), f"{len(overdue_payments)} scaduti" if overdue_payments else None, delta_color="inverse")
        metrics[3].metric("Incassato", euro(collected))
        metrics[4].metric("Margine", euro(collected - expenses))

        calendar_col, day_col = st.columns([3, 1], gap="large")
        with calendar_col:
            calendar_month = st.date_input("Mese calendario", value=date.today(), format="DD/MM/YYYY", key="home_calendar_month")
            calendar_events = []
            for item in data["appointments"]:
                calendar_events.append({
                    "date": item.get("date"),
                    "label": f"{item.get('start_time', '')} {item.get('title', '')}".strip(),
                    "kind": "appointment",
                    "href": hub_url(module="clienti_progetti", section="agenda", appointment_id=item.get("id")),
                })
            for item in expected_payments:
                calendar_events.append({
                    "date": item.get("due_date"),
                    "label": f"€ {float(item.get('amount') or 0):,.0f} {item.get('description', '')}".replace(",", "."),
                    "kind": "payment",
                    "href": hub_url(module="clienti_progetti", section="payments", client_id=item.get("client_id")),
                })
            for item in open_tasks:
                calendar_events.append({
                    "date": item.get("due_date"),
                    "label": item.get("title", "Attività"),
                    "kind": "task",
                    "href": hub_url(module="clienti_progetti", section="tasks", project_id=item.get("project_id")),
                })
            st.markdown(month_calendar(calendar_month, calendar_events), unsafe_allow_html=True)
        with day_col:
            st.markdown('<div class="home-section-title">Prossime scadenze</div>', unsafe_allow_html=True)
            deadlines = []
            for item in upcoming_appointments:
                deadlines.append((item.get("date", ""), item.get("title", ""), "Appuntamento", hub_url(module="clienti_progetti", section="agenda", appointment_id=item.get("id"))))
            for item in expected_payments:
                deadlines.append((item.get("due_date", ""), item.get("description", "Pagamento"), euro(item.get("amount")), hub_url(module="clienti_progetti", section="payments", client_id=item.get("client_id"))))
            for item in open_tasks:
                deadlines.append((item.get("due_date", ""), item.get("title", "Attività"), item.get("priority", ""), hub_url(module="clienti_progetti", section="tasks", project_id=item.get("project_id"))))
            if deadlines:
                rows = "".join(
                    f'<div class="home-list-row"><a class="record-link" href="{html.escape(link, quote=True)}">{html.escape(label)}</a><span>{html.escape(detail)}</span><strong>{html.escape(due)}</strong></div>'
                    for due, label, detail, link in sorted(deadlines)[:7]
                )
                st.markdown(f'<div class="home-list">{rows}</div>', unsafe_allow_html=True)
            else:
                st.info("Nessuna scadenza programmata.")

        st.markdown('<div class="home-section-title">Anagrafiche e commesse</div>', unsafe_allow_html=True)
        clients_col, projects_col = st.columns(2, gap="large")
        with clients_col:
            st.subheader("Clienti")
            if data["clients"]:
                rows = "".join(
                    f'<div class="home-list-row">{record_link(item.get("name", "Cliente"), module="clienti_progetti", section="client", client_id=item.get("id"))}<span>{html.escape(item.get("contact", ""))}</span><strong>{html.escape(item.get("status", "Attivo"))}</strong></div>'
                    for item in data["clients"][:8]
                )
                st.markdown(f'<div class="home-list">{rows}</div>', unsafe_allow_html=True)
            else:
                st.info("Nessun cliente registrato.")
        with projects_col:
            st.subheader("Progetti attivi")
            if active_projects:
                rows = "".join(
                    f'<div class="home-list-row">{record_link(item.get("name", "Progetto"), module="clienti_progetti", section="project", project_id=item.get("id"))}<span>{record_link(clients_by_id.get(item.get("client_id"), {}).get("name", "Cliente"), module="clienti_progetti", section="client", client_id=item.get("client_id"))}</span><strong>{html.escape(item.get("status", ""))}</strong></div>'
                    for item in active_projects[:8]
                )
                st.markdown(f'<div class="home-list">{rows}</div>', unsafe_allow_html=True)
            else:
                st.info("Nessun progetto aperto.")

        st.markdown('<div class="home-section-title">Situazione economica</div>', unsafe_allow_html=True)
        finance = st.columns(4)
        finance[0].metric("Ricavi incassati", euro(collected))
        finance[1].metric("Crediti attesi", euro(expected))
        finance[2].metric("Costi registrati", euro(expenses))
        finance[3].metric("Margine gestionale", euro(collected - expenses))

elif page == "settings":
    render_settings()

else:
    module = module_by_id[page]
    if module.get("allow_new_tab", True):
        _, action_column = st.columns([5, 1])
        with action_column:
            st.link_button(
                "Nuova scheda ↗",
                f"?module={module['id']}",
                width="stretch",
            )
    render_module(module)
