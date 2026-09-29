from datetime import date

import streamlit as st

from core.password_generator import derive_password
from core.storage import add_record, delete_record, load_data, update_record
from core.ui import empty_state, euro, module_header, rerun_notice


def _generate_password_from_session(master_key, service_key, length_key):
    master = st.session_state.get(master_key, "")
    service = st.session_state.get(service_key, "")
    length = st.session_state.get(length_key, 20)
    try:
        st.session_state["generated_password"] = derive_password(master, service, length)
        st.session_state["generated_password_service"] = service.strip()
        st.session_state.pop("password_error", None)
    except ValueError as error:
        st.session_state["password_error"] = str(error)
    st.session_state["password_form_nonce"] = st.session_state.get("password_form_nonce", 0) + 1


def _clear_password_session():
    for key in ("generated_password", "generated_password_service"):
        st.session_state.pop(key, None)
    st.session_state["password_form_nonce"] = st.session_state.get("password_form_nonce", 0) + 1


def render(module):
    module_header(module["name"], module.get("description", ""), "STRUMENTI RAPIDI")
    links_tab, notes_tab, password_tab, calculators_tab = st.tabs([
        "Collegamenti", "Note rapide", "Password", "Calcolatori"
    ])

    with links_tab:
        data = load_data()
        links = data["quick_links"]
        if links:
            columns = st.columns(3)
            for index, item in enumerate(links):
                with columns[index % 3]:
                    st.link_button(item.get("name", "Apri"), item.get("url", "#"), icon=":material/open_in_new:", width="stretch")
                    st.caption(item.get("category", ""))
        else:
            empty_state("Nessun collegamento", "Aggiungi gli strumenti web che usi più spesso.")
        with st.expander("Gestisci collegamenti", icon=":material/link:"):
            with st.form("new_link", clear_on_submit=True):
                col1, col2 = st.columns(2)
                name = col1.text_input("Nome")
                category = col2.text_input("Categoria", value="Lavoro")
                url = st.text_input("URL", placeholder="https://...")
                if st.form_submit_button("Aggiungi", icon=":material/add:"):
                    if not name.strip() or not url.startswith(("http://", "https://")):
                        st.error("Inserisci nome e URL completo.")
                    else:
                        add_record("quick_links", {"name": name.strip(), "url": url.strip(), "category": category.strip()})
                        rerun_notice("Collegamento aggiunto")
            if links:
                options = {item["id"]: item["name"] for item in links}
                selected_id = st.selectbox("Collegamento", options, format_func=options.get, key="quick_link_manage")
                selected = next(item for item in links if item["id"] == selected_id)
                ename = st.text_input("Nome collegamento", value=selected.get("name", ""), key="quick_link_name")
                ecat = st.text_input("Categoria collegamento", value=selected.get("category", ""), key="quick_link_category")
                eurl = st.text_input("URL collegamento", value=selected.get("url", ""), key="quick_link_url")
                if st.button("Salva modifiche", icon=":material/save:", key="quick_link_save"):
                    if not ename.strip() or not eurl.startswith(("http://", "https://")):
                        st.error("Inserisci nome e URL completo.")
                    else:
                        update_record("quick_links", selected_id, {"name": ename.strip(), "category": ecat.strip(), "url": eurl.strip()})
                        rerun_notice("Collegamento aggiornato")
                confirm = st.checkbox("Confermo eliminazione collegamento", key=f"quick_link_confirm_{selected_id}")
                if st.button("Elimina definitivamente", icon=":material/delete:", disabled=not confirm, key="quick_link_delete"):
                    delete_record("quick_links", selected_id)
                    rerun_notice("Collegamento rimosso")

    with notes_tab:
        data = load_data()
        notes = data["notes"]
        with st.form("new_note", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            title = col1.text_input("Titolo")
            due_date = col2.date_input("Promemoria", value=date.today())
            text = st.text_area("Nota")
            if st.form_submit_button("Salva nota", icon=":material/save:"):
                if not title.strip():
                    st.error("Inserisci un titolo.")
                else:
                    add_record("notes", {"title": title.strip(), "text": text.strip(), "due_date": due_date.isoformat()})
                    rerun_notice("Nota salvata")
        if notes:
            for item in sorted(notes, key=lambda entry: entry.get("due_date", "")):
                with st.expander(f"{item.get('due_date', '')} · {item.get('title', '')}"):
                    etitle = st.text_input("Titolo", value=item.get("title", ""), key=f"note_title_{item['id']}")
                    try:
                        edue = date.fromisoformat(item.get("due_date") or date.today().isoformat())
                    except ValueError:
                        edue = date.today()
                    edue = st.date_input("Promemoria", value=edue, key=f"note_due_{item['id']}")
                    etext = st.text_area("Testo", value=item.get("text", ""), key=f"note_text_{item['id']}")
                    if st.button("Salva modifiche", key=f"save_note_{item['id']}", icon=":material/save:"):
                        update_record("notes", item["id"], {"title": etitle.strip(), "due_date": edue.isoformat(), "text": etext.strip()})
                        rerun_notice("Nota aggiornata")
                    confirm = st.checkbox("Confermo eliminazione nota", key=f"confirm_note_{item['id']}")
                    if st.button("Elimina definitivamente", key=f"delete_note_{item['id']}", icon=":material/delete:", disabled=not confirm):
                        delete_record("notes", item["id"])
                        rerun_notice("Nota eliminata")
        else:
            empty_state("Nessuna nota", "Annota idee, telefonate e promemoria temporanei.")

    with password_tab:
        st.subheader("Generatore password")
        st.caption("La chiave principale e la password generata non vengono salvate nel database.")
        nonce = st.session_state.get("password_form_nonce", 0)
        master_key = f"password_master_{nonce}"
        service_key = f"password_service_{nonce}"
        length_key = f"password_length_{nonce}"
        with st.form(f"password_generator_form_{nonce}"):
            left, right = st.columns(2)
            left.text_input(
                "Chiave principale",
                type="password",
                placeholder="La tua chiave segreta",
                key=master_key,
            )
            right.text_input(
                "Servizio",
                placeholder="es. Aruba, Microsoft 365, QGIS Cloud",
                key=service_key,
            )
            st.slider("Lunghezza", min_value=12, max_value=64, value=20, key=length_key)
            st.form_submit_button(
                "Genera password",
                icon=":material/password:",
                type="primary",
                width="stretch",
                on_click=_generate_password_from_session,
                args=(master_key, service_key, length_key),
            )

        password_error = st.session_state.pop("password_error", None)
        if password_error:
            st.error(password_error)

        generated = st.session_state.get("generated_password", "")
        if generated:
            st.markdown("#### Password generata")
            st.code(generated, language=None, wrap_lines=True)
            st.caption(f"Servizio: {st.session_state.get('generated_password_service', '')} · {len(generated)} caratteri")
            st.button(
                "Cancella dalla sessione",
                icon=":material/delete:",
                key="clear_generated_password",
                on_click=_clear_password_session,
            )

        st.info("Usando la stessa chiave principale, lo stesso servizio e la stessa lunghezza otterrai nuovamente la stessa password.")

    with calculators_tab:
        st.subheader("Stima economica")
        col1, col2, col3 = st.columns(3)
        hours = col1.number_input("Ore previste", min_value=0.0, step=1.0)
        hourly_rate = col2.number_input("Tariffa oraria", min_value=0.0, step=5.0)
        extra_costs = col3.number_input("Costi esterni", min_value=0.0, step=10.0)
        st.metric("Totale stimato", euro(hours * hourly_rate + extra_costs))
        st.subheader("Tempo risparmiato con automazione")
        col1, col2, col3 = st.columns(3)
        minutes = col1.number_input("Minuti per operazione", min_value=0.0, step=5.0)
        repetitions = col2.number_input("Ripetizioni mensili", min_value=0, step=1)
        automated_minutes = col3.number_input("Minuti dopo automazione", min_value=0.0, step=1.0)
        saved_hours = max(0.0, (minutes - automated_minutes) * repetitions / 60)
        st.metric("Ore risparmiate al mese", f"{saved_hours:.1f}")
