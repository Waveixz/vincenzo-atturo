import calendar
import html
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from core.storage import add_record, delete_record, load_data, update_record
from core.ui import empty_state, euro, module_header, parse_date, rerun_notice


PROJECT_STATUSES = ["Da valutare", "Proposta", "In corso", "In attesa", "Concluso"]
TASK_STATUSES = ["Da fare", "In corso", "In attesa", "Completata"]
PRIORITIES = ["Bassa", "Media", "Alta", "Urgente"]
PAYMENT_STATUSES = ["Previsto", "Incassato", "Annullato"]
APPOINTMENT_STATUSES = ["Pianificato", "Confermato", "Completato", "Annullato"]


def _by_id(records):
    return {item.get("id"): item for item in records}


def _name(records, record_id, fallback="Non associato"):
    item = _by_id(records).get(record_id)
    return item.get("name", fallback) if item else fallback


def _payment_state(item):
    status = item.get("status", "Previsto")
    due = parse_date(item.get("due_date"))
    if status == "Previsto" and due and due < date.today():
        return "Scaduto"
    return status


def _totals(data, client_id=None, project_id=None):
    payments = data["payments"]
    expenses = data["expenses"]
    if client_id:
        payments = [item for item in payments if item.get("client_id") == client_id]
        client_projects = {item["id"] for item in data["projects"] if item.get("client_id") == client_id}
        expenses = [item for item in expenses if item.get("project_id") in client_projects]
    if project_id:
        payments = [item for item in payments if item.get("project_id") == project_id]
        expenses = [item for item in expenses if item.get("project_id") == project_id]
    expected = sum(float(item.get("amount") or 0) for item in payments if _payment_state(item) not in {"Incassato", "Annullato"})
    collected = sum(float(item.get("amount") or 0) for item in payments if _payment_state(item) == "Incassato")
    overdue = sum(float(item.get("amount") or 0) for item in payments if _payment_state(item) == "Scaduto")
    spent = sum(float(item.get("amount") or 0) for item in expenses)
    return expected, collected, overdue, spent



def _calendar_html(events, focus, clients):
    """Calendario mensile navigabile: ogni giorno apre la vista giornaliera dell'agenda."""
    year, month = focus.year, focus.month
    cal = calendar.Calendar(firstweekday=0)
    client_map = _by_id(clients)
    parts = ["<div class='va-calendar'>", f"<div class='calendar-title'>{html.escape(focus.strftime('%B %Y').capitalize())}</div>", "<div class='calendar-grid calendar-head'>"]
    for name in ["Lun","Mar","Mer","Gio","Ven","Sab","Dom"]:
        parts.append(f"<div>{name}</div>")
    parts.append("</div><div class='calendar-grid'>")
    for d in cal.itermonthdates(year, month):
        outside = " outside" if d.month != month else ""
        today = " today" if d == date.today() else ""
        day_events = sorted([e for e in events if parse_date(e.get("date")) == d], key=lambda e:e.get("start_time", ""))
        href=f"?module=agenda&agenda_date={d.isoformat()}&agenda_view=Giorno"
        bits=[]
        for e in day_events[:3]:
            cname=client_map.get(e.get("client_id"),{}).get("name","")
            label=((e.get("start_time","")+" "+e.get("title","")).strip())
            if cname: label += " · "+cname
            bits.append(f"<span class='cal-event'>{html.escape(label)}</span>")
        more=f"<span class='cal-more'>+{len(day_events)-3} altri</span>" if len(day_events)>3 else ""
        parts.append(f"<a class='calendar-day{outside}{today}' href='{href}' target='_self'><b>{d.day}</b>{''.join(bits)}{more}</a>")
    parts.append("</div></div>")
    return "".join(parts)


# --- VA Digital 5.6 · drawer di inserimento ---
def _close_drawer_notice(message):
    """Chiude il dialog dopo il salvataggio e aggiorna la vista corrente."""
    st.session_state.pop("drawer_appointment_defaults", None)
    st.toast(message, icon=":material/check_circle:")
    st.rerun(scope="app")

@st.dialog("Nuovo cliente", width="large")
def _drawer_client():
    with st.form("drawer_new_client", clear_on_submit=True):
        c1,c2=st.columns(2); name=c1.text_input("Cliente o ragione sociale *"); contact=c2.text_input("Referente")
        email=c1.text_input("Email"); phone=c2.text_input("Telefono"); vat=c1.text_input("Partita IVA"); tax=c2.text_input("Codice fiscale")
        address=st.text_input("Indirizzo"); notes=st.text_area("Esigenze e note")
        if st.form_submit_button("Salva cliente", type="primary", width="stretch"):
            if not name.strip(): st.warning("Inserisci il nome del cliente.")
            else:
                add_record("clients", {"name":name.strip(),"contact":contact.strip(),"email":email.strip(),"phone":phone.strip(),"vat_code":vat.strip(),"tax_code":tax.strip(),"address":address.strip(),"notes":notes.strip(),"status":"Attivo"})
                _close_drawer_notice("Cliente aggiunto")

@st.dialog("Nuovo progetto", width="large")
def _drawer_project():
    data=load_data(); clients=data["clients"]
    if not clients: st.info("Aggiungi prima almeno un cliente."); return
    with st.form("drawer_new_project", clear_on_submit=True):
        opts={x["id"]:x["name"] for x in clients}; c1,c2=st.columns(2)
        name=c1.text_input("Nome progetto *"); cid=c2.selectbox("Cliente",opts,format_func=opts.get); status=c1.selectbox("Stato",PROJECT_STATUSES,index=2); due=c2.date_input("Scadenza prevista",value=date.today()+timedelta(days=30),format="DD/MM/YYYY")
        value=c1.number_input("Valore concordato",min_value=0.0,step=100.0); owner=c2.text_input("Referente operativo",value="Vincenzo Atturo"); notes=st.text_area("Obiettivo e note")
        if st.form_submit_button("Crea progetto",type="primary",width="stretch"):
            if not name.strip(): st.warning("Inserisci il nome del progetto.")
            else: add_record("projects",{"name":name.strip(),"client_id":cid,"status":status,"due_date":due.isoformat(),"value":value,"owner":owner.strip(),"notes":notes.strip()}); _close_drawer_notice("Progetto creato")

@st.dialog("Nuovo appuntamento", width="large")
def _drawer_appointment():
    data=load_data(); clients=data["clients"]; projects=data["projects"]; defaults=st.session_state.get("drawer_appointment_defaults",{})
    copts={"":"Non associato",**{x["id"]:x["name"] for x in clients}}; popts={"":"Non associato",**{x["id"]:x["name"] for x in projects}}
    with st.form("drawer_new_appointment",clear_on_submit=True):
        c1,c2=st.columns(2); title=c1.text_input("Titolo appuntamento *"); d=c2.date_input("Data",value=parse_date(defaults.get("date")) or date.today(),format="DD/MM/YYYY")
        tval=defaults.get("time","09:00"); tm=datetime.strptime(tval,"%H:%M").time() if isinstance(tval,str) else tval
        tm=c1.time_input("Ora",value=tm); kind=c2.selectbox("Tipo",["Incontro","Videochiamata","Telefonata","Scadenza","Consegna","Altro"]); cid=c1.selectbox("Cliente",copts,format_func=copts.get); pid=c2.selectbox("Progetto",popts,format_func=popts.get)
        location=c1.text_input("Luogo o collegamento"); status=c2.selectbox("Stato",APPOINTMENT_STATUSES); notes=st.text_area("Note")
        if st.form_submit_button("Aggiungi in agenda",type="primary",width="stretch"):
            if not title.strip(): st.warning("Inserisci il titolo.")
            else: add_record("appointments",{"title":title.strip(),"date":d.isoformat(),"start_time":tm.strftime("%H:%M"),"type":kind,"client_id":cid,"project_id":pid,"location":location.strip(),"status":status,"notes":notes.strip()}); _close_drawer_notice("Appuntamento aggiunto")

@st.dialog("Nuovo pagamento", width="large")
def _drawer_payment():
    data=load_data(); clients=data["clients"]; projects=data["projects"]
    if not clients: st.info("Aggiungi prima un cliente."); return
    copts={x["id"]:x["name"] for x in clients}; popts={"":"Non associato",**{x["id"]:x["name"] for x in projects}}
    with st.form("drawer_new_payment",clear_on_submit=True):
        c1,c2=st.columns(2); cid=c1.selectbox("Cliente",copts,format_func=copts.get); pid=c2.selectbox("Progetto",popts,format_func=popts.get); desc=c1.text_input("Descrizione *"); amount=c2.number_input("Importo",min_value=0.0,step=50.0); due=c1.date_input("Scadenza",value=date.today()+timedelta(days=30),format="DD/MM/YYYY"); status=c2.selectbox("Stato",PAYMENT_STATUSES); notes=st.text_area("Note")
        if st.form_submit_button("Registra pagamento",type="primary",width="stretch"):
            if not desc.strip() or amount<=0: st.warning("Inserisci descrizione e importo.")
            else: add_record("payments",{"client_id":cid,"project_id":pid,"description":desc.strip(),"amount":amount,"due_date":due.isoformat(),"paid_date":date.today().isoformat() if status=="Incassato" else "","status":status,"notes":notes.strip()}); _close_drawer_notice("Pagamento registrato")

@st.dialog("Nuovo costo", width="large")
def _drawer_expense():
    projects=load_data()["projects"]; opts={"":"Generale",**{x["id"]:x["name"] for x in projects}}
    with st.form("drawer_new_expense",clear_on_submit=True):
        c1,c2=st.columns(2); d=c1.date_input("Data",value=date.today(),format="DD/MM/YYYY"); pid=c2.selectbox("Progetto",opts,format_func=opts.get); category=c1.selectbox("Categoria",["Software e servizi","Hardware","Trasferte","Collaborazioni","Imposte e commissioni","Altro"]); supplier=c2.text_input("Fornitore"); desc=c1.text_input("Descrizione *"); amount=c2.number_input("Importo",min_value=0.0,step=10.0);
        if st.form_submit_button("Registra costo",type="primary",width="stretch"):
            if not desc.strip() or amount<=0: st.warning("Inserisci descrizione e importo.")
            else: add_record("expenses",{"date":d.isoformat(),"project_id":pid,"category":category,"supplier":supplier.strip(),"description":desc.strip(),"amount":amount}); _close_drawer_notice("Costo registrato")

def _overview(data):
    clients = data["clients"]
    projects = data["projects"]
    active_projects = [item for item in projects if item.get("status") != "Concluso"]
    open_tasks = [item for item in data["tasks"] if item.get("status") != "Completata"]
    upcoming = [
        item for item in data["appointments"]
        if parse_date(item.get("date")) and parse_date(item.get("date")) >= date.today() and item.get("status") != "Annullato"
    ]
    expected, collected, overdue, spent = _totals(data)

    metrics = st.columns(5)
    metrics[0].metric("Clienti", len(clients))
    metrics[1].metric("Progetti aperti", len(active_projects))
    metrics[2].metric("Da incassare", euro(expected))
    metrics[3].metric("Incassato", euro(collected))
    metrics[4].metric("Scaduto", euro(overdue))

    left, middle, right = st.columns([2, 2, 1], gap="large")
    with left:
        st.subheader("Lavoro in corso")
        if active_projects:
            st.dataframe([
                {
                    "Progetto": item.get("name", ""),
                    "Cliente": _name(clients, item.get("client_id")),
                    "Stato": item.get("status", ""),
                    "Scadenza": item.get("due_date", ""),
                    "Valore": euro(item.get("value")),
                }
                for item in active_projects
            ], hide_index=True, width="stretch")
        else:
            empty_state("Nessun progetto aperto", "Crea una commessa dalla scheda Progetti.")
    with middle:
        st.subheader("Prossimi appuntamenti")
        if upcoming:
            for item in sorted(upcoming, key=lambda row: (row.get("date", ""), row.get("start_time", "")))[:6]:
                client = _name(clients, item.get("client_id"), "")
                st.markdown(f"**{item.get('date', '')} · {item.get('start_time', '')} — {item.get('title', '')}**  \n{client} · {item.get('status', '')}")
        else:
            empty_state("Agenda libera", "I prossimi appuntamenti compariranno qui.")
    with right:
        st.subheader("Controllo")
        st.metric("Attività aperte", len(open_tasks))
        st.metric("Costi registrati", euro(spent))


def _new_client_form(expanded=False):
    if st.button("+ Nuovo cliente", icon=":material/person_add:", type="primary", key=f"new_client_{expanded}"):
        _drawer_client()

def _client_documents(data, client):
    client_name = client.get("name", "").casefold()
    return [
        item for item in data["documents"]
        if item.get("client_id") == client.get("id") or client_name in item.get("context", "").casefold()
    ]


def _client_profile(data):
    clients = data["clients"]
    _new_client_form(expanded=not clients)
    if not clients:
        empty_state("Nessun cliente", "Inserisci il primo cliente per costruire la sua scheda operativa.")
        return

    options = {item["id"]: item["name"] for item in clients}
    requested_client = st.query_params.get("client")
    default_index = list(options).index(requested_client) if requested_client in options else 0
    selected_id = st.selectbox("Apri la scheda cliente", options, index=default_index, format_func=options.get)
    client = _by_id(clients)[selected_id]
    projects = [item for item in data["projects"] if item.get("client_id") == selected_id]
    project_ids = {item["id"] for item in projects}
    payments = [item for item in data["payments"] if item.get("client_id") == selected_id]
    appointments = [item for item in data["appointments"] if item.get("client_id") == selected_id]
    tasks = [item for item in data["tasks"] if item.get("project_id") in project_ids]
    expenses = [item for item in data["expenses"] if item.get("project_id") in project_ids]
    documents = _client_documents(data, client)
    tickets = [item for item in data.get("support_tickets", []) if item.get("client_id") == selected_id]
    client_notes = [item for item in data.get("notes", []) if item.get("client_id") == selected_id]
    expected, collected, overdue, spent = _totals(data, client_id=selected_id)

    st.markdown(f"### {html.escape(client.get('name', ''))}")
    st.caption(" · ".join(value for value in [client.get("contact"), client.get("email"), client.get("phone")] if value))
    metrics = st.columns(6)
    metrics[0].metric("Progetti", len(projects))
    metrics[1].metric("Incassato", euro(collected))
    metrics[2].metric("Da incassare", euro(expected))
    metrics[3].metric("Scaduto", euro(overdue))
    metrics[4].metric("Costi", euro(spent))
    metrics[5].metric("Margine", euro(collected - spent))

    tabs = st.tabs(["Riepilogo", "Progetti", "Contabilità", "Agenda", "Documenti", "Assistenza", "Note"])
    summary_tab, projects_tab, accounting_tab, agenda_tab, documents_tab, support_tab, notes_tab = tabs

    with summary_tab:
        left, right = st.columns([1, 1], gap="large")
        with left:
            st.markdown("#### Anagrafica")
            st.write(client.get("address") or "Indirizzo non inserito")
            st.write(f"Referente: {client.get('contact') or '-'}")
            st.write(f"Email: {client.get('email') or '-'}")
            st.write(f"Telefono: {client.get('phone') or '-'}")
            st.write(f"P. IVA: {client.get('vat_code') or '-'}")
            st.write(f"Codice fiscale: {client.get('tax_code') or '-'}")
        with right:
            st.markdown("#### Situazione operativa")
            active = [x for x in projects if x.get("status") != "Concluso"]
            open_tasks = [x for x in tasks if x.get("status") != "Completata"]
            next_appts = sorted([x for x in appointments if parse_date(x.get("date")) and parse_date(x.get("date")) >= date.today() and x.get("status") != "Annullato"], key=lambda x:(x.get("date", ""), x.get("start_time", "")))
            st.write(f"Commesse aperte: **{len(active)}**")
            st.write(f"Attività aperte: **{len(open_tasks)}**")
            st.write(f"Assistenze aperte: **{len([x for x in tickets if x.get('status') != 'Chiusa'])}**")
            if next_appts:
                x=next_appts[0]
                st.write(f"Prossimo appuntamento: **{x.get('date','')} {x.get('start_time','')} · {x.get('title','')}**")
            else: st.write("Prossimo appuntamento: **nessuno**")
        st.markdown("#### Note operative")
        st.write(client.get("notes") or "Nessuna nota operativa nell'anagrafica.")
        with st.expander("Aggiorna anagrafica", icon=":material/edit:"):
            with st.form("edit_client"):
                c1,c2=st.columns(2)
                contact=c1.text_input("Referente",client.get("contact","")); email=c2.text_input("Email",client.get("email",""))
                phone=c1.text_input("Telefono",client.get("phone","")); statuses=["Attivo","Potenziale","Archiviato"]
                current=client.get("status","Attivo"); status=c2.selectbox("Stato",statuses,index=statuses.index(current) if current in statuses else 0)
                address=st.text_input("Indirizzo",client.get("address","")); notes=st.text_area("Note operative",client.get("notes",""))
                if st.form_submit_button("Salva anagrafica",icon=":material/save:"):
                    update_record("clients",selected_id,{"contact":contact,"email":email,"phone":phone,"status":status,"address":address,"notes":notes}); rerun_notice("Anagrafica aggiornata")

    with projects_tab:
        if projects:
            for item in projects:
                href=f"?module=clienti_progetti&project={item['id']}"
                st.markdown(f"<a class='agenda-day-card' style='display:block;text-decoration:none;color:inherit' href='{href}' target='_self'><b>{html.escape(item.get('name',''))}</b><small>{html.escape(item.get('status',''))} · scadenza {html.escape(item.get('due_date') or '-')} · {html.escape(euro(item.get('value')))}</small></a>", unsafe_allow_html=True)
        else: empty_state("Nessun progetto", "Il cliente non ha ancora commesse collegate.")
        if tasks:
            st.markdown("#### Attività collegate")
            st.dataframe([{"Attività":x.get("title"),"Progetto":_name(projects,x.get("project_id")),"Scadenza":x.get("due_date"),"Priorità":x.get("priority"),"Stato":x.get("status")} for x in tasks],hide_index=True,width="stretch")

    with accounting_tab:
        c1,c2,c3,c4=st.columns(4); c1.metric("Incassato",euro(collected)); c2.metric("Da incassare",euro(expected)); c3.metric("Scaduto",euro(overdue)); c4.metric("Margine",euro(collected-spent))
        movements=[]
        for x in payments:
            movements.append({"Data":x.get("paid_date") or x.get("due_date") or "","Tipo":"Entrata","Voce":x.get("description") or "Pagamento","Progetto":_name(projects,x.get("project_id"),""),"Importo":euro(x.get("amount")),"Stato":_payment_state(x)})
        for x in expenses:
            movements.append({"Data":x.get("date") or "","Tipo":"Uscita","Voce":x.get("description") or x.get("category") or "Costo","Progetto":_name(projects,x.get("project_id"),""),"Importo":euro(x.get("amount")),"Stato":"Registrata"})
        if movements: st.dataframe(sorted(movements,key=lambda x:x["Data"],reverse=True),hide_index=True,width="stretch")
        else: empty_state("Nessun movimento", "Pagamenti e costi del cliente compariranno qui.")

    with agenda_tab:
        upcoming=sorted(appointments,key=lambda x:(x.get("date",""),x.get("start_time","")))
        if upcoming: st.dataframe([{"Data":x.get("date"),"Ora":x.get("start_time"),"Appuntamento":x.get("title"),"Progetto":_name(projects,x.get("project_id"),""),"Stato":x.get("status")} for x in upcoming],hide_index=True,width="stretch")
        else: empty_state("Nessun appuntamento", "Gli appuntamenti collegati al cliente compariranno qui.")
        st.page_link("app.py", label="Apri Agenda completa", icon=":material/calendar_month:", query_params={"module":"clienti_progetti","section":"agenda","client":selected_id}) if False else None

    with documents_tab:
        if documents: st.dataframe([{"Documento":x.get("title"),"Categoria":x.get("category"),"File":Path(x.get("path","")).name} for x in documents],hide_index=True,width="stretch")
        else: empty_state("Nessun documento", "Compila o archivia un documento indicando questo cliente.")

    with support_tab:
        with st.expander("Nuova richiesta / intervento", icon=":material/support_agent:"):
            with st.form("new_support_ticket",clear_on_submit=True):
                c1,c2=st.columns(2); title=c1.text_input("Oggetto"); priority=c2.selectbox("Priorità",PRIORITIES,index=1)
                project_opts={"":"Non associato",**{x["id"]:x["name"] for x in projects}}; project_id=c1.selectbox("Progetto",project_opts,format_func=project_opts.get)
                status=c2.selectbox("Stato",["Aperta","In lavorazione","In attesa","Chiusa"]); details=st.text_area("Descrizione / intervento")
                if st.form_submit_button("Registra",icon=":material/add:"):
                    if title.strip(): add_record("support_tickets",{"client_id":selected_id,"project_id":project_id,"title":title.strip(),"priority":priority,"status":status,"details":details.strip(),"date":date.today().isoformat()}); rerun_notice("Assistenza registrata")
                    else: st.error("Inserisci l'oggetto della richiesta.")
        if tickets: st.dataframe([{"Data":x.get("date"),"Oggetto":x.get("title"),"Progetto":_name(projects,x.get("project_id"),""),"Priorità":x.get("priority"),"Stato":x.get("status")} for x in sorted(tickets,key=lambda x:x.get("date",""),reverse=True)],hide_index=True,width="stretch")
        else: empty_state("Nessuna assistenza", "Qui manterrai lo storico delle richieste e degli interventi del cliente.")

    with notes_tab:
        with st.form("new_client_note",clear_on_submit=True):
            c1,c2=st.columns([1,2]); category=c1.selectbox("Categoria",["Generale","Commerciale","Tecnica","Amministrativa","Follow-up"]); text=c2.text_area("Nuova nota")
            if st.form_submit_button("Aggiungi nota",icon=":material/note_add:"):
                if text.strip(): add_record("notes",{"client_id":selected_id,"category":category,"text":text.strip(),"date":datetime.now().isoformat(timespec="minutes")}); rerun_notice("Nota aggiunta")
        if client_notes:
            for x in sorted(client_notes,key=lambda x:x.get("date",""),reverse=True):
                st.markdown(f"**{html.escape(x.get('category','Nota'))} · {html.escape(x.get('date',''))}**  \n{html.escape(x.get('text',''))}")
        else: empty_state("Nessuna nota", "Aggiungi note commerciali, tecniche o di follow-up senza sovraccaricare l'anagrafica.")

def _projects(data):
    clients, projects = data["clients"], data["projects"]
    if st.button("+ Nuovo progetto", icon=":material/create_new_folder:", type="primary", key="open_project_drawer"):
        _drawer_project()
    if not projects:
        empty_state("Nessun progetto", "Le commesse attive compariranno qui.")
        return
    st.dataframe([{"Progetto": item.get("name"), "Cliente": _name(clients, item.get("client_id")), "Stato": item.get("status"), "Scadenza": item.get("due_date"), "Valore": euro(item.get("value"))} for item in projects], hide_index=True, width="stretch")
    with st.expander("Aggiorna progetto", icon=":material/edit:"):
        options = {item["id"]: item["name"] for item in projects}
        selected_id = st.selectbox("Progetto", options, format_func=options.get, key="edit_project")
        selected = _by_id(projects)[selected_id]
        col1, col2 = st.columns(2)
        status = col1.selectbox("Stato", PROJECT_STATUSES, index=PROJECT_STATUSES.index(selected.get("status", "Da valutare")))
        due_date = col2.date_input("Scadenza", value=parse_date(selected.get("due_date")) or date.today(), format="DD/MM/YYYY")
        notes = st.text_area("Note", selected.get("notes", ""))
        if st.button("Salva progetto", icon=":material/save:"):
            update_record("projects", selected_id, {"status": status, "due_date": due_date.isoformat(), "notes": notes})
            rerun_notice("Progetto aggiornato")


def _tasks(data):
    projects, tasks = data["projects"], data["tasks"]
    with st.expander("Nuova attività", icon=":material/add_task:", expanded=not tasks):
        with st.form("new_task", clear_on_submit=True):
            col1, col2 = st.columns(2)
            title = col1.text_input("Attività")
            options = {"": "Non associata", **{item["id"]: item["name"] for item in projects}}
            project_id = col2.selectbox("Progetto", options, format_func=options.get)
            priority = col1.selectbox("Priorità", PRIORITIES, index=1)
            due_date = col2.date_input("Scadenza", value=date.today() + timedelta(days=7), format="DD/MM/YYYY")
            notes = st.text_area("Note")
            if st.form_submit_button("Aggiungi attività", icon=":material/add:"):
                if not title.strip():
                    st.error("Inserisci il titolo dell'attività.")
                else:
                    add_record("tasks", {"title": title.strip(), "project_id": project_id, "priority": priority, "due_date": due_date.isoformat(), "status": "Da fare", "notes": notes.strip()})
                    rerun_notice("Attività aggiunta")
    if not tasks:
        empty_state("Nessuna attività", "Usa questa area come agenda operativa dei progetti.")
        return
    st.dataframe([{"Attività": item.get("title"), "Progetto": _name(projects, item.get("project_id"), "Non associata"), "Priorità": item.get("priority"), "Scadenza": item.get("due_date"), "Stato": item.get("status")} for item in tasks], hide_index=True, width="stretch")
    with st.expander("Aggiorna attività", icon=":material/edit:"):
        options = {item["id"]: item["title"] for item in tasks}
        selected_id = st.selectbox("Attività", options, format_func=options.get, key="edit_task")
        selected = _by_id(tasks)[selected_id]
        col1, col2 = st.columns(2)
        status = col1.selectbox("Stato", TASK_STATUSES, index=TASK_STATUSES.index(selected.get("status", "Da fare")), key="task_status")
        priority = col2.selectbox("Priorità", PRIORITIES, index=PRIORITIES.index(selected.get("priority", "Media")), key="task_priority")
        if st.button("Salva attività", icon=":material/save:"):
            update_record("tasks", selected_id, {"status": status, "priority": priority})
            rerun_notice("Attività aggiornata")


def _payments(data):
    clients, projects, payments = data["clients"], data["projects"], data["payments"]
    expected, collected, overdue, _ = _totals(data)
    m1,m2,m3=st.columns(3); m1.metric("Da incassare",euro(expected)); m2.metric("Incassato",euro(collected)); m3.metric("Scaduto",euro(overdue))
    if st.button("+ Nuovo pagamento", icon=":material/payments:", type="primary", key="open_payment_drawer"):
        _drawer_payment()
    if payments:
        st.dataframe([{"Cliente": _name(clients, item.get("client_id")), "Progetto": _name(projects, item.get("project_id"), "-"), "Descrizione": item.get("description"), "Scadenza": item.get("due_date"), "Importo": euro(item.get("amount")), "Stato": _payment_state(item)} for item in sorted(payments, key=lambda row: row.get("due_date", ""))], hide_index=True, width="stretch")
        with st.expander("Aggiorna pagamento", icon=":material/edit:"):
            options = {item["id"]: f"{item.get('description')} · {_name(clients, item.get('client_id'))} · {euro(item.get('amount'))}" for item in payments}
            selected_id = st.selectbox("Pagamento", options, format_func=options.get)
            selected = _by_id(payments)[selected_id]
            status = st.selectbox("Stato pagamento", PAYMENT_STATUSES, index=PAYMENT_STATUSES.index(selected.get("status", "Previsto")))
            if st.button("Salva stato", icon=":material/save:"):
                paid_date = date.today().isoformat() if status == "Incassato" else ""
                update_record("payments", selected_id, {"status": status, "paid_date": paid_date})
                rerun_notice("Pagamento aggiornato")
    else:
        empty_state("Nessun pagamento", "Inserisci la prima scadenza collegata a un cliente.")


def _accounting(data):
    clients, projects, payments, expenses = data["clients"], data["projects"], data["payments"], data["expenses"]
    expected, collected, overdue, spent = _totals(data)
    cols = st.columns(4)
    cols[0].metric("Incassato", euro(collected))
    cols[1].metric("Da incassare", euro(expected))
    cols[2].metric("Scaduto", euro(overdue))
    cols[3].metric("Margine", euro(collected - spent))

    f1, f2, f3 = st.columns([2,2,1])
    client_options = {"": "Tutti i clienti", **{x["id"]: x["name"] for x in clients}}
    project_options = {"": "Tutte le commesse", **{x["id"]: x["name"] for x in projects}}
    client_filter = f1.selectbox("Cliente", client_options, format_func=client_options.get, key="account_client_filter")
    project_filter = f2.selectbox("Commessa", project_options, format_func=project_options.get, key="account_project_filter")
    year_filter = f3.selectbox("Anno", ["Tutti", *[str(y) for y in range(date.today().year, date.today().year-5, -1)]], key="account_year")

    def accepted(client_id="", project_id="", day_value=""):
        if client_filter and client_id != client_filter: return False
        if project_filter and project_id != project_filter: return False
        d = parse_date(day_value)
        return year_filter == "Tutti" or (d and str(d.year) == year_filter)

    ledger = []
    for item in payments:
        if item.get("status") == "Annullato": continue
        day_value = item.get("paid_date") if item.get("status") == "Incassato" else item.get("due_date")
        if not accepted(item.get("client_id", ""), item.get("project_id", ""), day_value): continue
        ledger.append({"date": parse_date(day_value), "kind": "Entrata", "description": item.get("description", "Pagamento"), "client_id": item.get("client_id", ""), "project_id": item.get("project_id", ""), "amount": float(item.get("amount") or 0), "state": _payment_state(item)})
    for item in expenses:
        project = _by_id(projects).get(item.get("project_id"), {})
        client_id = project.get("client_id", "")
        if not accepted(client_id, item.get("project_id", ""), item.get("date")): continue
        ledger.append({"date": parse_date(item.get("date")), "kind": "Uscita", "description": item.get("description", "Costo"), "client_id": client_id, "project_id": item.get("project_id", ""), "amount": -float(item.get("amount") or 0), "state": item.get("category", "Costo")})

    st.subheader("Prima nota gestionale")
    if ledger:
        for row in sorted(ledger, key=lambda x: x["date"] or date.min, reverse=True):
            client = _by_id(clients).get(row["client_id"], {})
            project = _by_id(projects).get(row["project_id"], {})
            href = "?module=clienti_progetti"
            if row["client_id"]: href += f"&client={row['client_id']}"
            if row["project_id"]: href += f"&project={row['project_id']}"
            css = " overdue" if row["state"] == "Scaduto" else ""
            meta = " · ".join(x for x in [client.get("name", ""), project.get("name", ""), row["state"]] if x)
            st.markdown(f"<a class='ledger-row{css}' href='{href}' target='_self'><span>{row['date'].strftime('%d/%m/%Y') if row['date'] else '-'}</span><span><b>{html.escape(row['kind'])} · {html.escape(row['description'])}</b><small>{html.escape(meta)}</small></span><span></span><span class='amount'>{euro(row['amount'])}</span></a>", unsafe_allow_html=True)
    else:
        empty_state("Nessun movimento", "Non ci sono movimenti per i filtri selezionati.")

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("#### Inserimenti")
        if st.button("+ Registra costo", icon=":material/receipt_long:", type="primary", key="open_expense_drawer"):
            _drawer_expense()
        if st.button("+ Registra pagamento", icon=":material/payments:", key="open_payment_from_accounting"):
            _drawer_payment()
    with right:
        st.markdown("#### Situazione per cliente")
        rows=[]
        for client in clients:
            exp, inc, scad, costs = _totals(data, client_id=client["id"])
            if exp or inc or costs:
                rows.append({"Cliente": client["name"], "Incassato": euro(inc), "Da incassare": euro(exp), "Scaduto": euro(scad), "Costi": euro(costs), "Margine": euro(inc-costs)})
        if rows: st.dataframe(rows, hide_index=True, width="stretch")
        else: st.caption("Nessun dato economico disponibile.")
    st.info("Contabilità gestionale interna: non sostituisce la contabilità fiscale.")


def _agenda(data):
    clients, projects, appointments = data["clients"], data["projects"], data["appointments"]
    tasks = [x for x in data["tasks"] if x.get("status") != "Completata"]
    payments = [x for x in data["payments"] if x.get("status", "Previsto") == "Previsto"]

    a1,a2,a3=st.columns([1,1,4])
    if a1.button("+ Appuntamento", icon=":material/event:", type="primary", key="agenda_drawer_appointment"):
        st.session_state["drawer_appointment_defaults"]={"date":date.today().isoformat(),"time":"09:00"}; _drawer_appointment()
    if a2.button("+ Cliente", icon=":material/person_add:", key="agenda_drawer_client"):
        _drawer_client()

    f1, f2, f3 = st.columns([1.45,2,2])
    view = f1.segmented_control("Vista", ["Giorno", "Settimana", "Mese"], default="Mese", key="agenda_view")
    client_opts = {"": "Tutti i clienti", **{x["id"]: x["name"] for x in clients}}
    project_opts = {"": "Tutti i progetti", **{x["id"]: x["name"] for x in projects}}
    cf = f2.selectbox("Cliente", client_opts, format_func=client_opts.get, key="agenda_client")
    pf = f3.selectbox("Progetto", project_opts, format_func=project_opts.get, key="agenda_project")
    requested_date = parse_date(st.query_params.get("agenda_date"))
    requested_view = st.query_params.get("agenda_view")
    if requested_view in {"Giorno", "Settimana", "Mese"}:
        view = requested_view
    focus = st.date_input("Data di riferimento", value=requested_date or date.today(), format="DD/MM/YYYY", key="agenda_focus")

    events=[]
    for x in appointments:
        if x.get("status") == "Annullato": continue
        events.append({"date":parse_date(x.get("date")),"time":x.get("start_time", ""),"kind":"Appuntamento","title":x.get("title", ""),"client_id":x.get("client_id", ""),"project_id":x.get("project_id", "")})
    for x in tasks:
        project=_by_id(projects).get(x.get("project_id"),{})
        events.append({"date":parse_date(x.get("due_date")),"time":"","kind":"Attività","title":x.get("title", ""),"client_id":project.get("client_id", ""),"project_id":x.get("project_id", "")})
    for x in payments:
        events.append({"date":parse_date(x.get("due_date")),"time":"","kind":"Incasso","title":f"{x.get('description','Pagamento')} · {euro(x.get('amount'))}","client_id":x.get("client_id", ""),"project_id":x.get("project_id", "")})
    events=[x for x in events if x["date"] and (not cf or x["client_id"]==cf) and (not pf or x["project_id"]==pf)]

    def event_card(x):
        client_name=_name(clients,x["client_id"],"")
        project_name=_name(projects,x["project_id"],"")
        title=html.escape((x['time']+' '+x['kind']+' · '+x['title']).strip())
        links=[]
        if x["client_id"]:
            links.append(f"<a class='agenda-entity-link' href='?module=clienti_progetti&client={x['client_id']}' target='_self'>👤 {html.escape(client_name)}</a>")
        if x["project_id"]:
            links.append(f"<a class='agenda-entity-link' href='?module=clienti_progetti&project={x['project_id']}' target='_self'>📁 {html.escape(project_name)}</a>")
        return f"<div class='agenda-day-card'><b>{title}</b><div class='agenda-entity-links'>{''.join(links)}</div></div>"

    if view == "Giorno":
        st.markdown(f"### Giornata · {focus.strftime('%d/%m/%Y')}")
        rows=sorted([x for x in events if x["date"]==focus], key=lambda x:x["time"])
        by_hour = {}
        for x in rows:
            hour = int((x.get("time") or "09:00")[:2]) if (x.get("time") or "")[:2].isdigit() else 9
            by_hour.setdefault(hour, []).append(x)
        for hour in range(7, 21):
            ctime, cbody, cadd = st.columns([1,7,1])
            ctime.markdown(f"**{hour:02d}:00**")
            with cbody:
                if by_hour.get(hour):
                    for x in by_hour[hour]: st.markdown(event_card(x), unsafe_allow_html=True)
                else: st.caption("Libero")
            if cadd.button("+", key=f"slot_{focus}_{hour}", help=f"Nuovo appuntamento alle {hour:02d}:00"):
                st.session_state["drawer_appointment_defaults"]={"date":focus.isoformat(),"time":f"{hour:02d}:00"}
                _drawer_appointment()
    elif view == "Settimana":
        monday=focus-timedelta(days=focus.weekday())
        names=["Lun","Mar","Mer","Gio","Ven","Sab","Dom"]
        cells=[]
        for i in range(7):
            d=monday+timedelta(days=i); cls=" today" if d==date.today() else ""
            day_events=sorted([x for x in events if x["date"]==d], key=lambda x:x["time"])
            bits=[]
            for x in day_events[:5]:
                href="?module=clienti_progetti"+(f"&client={x['client_id']}" if x["client_id"] else "")+(f"&project={x['project_id']}" if x["project_id"] else "")
                kindcls="payment" if x["kind"]=="Incasso" else "task" if x["kind"]=="Attività" else ""
                bits.append(f"<a class='week-event {kindcls}' href='{href}' target='_self'>{html.escape((x['time']+' '+x['title']).strip())}</a>")
            cells.append(f"<div class='week-day{cls}'><div class='dow'>{names[i]}</div><div class='num'>{d.day}</div>{''.join(bits)}</div>")
        st.markdown("<div class='week-strip'>"+"".join(cells)+"</div>", unsafe_allow_html=True)
    else:
        # Reuse the common calendar, enriched with all operational events.
        synthetic=[]
        for i,x in enumerate(events):
            synthetic.append({"id":str(i),"date":x["date"].isoformat(),"start_time":x["time"],"title":f"{x['kind']} · {x['title']}","client_id":x["client_id"],"project_id":x["project_id"]})
        st.markdown(_calendar_html(synthetic, focus, clients), unsafe_allow_html=True)

    st.markdown("### Inserimento rapido")
    q1,q2=st.columns(2)
    if q1.button("+ Nuovo cliente", icon=":material/person_add:", key="agenda_quick_client", width="stretch"):
        _drawer_client()
    if q2.button("+ Nuovo progetto", icon=":material/create_new_folder:", key="agenda_quick_project", width="stretch"):
        _drawer_project()

    st.subheader("Prossimi impegni")
    upcoming=sorted([x for x in events if x["date"]>=date.today()], key=lambda x:(x["date"],x["time"]))[:15]
    if upcoming:
        for x in upcoming:
            st.markdown(event_card(x), unsafe_allow_html=True)
    else: empty_state("Nessun impegno futuro", "Aggiungi un appuntamento, un'attività o una scadenza.")

def _project_profile(data, project_id):
    project = _by_id(data["projects"]).get(project_id)
    if not project:
        return False
    client = _by_id(data["clients"]).get(project.get("client_id"), {})
    payments = [x for x in data["payments"] if x.get("project_id") == project_id]
    tasks = [x for x in data["tasks"] if x.get("project_id") == project_id]
    appointments = [x for x in data["appointments"] if x.get("project_id") == project_id]
    expenses = [x for x in data["expenses"] if x.get("project_id") == project_id]
    tickets = [x for x in data.get("support_tickets", []) if x.get("project_id") == project_id]
    notes = [x for x in data.get("notes", []) if x.get("project_id") == project_id]
    documents = [x for x in data.get("documents", []) if x.get("project_id") == project_id]
    expected, collected, overdue, spent = _totals(data, project_id=project_id)
    value = float(project.get("value") or 0)
    progress = int(project.get("progress") or (100 if project.get("status") == "Concluso" else 0))

    top1, top2 = st.columns([1, 5])
    with top1:
        if st.button("← Gestionale", key="back_project_profile"):
            st.query_params.pop("project", None); st.rerun()
    with top2:
        if client:
            st.markdown(f"[← Scheda cliente · {html.escape(client.get('name',''))}](?module=clienti_progetti&client={client.get('id','')})")

    st.markdown(f"## {html.escape(project.get('name', ''))}")
    st.caption(f"{project.get('status','')} · scadenza {project.get('due_date') or '-'} · referente {project.get('owner') or '-'}")
    cols = st.columns(6)
    cols[0].metric("Valore", euro(value)); cols[1].metric("Avanzamento", f"{progress}%")
    cols[2].metric("Incassato", euro(collected)); cols[3].metric("Da incassare", euro(expected))
    cols[4].metric("Costi", euro(spent)); cols[5].metric("Margine", euro(collected-spent))
    st.progress(max(0, min(progress, 100)) / 100)
    if overdue: st.warning(f"Scadenze economiche arretrate: {euro(overdue)}")

    tabs = st.tabs(["Dashboard", "Attività", "Timeline", "Economico", "Appuntamenti", "Documenti", "Assistenza", "Note"])
    dash, task_tab, timeline_tab, money_tab, agenda_tab, docs_tab, support_tab, notes_tab = tabs

    with dash:
        l, r = st.columns([2, 1], gap="large")
        with l:
            st.markdown("#### Obiettivo e note")
            st.write(project.get("notes") or "Nessuna descrizione inserita.")
            open_tasks=[x for x in tasks if x.get("status") != "Completata"]
            upcoming=sorted([x for x in appointments if parse_date(x.get("date")) and parse_date(x.get("date")) >= date.today() and x.get("status") != "Annullato"], key=lambda x:(x.get("date",""),x.get("start_time","")))
            st.markdown("#### Prossime azioni")
            if open_tasks:
                for x in sorted(open_tasks,key=lambda x:x.get("due_date") or "9999")[:5]: st.write(f"• {x.get('due_date') or '-'} · **{x.get('title','')}** · {x.get('status','')}")
            else: st.caption("Nessuna attività aperta.")
            if upcoming:
                x=upcoming[0]; st.info(f"Prossimo appuntamento: {x.get('date')} {x.get('start_time') or ''} · {x.get('title','')}")
        with r:
            st.markdown("#### Stato commessa")
            st.write(f"Cliente: **{client.get('name','-')}**")
            st.write(f"Attività aperte: **{len([x for x in tasks if x.get('status') != 'Completata'])}**")
            st.write(f"Documenti: **{len(documents)}**")
            st.write(f"Assistenze aperte: **{len([x for x in tickets if x.get('status') != 'Chiusa'])}**")
            st.write(f"Appuntamenti: **{len(appointments)}**")
        with st.expander("Aggiorna commessa", icon=":material/edit:"):
            with st.form("project_profile_edit"):
                c1,c2,c3=st.columns(3)
                status=c1.selectbox("Stato",PROJECT_STATUSES,index=PROJECT_STATUSES.index(project.get("status")) if project.get("status") in PROJECT_STATUSES else 0)
                due=c2.text_input("Scadenza",project.get("due_date") or "")
                owner=c3.text_input("Referente",project.get("owner") or "")
                value_edit=c1.number_input("Valore €",min_value=0.0,value=value,step=100.0)
                progress_edit=c2.slider("Avanzamento %",0,100,progress,5)
                description=st.text_area("Obiettivo / note",project.get("notes") or "")
                if st.form_submit_button("Salva commessa",icon=":material/save:"):
                    update_record("projects",project_id,{"status":status,"due_date":due,"owner":owner,"value":value_edit,"progress":progress_edit,"notes":description}); rerun_notice("Commessa aggiornata")

    with task_tab:
        with st.expander("Nuova attività", icon=":material/add_task:"):
            with st.form("project_new_task",clear_on_submit=True):
                c1,c2,c3=st.columns(3); title=c1.text_input("Attività"); due=c2.text_input("Scadenza"); priority=c3.selectbox("Priorità",PRIORITIES)
                if st.form_submit_button("Aggiungi attività"):
                    if title.strip(): add_record("tasks",{"title":title.strip(),"project_id":project_id,"due_date":due,"priority":priority,"status":"Da fare"}); rerun_notice("Attività aggiunta")
        if tasks: st.dataframe([{"Attività":x.get("title"),"Scadenza":x.get("due_date"),"Priorità":x.get("priority"),"Stato":x.get("status")} for x in sorted(tasks,key=lambda x:x.get("due_date") or "9999")],hide_index=True,width="stretch")
        else: empty_state("Nessuna attività","Aggiungi la prima attività della commessa.")

    with timeline_tab:
        timeline=[]
        for x in tasks: timeline.append((x.get("due_date") or x.get("created_at","")[:10],"Attività",x.get("title",""),x.get("status","")))
        for x in appointments: timeline.append((x.get("date") or "","Appuntamento",x.get("title",""),x.get("status","")))
        for x in payments: timeline.append((x.get("paid_date") or x.get("due_date") or "","Entrata",x.get("description") or "Pagamento",f"{euro(x.get('amount'))} · {_payment_state(x)}"))
        for x in expenses: timeline.append((x.get("date") or "","Uscita",x.get("description") or x.get("category") or "Costo",euro(x.get("amount"))))
        for x in tickets: timeline.append((x.get("date") or x.get("created_at","")[:10],"Assistenza",x.get("title",""),x.get("status","")))
        for x in notes: timeline.append((x.get("date") or x.get("created_at","")[:10],"Nota",x.get("title") or x.get("category") or "Nota",x.get("text") or x.get("content") or ""))
        if timeline:
            for d,k,t,detail in sorted(timeline,key=lambda x:x[0] or "",reverse=True): st.markdown(f"**{d or '-'} · {k} — {html.escape(str(t))}**  \n{html.escape(str(detail))}")
        else: empty_state("Timeline vuota","Le attività della commessa compariranno qui in ordine cronologico.")

    with money_tab:
        c1,c2,c3,c4=st.columns(4); c1.metric("Valore",euro(value)); c2.metric("Incassato",euro(collected)); c3.metric("Da incassare",euro(expected)); c4.metric("Margine",euro(collected-spent))
        movements=[]
        for x in payments: movements.append({"Data":x.get("paid_date") or x.get("due_date") or "","Tipo":"Entrata","Descrizione":x.get("description") or "Pagamento","Importo":euro(x.get("amount")),"Stato":_payment_state(x)})
        for x in expenses: movements.append({"Data":x.get("date") or "","Tipo":"Uscita","Descrizione":x.get("description") or x.get("category") or "Costo","Importo":euro(x.get("amount")),"Stato":"Registrata"})
        if movements: st.dataframe(sorted(movements,key=lambda x:x["Data"],reverse=True),hide_index=True,width="stretch")
        else: empty_state("Nessun movimento","Entrate e costi della commessa compariranno qui.")

    with agenda_tab:
        if appointments: st.dataframe([{"Data":x.get("date"),"Ora":x.get("start_time"),"Appuntamento":x.get("title"),"Stato":x.get("status")} for x in sorted(appointments,key=lambda x:(x.get("date",""),x.get("start_time","")))],hide_index=True,width="stretch")
        else: empty_state("Nessun appuntamento","Non ci sono appuntamenti collegati alla commessa.")

    with docs_tab:
        if documents: st.dataframe([{"Documento":x.get("name") or x.get("title") or x.get("filename"),"Tipo":x.get("type") or x.get("category") or "-","Data":x.get("date") or x.get("created_at","")[:10]} for x in documents],hide_index=True,width="stretch")
        else: empty_state("Nessun documento","I documenti associati alla commessa compariranno qui.")

    with support_tab:
        if tickets: st.dataframe([{"Data":x.get("date"),"Oggetto":x.get("title"),"Priorità":x.get("priority"),"Stato":x.get("status")} for x in sorted(tickets,key=lambda x:x.get("date","") or "",reverse=True)],hide_index=True,width="stretch")
        else: empty_state("Nessuna assistenza","Non risultano interventi collegati alla commessa.")

    with notes_tab:
        with st.form("project_note",clear_on_submit=True):
            c1,c2=st.columns([1,3]); category=c1.selectbox("Categoria",["Operativa","Tecnica","Commerciale","Amministrativa","Promemoria"]); text_note=c2.text_area("Nuova nota")
            if st.form_submit_button("Salva nota"):
                if text_note.strip(): add_record("notes",{"project_id":project_id,"client_id":project.get("client_id"),"date":date.today().isoformat(),"category":category,"text":text_note.strip()}); rerun_notice("Nota salvata")
        if notes:
            for x in sorted(notes,key=lambda x:x.get("date") or x.get("created_at","")[:10],reverse=True): st.markdown(f"**{x.get('date') or x.get('created_at','')[:10]} · {x.get('category','Nota')}**  \n{x.get('text') or x.get('content') or ''}")
        else: st.caption("Nessuna nota specifica della commessa.")
    return True


def _crm(data):
    st.subheader("CRM commerciale")
    st.caption("Contatti, opportunità, preventivi e follow-up fino alla conversione in cliente e commessa.")
    leads = data.get("leads", [])
    quotes = data.get("quotes", [])
    followups = data.get("followups", [])
    stages = ["Nuovo contatto", "Analisi", "Preventivo", "Trattativa", "Acquisito", "Perso"]
    open_leads = [x for x in leads if x.get("stage") not in {"Acquisito", "Perso"}]
    pipeline_value = sum(float(x.get("estimated_value") or 0) for x in open_leads)
    won = [x for x in leads if x.get("stage") == "Acquisito"]
    due_followups = [x for x in followups if x.get("status") != "Completato" and parse_date(x.get("date")) and parse_date(x.get("date")) <= date.today()]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Opportunità aperte", len(open_leads)); c2.metric("Valore pipeline", euro(pipeline_value)); c3.metric("Acquisiti", len(won)); c4.metric("Follow-up da fare", len(due_followups))

    tab1,tab2,tab3,tab4=st.tabs(["Pipeline","Lead","Preventivi","Follow-up"])
    with tab1:
        cols=st.columns(6)
        for col,stage in zip(cols,stages):
            items=[x for x in leads if x.get("stage","Nuovo contatto")==stage]
            with col:
                st.markdown(f"**{stage}**  \n{len(items)} contatti")
                for x in items:
                    st.markdown(f"**{x.get('company') or x.get('name','Contatto')}**  \n{euro(x.get('estimated_value'))}  \n{x.get('next_action') or ''}")
    with tab2:
        with st.expander("Nuovo contatto / opportunità", expanded=not leads):
            with st.form("new_lead",clear_on_submit=True):
                a,b,c=st.columns(3); name=a.text_input("Referente *"); company=b.text_input("Azienda"); source=c.selectbox("Origine",["Sito VA Digital","Passaparola","Social","Fiverr","Email","Telefono","Altro"])
                a,b,c=st.columns(3); email=a.text_input("Email"); phone=b.text_input("Telefono"); stage=c.selectbox("Fase",stages[:-2])
                a,b=st.columns(2); service=a.text_input("Servizio / esigenza"); value=b.number_input("Valore stimato",min_value=0.0,step=100.0)
                next_action=st.text_input("Prossima azione"); notes=st.text_area("Note commerciali")
                if st.form_submit_button("Salva opportunità",type="primary"):
                    if name.strip() or company.strip():
                        add_record("leads",{"name":name.strip(),"company":company.strip(),"source":source,"email":email.strip(),"phone":phone.strip(),"stage":stage,"service":service.strip(),"estimated_value":value,"next_action":next_action.strip(),"notes":notes.strip()}); rerun_notice("Opportunità creata")
                    else: st.warning("Inserisci almeno referente o azienda.")
        if leads:
            opts={x["id"]:f"{x.get('company') or x.get('name')} · {x.get('stage','Nuovo contatto')}" for x in leads}
            lead_id=st.selectbox("Apri opportunità",opts,format_func=opts.get)
            lead=next(x for x in leads if x["id"]==lead_id)
            st.markdown(f"### {lead.get('company') or lead.get('name')}")
            st.caption(" · ".join(x for x in [lead.get('name'),lead.get('email'),lead.get('phone'),lead.get('source')] if x))
            a,b,c=st.columns([1,1,2]); new_stage=a.selectbox("Fase",stages,index=stages.index(lead.get("stage","Nuovo contatto")),key=f"stage_{lead_id}"); next_action=b.text_input("Prossima azione",lead.get("next_action",""),key=f"next_{lead_id}"); est=c.number_input("Valore stimato",min_value=0.0,value=float(lead.get("estimated_value") or 0),step=100.0,key=f"est_{lead_id}")
            if st.button("Aggiorna opportunità",key=f"upd_{lead_id}"):
                update_record("leads",lead_id,{"stage":new_stage,"next_action":next_action.strip(),"estimated_value":est}); rerun_notice("Opportunità aggiornata")
            if lead.get("stage") != "Acquisito":
                with st.expander("Converti in cliente + commessa"):
                    project_name=st.text_input("Nome prima commessa",lead.get("service") or "Nuovo progetto",key=f"conv_proj_{lead_id}")
                    create_project=st.checkbox("Crea anche la prima commessa",True,key=f"conv_check_{lead_id}")
                    if st.button("Acquisisci cliente",type="primary",key=f"conv_{lead_id}"):
                        client=add_record("clients",{"name":lead.get("company") or lead.get("name"),"contact_person":lead.get("name", ""),"email":lead.get("email", ""),"phone":lead.get("phone", ""),"notes":f"Acquisito da CRM · origine: {lead.get('source','')}\n{lead.get('notes','')}","lead_id":lead_id})
                        project=None
                        if create_project:
                            project=add_record("projects",{"name":project_name.strip() or "Nuovo progetto","client_id":client["id"],"status":"Da avviare","due_date":"","value":float(lead.get("estimated_value") or 0),"owner":"","notes":"Commessa creata dalla conversione CRM"})
                        update_record("leads",lead_id,{"stage":"Acquisito","client_id":client["id"],"project_id":project["id"] if project else "","converted_at":datetime.now().isoformat(timespec="minutes")})
                        st.query_params["client"]=client["id"]; st.rerun()
        else: empty_state("Pipeline vuota","Inserisci il primo contatto commerciale.")
    with tab3:
        if not leads: empty_state("Nessuna opportunità","Crea prima un lead per registrare un preventivo.")
        else:
            with st.form("new_quote",clear_on_submit=True):
                opts={x["id"]:x.get("company") or x.get("name") for x in leads}; a,b,c=st.columns(3); lid=a.selectbox("Opportunità",opts,format_func=opts.get); title=b.text_input("Preventivo / proposta *"); amount=c.number_input("Importo",min_value=0.0,step=100.0)
                a,b,c=st.columns(3); qdate=a.date_input("Data",date.today()); valid=b.date_input("Valido fino",date.today()); status=c.selectbox("Stato",["Bozza","Inviato","Accettato","Rifiutato","Scaduto"])
                if st.form_submit_button("Registra preventivo"):
                    if title.strip(): add_record("quotes",{"lead_id":lid,"title":title.strip(),"amount":amount,"date":qdate.isoformat(),"valid_until":valid.isoformat(),"status":status}); rerun_notice("Preventivo registrato")
            if quotes: st.dataframe([{"Data":x.get("date"),"Opportunità":next((y.get("company") or y.get("name") for y in leads if y["id"]==x.get("lead_id")),"-"),"Preventivo":x.get("title"),"Importo":euro(x.get("amount")),"Stato":x.get("status"),"Valido fino":x.get("valid_until")} for x in sorted(quotes,key=lambda z:z.get("date",""),reverse=True)],hide_index=True,width="stretch")
    with tab4:
        if leads:
            with st.form("new_followup",clear_on_submit=True):
                opts={x["id"]:x.get("company") or x.get("name") for x in leads}; a,b,c=st.columns(3); lid=a.selectbox("Opportunità",opts,format_func=opts.get); fdate=b.date_input("Data follow-up",date.today()); kind=c.selectbox("Tipo",["Telefonata","Email","Riunione","Promemoria","Invio proposta"])
                text=st.text_input("Azione / promemoria *")
                if st.form_submit_button("Aggiungi follow-up"):
                    if text.strip(): add_record("followups",{"lead_id":lid,"date":fdate.isoformat(),"type":kind,"text":text.strip(),"status":"Da fare"}); rerun_notice("Follow-up aggiunto")
        if followups:
            st.dataframe([{"Data":x.get("date"),"Opportunità":next((y.get("company") or y.get("name") for y in leads if y["id"]==x.get("lead_id")),"-"),"Tipo":x.get("type"),"Azione":x.get("text"),"Stato":x.get("status")} for x in sorted(followups,key=lambda z:z.get("date",""))],hide_index=True,width="stretch")
        else: empty_state("Nessun follow-up","Programma qui richiami, email e prossime azioni commerciali.")


def render_agenda(module=None):
    module_header("Agenda", "Calendario operativo collegato a clienti, progetti, attività e scadenze.", "VA DIGITAL · AGENDA")
    _agenda(load_data())


def render_accounting(module=None):
    module_header("Contabilità", "Contabilità gestionale collegata a clienti e commesse.", "VA DIGITAL · CONTABILITÀ")
    _accounting(load_data())

def render(module):
    module_header(module["name"], module.get("description", ""), "GESTIONALE VA DIGITAL")
    data = load_data()
    requested_project = st.query_params.get("project")
    requested_client = st.query_params.get("client")
    requested_section = (st.query_params.get("section") or "").casefold()

    if requested_project and _project_profile(data, requested_project):
        return
    if requested_client:
        _client_profile(data)
        return

    direct_sections = {
        "clienti": _client_profile,
        "progetti": _projects,
        "agenda": _agenda,
        "contabilità": _accounting,
        "contabilita": _accounting,
        "pagamenti": _payments,
        "attività": _tasks,
        "attivita": _tasks,
        "crm": _crm,
    }
    if requested_section in direct_sections:
        if st.button("← Torna al gestionale", key="back_direct_section"):
            st.query_params.pop("section", None)
            st.rerun()
        direct_sections[requested_section](data)
        return

    tabs = st.tabs(["Cruscotto", "CRM", "Scheda cliente", "Progetti", "Attività", "Pagamenti"])
    with tabs[0]: _overview(data)
    with tabs[1]: _crm(data)
    with tabs[2]: _client_profile(data)
    with tabs[3]: _projects(data)
    with tabs[4]: _tasks(data)
    with tabs[5]: _payments(data)
