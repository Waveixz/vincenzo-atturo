import html
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from core.storage import add_record, delete_record, load_data, update_record
from core.ui import empty_state, euro, hub_url, module_header, month_calendar, parse_date, record_link, rerun_notice


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
    with st.expander("Nuovo cliente", icon=":material/person_add:", expanded=expanded):
        with st.form("new_client", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Cliente o ragione sociale")
            contact = col2.text_input("Referente")
            email = col1.text_input("Email")
            phone = col2.text_input("Telefono")
            vat_code = col1.text_input("Partita IVA")
            tax_code = col2.text_input("Codice fiscale")
            address = st.text_input("Indirizzo")
            notes = st.text_area("Esigenze e note")
            if st.form_submit_button("Aggiungi cliente", icon=":material/add:"):
                if not name.strip():
                    st.error("Inserisci il nome del cliente.")
                else:
                    add_record("clients", {
                        "name": name.strip(), "contact": contact.strip(), "email": email.strip(),
                        "phone": phone.strip(), "vat_code": vat_code.strip(), "tax_code": tax_code.strip(),
                        "address": address.strip(), "notes": notes.strip(), "status": "Attivo",
                    })
                    rerun_notice("Cliente aggiunto")


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
    requested_id = st.query_params.get("client_id")
    option_ids = list(options)
    selected_index = option_ids.index(requested_id) if requested_id in options else 0
    selected_id = st.selectbox("Apri la scheda cliente", option_ids, index=selected_index, format_func=options.get)
    client = _by_id(clients)[selected_id]
    projects = [item for item in data["projects"] if item.get("client_id") == selected_id]
    project_ids = {item["id"] for item in projects}
    payments = [item for item in data["payments"] if item.get("client_id") == selected_id]
    appointments = [item for item in data["appointments"] if item.get("client_id") == selected_id]
    tasks = [item for item in data["tasks"] if item.get("project_id") in project_ids]
    documents = _client_documents(data, client)
    expected, collected, overdue, spent = _totals(data, client_id=selected_id)

    st.markdown(f"### {html.escape(client.get('name', ''))}")
    st.caption(" · ".join(value for value in [client.get("contact"), client.get("email"), client.get("phone")] if value))
    metrics = st.columns(5)
    metrics[0].metric("Progetti", len(projects))
    metrics[1].metric("Da incassare", euro(expected))
    metrics[2].metric("Incassato", euro(collected))
    metrics[3].metric("Scaduto", euro(overdue))
    metrics[4].metric("Costi commesse", euro(spent))

    summary_tab, projects_tab, payments_tab, appointments_tab, documents_tab = st.tabs([
        "Riepilogo", "Progetti e attività", "Pagamenti", "Appuntamenti", "Documenti"
    ])
    with summary_tab:
        left, right = st.columns(2)
        with left:
            st.markdown("**Dati cliente**")
            st.write(client.get("address") or "Indirizzo non inserito")
            st.write(f"P. IVA: {client.get('vat_code') or '-'}")
            st.write(f"Codice fiscale: {client.get('tax_code') or '-'}")
        with right:
            st.markdown("**Note operative**")
            st.write(client.get("notes") or "Nessuna nota")
        with st.expander("Aggiorna anagrafica", icon=":material/edit:"):
            with st.form("edit_client"):
                col1, col2 = st.columns(2)
                contact = col1.text_input("Referente", client.get("contact", ""))
                email = col2.text_input("Email", client.get("email", ""))
                phone = col1.text_input("Telefono", client.get("phone", ""))
                status = col2.selectbox("Stato", ["Attivo", "Potenziale", "Archiviato"], index=["Attivo", "Potenziale", "Archiviato"].index(client.get("status", "Attivo")))
                address = st.text_input("Indirizzo", client.get("address", ""))
                notes = st.text_area("Note", client.get("notes", ""))
                if st.form_submit_button("Salva anagrafica", icon=":material/save:"):
                    update_record("clients", selected_id, {"contact": contact, "email": email, "phone": phone, "status": status, "address": address, "notes": notes})
                    rerun_notice("Anagrafica aggiornata")
    with projects_tab:
        if projects:
            for item in projects:
                st.markdown(f"{record_link(item.get('name', 'Progetto'), module='clienti_progetti', section='project', project_id=item.get('id'))} · {html.escape(item.get('status', ''))} · {euro(item.get('value'))}", unsafe_allow_html=True)
        else:
            empty_state("Nessun progetto", "Il cliente non ha ancora commesse collegate.")
        if tasks:
            st.markdown("**Attività collegate**")
            st.dataframe([{"Attività": item.get("title"), "Scadenza": item.get("due_date"), "Stato": item.get("status")} for item in tasks], hide_index=True, width="stretch")
    with payments_tab:
        if payments:
            st.dataframe([{"Descrizione": item.get("description"), "Scadenza": item.get("due_date"), "Importo": euro(item.get("amount")), "Stato": _payment_state(item)} for item in payments], hide_index=True, width="stretch")
        else:
            empty_state("Nessun pagamento", "Registra le scadenze dalla sezione Pagamenti.")
    with appointments_tab:
        if appointments:
            st.dataframe([{"Data": item.get("date"), "Ora": item.get("start_time"), "Appuntamento": item.get("title"), "Stato": item.get("status")} for item in appointments], hide_index=True, width="stretch")
        else:
            empty_state("Nessun appuntamento", "Gli incontri collegati al cliente compariranno qui.")
    with documents_tab:
        if documents:
            st.dataframe([{"Documento": item.get("title"), "Categoria": item.get("category"), "File": Path(item.get("path", "")).name} for item in documents], hide_index=True, width="stretch")
        else:
            empty_state("Nessun documento", "Compila o archivia un documento indicando questo cliente.")


def _project_detail(data, project):
    client = _by_id(data["clients"]).get(project.get("client_id"), {})
    project_id = project.get("id")
    tasks = [item for item in data["tasks"] if item.get("project_id") == project_id]
    payments = [item for item in data["payments"] if item.get("project_id") == project_id]
    expenses = [item for item in data["expenses"] if item.get("project_id") == project_id]
    appointments = [item for item in data["appointments"] if item.get("project_id") == project_id]
    expected, collected, overdue, spent = _totals(data, project_id=project_id)

    st.markdown(f"### {html.escape(project.get('name', ''))}")
    if client:
        st.markdown(f"Cliente: {record_link(client.get('name', 'Cliente'), module='clienti_progetti', section='client', client_id=client.get('id'))}", unsafe_allow_html=True)
    metrics = st.columns(5)
    metrics[0].metric("Valore commessa", euro(project.get("value")))
    metrics[1].metric("Da incassare", euro(expected))
    metrics[2].metric("Incassato", euro(collected))
    metrics[3].metric("Costi", euro(spent))
    metrics[4].metric("Margine", euro(collected - spent))
    st.caption(f"Stato: {project.get('status', '')} · Scadenza: {project.get('due_date', '-')}")

    details = st.tabs(["Attività", "Pagamenti", "Costi", "Appuntamenti"])
    with details[0]:
        if tasks:
            st.dataframe([{"Attività": item.get("title"), "Scadenza": item.get("due_date"), "Priorità": item.get("priority"), "Stato": item.get("status")} for item in tasks], hide_index=True, width="stretch")
        else:
            empty_state("Nessuna attività", "Non sono presenti attività per questa commessa.")
    with details[1]:
        if payments:
            st.dataframe([{"Descrizione": item.get("description"), "Scadenza": item.get("due_date"), "Importo": euro(item.get("amount")), "Stato": _payment_state(item)} for item in payments], hide_index=True, width="stretch")
        else:
            empty_state("Nessun pagamento", "Non sono presenti rate per questa commessa.")
    with details[2]:
        if expenses:
            st.dataframe([{"Data": item.get("date"), "Descrizione": item.get("description"), "Categoria": item.get("category"), "Importo": euro(item.get("amount"))} for item in expenses], hide_index=True, width="stretch")
        else:
            empty_state("Nessun costo", "Non sono presenti costi per questa commessa.")
    with details[3]:
        if appointments:
            st.dataframe([{"Data": item.get("date"), "Ora": item.get("start_time"), "Appuntamento": item.get("title"), "Stato": item.get("status")} for item in appointments], hide_index=True, width="stretch")
        else:
            empty_state("Nessun appuntamento", "Non sono presenti appuntamenti per questa commessa.")


def _projects(data):
    clients, projects = data["clients"], data["projects"]
    with st.expander("Nuovo progetto", icon=":material/create_new_folder:", expanded=not projects):
        if not clients:
            st.info("Aggiungi prima almeno un cliente.")
        else:
            with st.form("new_project", clear_on_submit=True):
                options = {item["id"]: item["name"] for item in clients}
                col1, col2 = st.columns(2)
                name = col1.text_input("Nome progetto")
                client_id = col2.selectbox("Cliente", options, format_func=options.get)
                status = col1.selectbox("Stato", PROJECT_STATUSES, index=2)
                due_date = col2.date_input("Scadenza prevista", value=date.today() + timedelta(days=30), format="DD/MM/YYYY")
                value = col1.number_input("Valore concordato", min_value=0.0, step=100.0)
                owner = col2.text_input("Referente operativo", value="Vincenzo Atturo")
                notes = st.text_area("Obiettivo e note")
                if st.form_submit_button("Crea progetto", icon=":material/add:"):
                    if not name.strip():
                        st.error("Inserisci il nome del progetto.")
                    else:
                        add_record("projects", {"name": name.strip(), "client_id": client_id, "status": status, "due_date": due_date.isoformat(), "value": value, "owner": owner.strip(), "notes": notes.strip()})
                        rerun_notice("Progetto creato")
    if not projects:
        empty_state("Nessun progetto", "Le commesse attive compariranno qui.")
        return
    project_options = {item["id"]: item["name"] for item in projects}
    requested_id = st.query_params.get("project_id")
    project_ids = list(project_options)
    selected_index = project_ids.index(requested_id) if requested_id in project_options else 0
    selected_project_id = st.selectbox("Apri la commessa", project_ids, index=selected_index, format_func=project_options.get, key="project_profile")
    _project_detail(data, _by_id(projects)[selected_project_id])
    with st.expander("Aggiorna progetto", icon=":material/edit:"):
        options = {item["id"]: item["name"] for item in projects}
        selected_id = st.selectbox("Progetto", list(options), index=list(options).index(selected_project_id), format_func=options.get, key="edit_project")
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
    cols = st.columns(3)
    cols[0].metric("Da incassare", euro(expected))
    cols[1].metric("Incassato", euro(collected))
    cols[2].metric("Scaduto", euro(overdue))
    with st.expander("Nuova scadenza di pagamento", icon=":material/payments:", expanded=not payments):
        if not clients:
            st.info("Aggiungi prima almeno un cliente.")
        else:
            with st.form("new_payment", clear_on_submit=True):
                client_options = {item["id"]: item["name"] for item in clients}
                project_options = {"": "Non associato", **{item["id"]: item["name"] for item in projects}}
                col1, col2 = st.columns(2)
                client_id = col1.selectbox("Cliente", client_options, format_func=client_options.get)
                project_id = col2.selectbox("Progetto", project_options, format_func=project_options.get)
                description = col1.text_input("Descrizione", placeholder="Acconto, SAL, saldo, canone...")
                amount = col2.number_input("Importo", min_value=0.0, step=50.0)
                due_date = col1.date_input("Scadenza", value=date.today() + timedelta(days=30), format="DD/MM/YYYY")
                status = col2.selectbox("Stato", PAYMENT_STATUSES)
                notes = st.text_area("Note")
                if st.form_submit_button("Registra pagamento", icon=":material/add:"):
                    if not description.strip() or amount <= 0:
                        st.error("Inserisci descrizione e importo.")
                    else:
                        paid_date = date.today().isoformat() if status == "Incassato" else ""
                        add_record("payments", {"client_id": client_id, "project_id": project_id, "description": description.strip(), "amount": amount, "due_date": due_date.isoformat(), "paid_date": paid_date, "status": status, "notes": notes.strip()})
                        rerun_notice("Pagamento registrato")
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
    projects, expenses = data["projects"], data["expenses"]
    _, collected, _, spent = _totals(data)
    cols = st.columns(3)
    cols[0].metric("Entrate incassate", euro(collected))
    cols[1].metric("Uscite registrate", euro(spent))
    cols[2].metric("Margine gestionale", euro(collected - spent))
    with st.expander("Registra un costo", icon=":material/receipt_long:", expanded=not expenses):
        with st.form("new_expense", clear_on_submit=True):
            project_options = {"": "Generale", **{item["id"]: item["name"] for item in projects}}
            col1, col2 = st.columns(2)
            expense_date = col1.date_input("Data", value=date.today(), format="DD/MM/YYYY")
            project_id = col2.selectbox("Progetto", project_options, format_func=project_options.get)
            category = col1.selectbox("Categoria", ["Software e servizi", "Hardware", "Trasferte", "Collaborazioni", "Imposte e commissioni", "Altro"])
            supplier = col2.text_input("Fornitore")
            description = col1.text_input("Descrizione")
            amount = col2.number_input("Importo", min_value=0.0, step=10.0, key="expense_amount")
            if st.form_submit_button("Registra costo", icon=":material/add:"):
                if not description.strip() or amount <= 0:
                    st.error("Inserisci descrizione e importo.")
                else:
                    add_record("expenses", {"date": expense_date.isoformat(), "project_id": project_id, "category": category, "supplier": supplier.strip(), "description": description.strip(), "amount": amount})
                    rerun_notice("Costo registrato")
    if expenses:
        st.dataframe([{"Data": item.get("date"), "Descrizione": item.get("description"), "Categoria": item.get("category"), "Progetto": _name(projects, item.get("project_id"), "Generale"), "Fornitore": item.get("supplier"), "Importo": euro(item.get("amount"))} for item in sorted(expenses, key=lambda row: row.get("date", ""), reverse=True)], hide_index=True, width="stretch")
    else:
        empty_state("Nessun costo", "Registra qui software, trasferte, collaborazioni e altre uscite.")
    st.info("Questa è una prima nota per il controllo di gestione e non sostituisce la contabilità fiscale.")


def _calendar_html(appointments, selected_month, clients):
    events = [
        {
            "date": item.get("date"),
            "label": f"{item.get('start_time', '')} {item.get('title', '')}".strip(),
            "kind": "appointment",
            "href": hub_url(module="clienti_progetti", section="agenda", appointment_id=item.get("id")),
        }
        for item in appointments
    ]
    return month_calendar(selected_month, events)


def _agenda(data):
    clients, projects, appointments = data["clients"], data["projects"], data["appointments"]
    with st.expander("Nuovo appuntamento", icon=":material/event:", expanded=not appointments):
        with st.form("new_appointment", clear_on_submit=True):
            client_options = {"": "Non associato", **{item["id"]: item["name"] for item in clients}}
            project_options = {"": "Non associato", **{item["id"]: item["name"] for item in projects}}
            col1, col2 = st.columns(2)
            title = col1.text_input("Titolo appuntamento")
            appointment_date = col2.date_input("Data", value=date.today(), format="DD/MM/YYYY")
            start_time = col1.time_input("Ora", value=datetime.now().replace(second=0, microsecond=0).time())
            kind = col2.selectbox("Tipo", ["Incontro", "Videochiamata", "Telefonata", "Scadenza", "Consegna", "Altro"])
            client_id = col1.selectbox("Cliente", client_options, format_func=client_options.get)
            project_id = col2.selectbox("Progetto", project_options, format_func=project_options.get)
            location = col1.text_input("Luogo o collegamento")
            status = col2.selectbox("Stato", APPOINTMENT_STATUSES)
            notes = st.text_area("Note")
            if st.form_submit_button("Aggiungi in agenda", icon=":material/add:"):
                if not title.strip():
                    st.error("Inserisci il titolo dell'appuntamento.")
                else:
                    add_record("appointments", {"title": title.strip(), "date": appointment_date.isoformat(), "start_time": start_time.strftime("%H:%M"), "type": kind, "client_id": client_id, "project_id": project_id, "location": location.strip(), "status": status, "notes": notes.strip()})
                    rerun_notice("Appuntamento aggiunto")
    selected_month = st.date_input("Mese da visualizzare", value=date.today(), format="DD/MM/YYYY", key="calendar_month")
    st.markdown(_calendar_html(appointments, selected_month, clients), unsafe_allow_html=True)
    upcoming = [item for item in appointments if parse_date(item.get("date")) and parse_date(item.get("date")) >= date.today() and item.get("status") != "Annullato"]
    st.subheader("Prossimi appuntamenti")
    if upcoming:
        st.dataframe([{"Data": item.get("date"), "Ora": item.get("start_time"), "Appuntamento": item.get("title"), "Cliente": _name(clients, item.get("client_id"), "-"), "Progetto": _name(projects, item.get("project_id"), "-"), "Stato": item.get("status")} for item in sorted(upcoming, key=lambda row: (row.get("date", ""), row.get("start_time", "")))], hide_index=True, width="stretch")
    else:
        empty_state("Nessun appuntamento futuro", "Aggiungi un incontro, una telefonata o una scadenza.")


def render(module):
    module_header(module["name"], module.get("description", ""), "GESTIONALE VA DIGITAL")
    data = load_data()
    labels = ["Cruscotto", "Scheda cliente", "Progetti", "Attività", "Pagamenti", "Contabilità", "Agenda"]
    section_defaults = {
        "client": "Scheda cliente",
        "project": "Progetti",
        "tasks": "Attività",
        "payments": "Pagamenti",
        "accounting": "Contabilità",
        "agenda": "Agenda",
    }
    default_tab = section_defaults.get(st.query_params.get("section"), "Cruscotto")
    tabs = st.tabs(labels, default=default_tab, key="clienti_progetti_tabs")
    with tabs[0]:
        _overview(data)
    with tabs[1]:
        _client_profile(data)
    with tabs[2]:
        _projects(data)
    with tabs[3]:
        _tasks(data)
    with tabs[4]:
        _payments(data)
    with tabs[5]:
        _accounting(data)
    with tabs[6]:
        _agenda(data)
