from datetime import date

import streamlit as st

from core.storage import add_record, delete_record, load_data
from core.ui import empty_state, euro, module_header, rerun_notice


def render(module):
    module_header(module["name"], module.get("description", ""), "STRUMENTI RAPIDI")
    links_tab, notes_tab, calculators_tab = st.tabs(["Collegamenti", "Note rapide", "Calcolatori"])

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
                selected_id = st.selectbox("Rimuovi collegamento", options, format_func=options.get)
                if st.button("Rimuovi", icon=":material/delete:"):
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
                    st.write(item.get("text") or "Nessun dettaglio")
                    if st.button("Elimina nota", key=f"delete_note_{item['id']}", icon=":material/delete:"):
                        delete_record("notes", item["id"])
                        rerun_notice("Nota eliminata")
        else:
            empty_state("Nessuna nota", "Annota idee, telefonate e promemoria temporanei.")

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
