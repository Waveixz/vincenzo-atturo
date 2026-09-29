import calendar
import html
import hmac
import os
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from core.module_loader import render_module
from core.module_registry import enabled_modules
from core.storage import load_data
from core.ui import euro, parse_date
from settings.module_manager import render as render_settings

APP_VERSION = "5.7.1"
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

# Messaggio breve dopo il salvataggio: niente toast persistenti o dialog lasciati aperti.
_flash = st.session_state.pop("flash_message", None)
if _flash:
    st.success(_flash)

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
    "agenda": ":material/calendar_month:",
    "contabilita": ":material/account_balance_wallet:",
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
                <h2>Dashboard pronta</h2>
                <p>Non ci sono moduli attivi. Apri Sistema → Impostazioni per configurarli.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        data = load_data()
        clients = {item["id"]: item for item in data["clients"]}
        projects = {item["id"]: item for item in data["projects"]}
        active_projects = [item for item in data["projects"] if item.get("status") != "Concluso"]
        open_tasks = [item for item in data["tasks"] if item.get("status") != "Completata"]
        expected = sum(float(item.get("amount") or 0) for item in data["payments"] if item.get("status", "Previsto") == "Previsto")
        collected = sum(float(item.get("amount") or 0) for item in data["payments"] if item.get("status") == "Incassato")
        expenses = sum(float(item.get("amount") or 0) for item in data["expenses"])
        overdue_payments = [item for item in data["payments"] if item.get("status", "Previsto") == "Previsto" and parse_date(item.get("due_date")) and parse_date(item.get("due_date")) < date.today()]

        st.markdown("""
            <div class="home-intro">
                <div class="module-eyebrow">VA DIGITAL · CONTROL ROOM</div>
                <h1>Agenda, clienti e contabilità.</h1>
                <p>La giornata operativa di VA Digital: appuntamenti, scadenze, commesse e situazione economica in un'unica vista.</p>
            </div>
        """, unsafe_allow_html=True)

        metrics = st.columns(5)
        metrics[0].metric("Clienti", len(data["clients"]))
        metrics[1].metric("Progetti aperti", len(active_projects))
        metrics[2].metric("Da incassare", euro(expected), f"{len(overdue_payments)} scaduti" if overdue_payments else None, delta_color="inverse")
        metrics[3].metric("Incassato", euro(collected))
        metrics[4].metric("Margine", euro(collected - expenses))

        # Calendario operativo: appuntamenti, attività e scadenze economiche nella stessa vista.
        if "home_calendar_month" not in st.session_state:
            st.session_state.home_calendar_month = date.today().replace(day=1)
        cal_month = st.session_state.home_calendar_month
        cprev, ctitle, cnext = st.columns([1, 5, 1])
        with cprev:
            if st.button("", icon=":material/chevron_left:", key="home_cal_prev", help="Mese precedente", width="stretch"):
                st.session_state.home_calendar_month = (cal_month.replace(day=1) - __import__('datetime').timedelta(days=1)).replace(day=1)
                st.rerun()
        month_names = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        with ctitle:
            st.markdown(f"<div class='home-calendar-heading'>Calendario operativo · {month_names[cal_month.month]} {cal_month.year}</div>", unsafe_allow_html=True)
        with cnext:
            if st.button("", icon=":material/chevron_right:", key="home_cal_next", help="Mese successivo", width="stretch"):
                st.session_state.home_calendar_month = (cal_month.replace(day=28) + __import__('datetime').timedelta(days=4)).replace(day=1)
                st.rerun()

        events = {}
        def add_event(day_value, kind, title, client_id="", project_id="", prefix=""):
            parsed = parse_date(day_value)
            if not parsed or parsed.year != cal_month.year or parsed.month != cal_month.month:
                return
            events.setdefault(parsed.day, []).append({"kind": kind, "title": title, "client_id": client_id, "project_id": project_id, "prefix": prefix})

        for item in data["appointments"]:
            if item.get("status") != "Annullato":
                add_event(item.get("date"), "appointment", item.get("title", "Appuntamento"), item.get("client_id", ""), item.get("project_id", ""), item.get("start_time", ""))
        for item in open_tasks:
            project = projects.get(item.get("project_id"), {})
            add_event(item.get("due_date"), "task", item.get("title", "Attività"), project.get("client_id", ""), item.get("project_id", ""), "Attività")
        for item in data["payments"]:
            if item.get("status", "Previsto") == "Previsto":
                add_event(item.get("due_date"), "payment", f"{item.get('description', 'Pagamento')} · {euro(item.get('amount'))}", item.get("client_id", ""), item.get("project_id", ""), "Incasso")

        headers = "".join(f"<div class='calendar-weekday'>{d}</div>" for d in ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"])
        cells = []
        today = date.today()
        for day in calendar.Calendar(firstweekday=0).itermonthdays(cal_month.year, cal_month.month):
            if day == 0:
                cells.append("<div class='calendar-day is-empty'></div>")
                continue
            entries = []
            for event in events.get(day, [])[:4]:
                label = html.escape((event["prefix"] + " " + event["title"]).strip())
                client = clients.get(event["client_id"], {})
                project = projects.get(event["project_id"], {})
                client_link = f"<a class='home-context-link' href='?module=clienti_progetti&client={event['client_id']}' target='_self'>👤 {html.escape(client.get('name',''))}</a>" if event["client_id"] else ""
                project_link = f"<a class='home-context-link' href='?module=clienti_progetti&project={event['project_id']}' target='_self'>📁 {html.escape(project.get('name',''))}</a>" if event["project_id"] else ""
                context = "".join(x for x in [client_link, project_link] if x)
                if event["kind"] == "appointment":
                    event_target = f"?module=agenda&agenda_date={cal_month.year:04d}-{cal_month.month:02d}-{day:02d}&agenda_view=Giorno"
                    title_html = f"<a class='home-event-title' href='{event_target}' target='_self'>{label}</a>"
                else:
                    title_html = f"<span class='home-event-title'>{label}</span>"
                entries.append(f"<div class='calendar-event event-{event['kind']}'>{title_html}<small class='home-event-context'>{context}</small></div>")
            more = len(events.get(day, [])) - 4
            if more > 0:
                entries.append(f"<div class='calendar-more'>+ {more} altri</div>")
            today_class = " is-today" if today.year == cal_month.year and today.month == cal_month.month and today.day == day else ""
            day_href=f"?module=agenda&agenda_date={cal_month.year:04d}-{cal_month.month:02d}-{day:02d}&agenda_view=Giorno"
            cells.append(f"<div class='calendar-day{today_class}'><a class='calendar-day-link' href='{day_href}' target='_self'><b>{day}</b></a>{''.join(entries)}</div>")
        st.markdown(f"<div class='va-calendar home-calendar'><div class='calendar-grid'>{headers}{''.join(cells)}</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='calendar-legend'><span>● Appuntamenti</span><span>■ Attività</span><span>€ Incassi</span></div>", unsafe_allow_html=True)

        left, right = st.columns([3, 2], gap="large")
        with left:
            st.subheader("Oggi e prossime scadenze")
            timeline = []
            for item in data["appointments"]:
                d = parse_date(item.get("date"))
                if d and d >= date.today() and item.get("status") != "Annullato":
                    timeline.append((d, item.get("start_time", ""), "Appuntamento", item.get("title", ""), item.get("client_id", ""), item.get("project_id", "")))
            for item in open_tasks:
                d = parse_date(item.get("due_date"))
                if d:
                    project = projects.get(item.get("project_id"), {})
                    timeline.append((d, "", "Attività", item.get("title", ""), project.get("client_id", ""), item.get("project_id", "")))
            for item in data["payments"]:
                d = parse_date(item.get("due_date"))
                if d and item.get("status", "Previsto") == "Previsto":
                    timeline.append((d, "", "Incasso", f"{item.get('description', '')} · {euro(item.get('amount'))}", item.get("client_id", ""), item.get("project_id", "")))
            if timeline:
                for d, tm, kind, title, client_id, project_id in sorted(timeline, key=lambda x: (x[0], x[1]))[:10]:
                    client = clients.get(client_id, {})
                    project = projects.get(project_id, {})
                    link = "?module=clienti_progetti"
                    if client_id: link += f"&client={client_id}"
                    if project_id: link += f"&project={project_id}"
                    meta = " · ".join(x for x in [client.get("name", ""), project.get("name", "")] if x)
                    st.markdown(f"<a class='timeline-row' href='{link}' target='_self'><span class='timeline-date'>{d.strftime('%d/%m')} {html.escape(tm)}</span><span><b>{html.escape(kind)} · {html.escape(title)}</b><small>{html.escape(meta)}</small></span></a>", unsafe_allow_html=True)
            else:
                st.info("Nessuna scadenza operativa registrata.")
        with right:
            st.subheader("Contabilità gestionale")
            st.markdown(f"""
                <div class='accounting-card'>
                    <div><span>Incassato</span><b>{euro(collected)}</b></div>
                    <div><span>Da incassare</span><b>{euro(expected)}</b></div>
                    <div><span>Costi</span><b>{euro(expenses)}</b></div>
                    <div class='accounting-total'><span>Margine</span><b>{euro(collected-expenses)}</b></div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Apri pagamenti e contabilità", icon=":material/account_balance_wallet:", width="stretch"):
                navigate("contabilita")
                st.rerun()

            st.subheader("Commesse aperte")
            for project in active_projects[:6]:
                client = clients.get(project.get("client_id"), {})
                st.markdown(f"<a class='project-link-card' href='?module=clienti_progetti&client={project.get('client_id','')}&project={project.get('id','')}' target='_self'><b>{html.escape(project.get('name',''))}</b><span>{html.escape(client.get('name',''))} · {html.escape(project.get('status',''))}</span></a>", unsafe_allow_html=True)

        st.subheader("Accesso rapido")
        quick = st.columns(4)
        actions = [("Clienti", ":material/group:"), ("Progetti", ":material/work:"), ("Agenda", ":material/calendar_month:"), ("Contabilità", ":material/euro:")]
        for col, (label, icon) in zip(quick, actions):
            with col:
                if st.button(label, icon=icon, key=f"quick_{label}", width="stretch"):
                    if label == "Agenda":
                        navigate("agenda")
                    elif label == "Contabilità":
                        navigate("contabilita")
                    else:
                        navigate("clienti_progetti")
                        st.query_params["section"] = label.casefold()
                    st.rerun()

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
