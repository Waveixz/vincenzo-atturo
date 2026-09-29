from pathlib import Path

import streamlit as st

from core.storage import add_record, delete_record, load_data, update_record
from core.ui import empty_state, module_header, rerun_notice


RESOURCE_TYPES = ["Progetto QGIS", "WebGIS", "Mappa pubblicata", "Dataset", "Servizio WMS WFS", "Database PostGIS", "Altro"]
STATUSES = ["Operativo", "In sviluppo", "Da verificare", "Archiviato"]


def render(module):
    module_header(module["name"], module.get("description", ""), "GIS E TERRITORIO")
    data = load_data()
    resources = data["gis_resources"]
    dashboard_tab, add_tab = st.tabs(["Risorse GIS", "Aggiungi risorsa"])

    with dashboard_tab:
        cols = st.columns(4)
        cols[0].metric("Risorse", len(resources))
        cols[1].metric("Web e mappe", len([item for item in resources if item.get("type") in {"WebGIS", "Mappa pubblicata"}]))
        cols[2].metric("Progetti QGIS", len([item for item in resources if item.get("type") == "Progetto QGIS"]))
        cols[3].metric("Da verificare", len([item for item in resources if item.get("status") == "Da verificare"]))
        if not resources:
            empty_state("Nessuna risorsa GIS", "Registra progetti QGIS, mappe pubblicate, servizi e dataset.")
        else:
            query = st.text_input("Cerca risorsa", placeholder="Nome, cliente, tipo o nota")
            filtered = resources
            if query:
                needle = query.casefold()
                filtered = [item for item in resources if needle in " ".join(str(value) for value in item.values()).casefold()]
            st.dataframe([
                {"Nome": item.get("name", ""), "Tipo": item.get("type", ""), "Cliente": item.get("client", ""), "Stato": item.get("status", ""), "Percorso o URL": item.get("location", "")}
                for item in filtered
            ], hide_index=True, width="stretch")
            web_resources = [item for item in filtered if str(item.get("location", "")).startswith(("http://", "https://"))]
            if web_resources:
                st.subheader("Apri mappe e servizi")
                columns = st.columns(min(3, len(web_resources)))
                for index, item in enumerate(web_resources):
                    with columns[index % len(columns)]:
                        st.link_button(item.get("name", "Apri risorsa"), item["location"], icon=":material/open_in_new:", width="stretch")
            with st.expander("Aggiorna risorsa", icon=":material/edit:"):
                options = {item["id"]: item["name"] for item in resources}
                selected_id = st.selectbox("Risorsa", options, format_func=options.get)
                selected = next(item for item in resources if item["id"] == selected_id)
                col1, col2 = st.columns(2)
                status = col1.selectbox("Stato", STATUSES, index=STATUSES.index(selected.get("status", "Operativo")))
                location = col2.text_input("Percorso o URL", selected.get("location", ""))
                notes = st.text_area("Note", selected.get("notes", ""))
                save_col, delete_col = st.columns(2)
                if save_col.button("Salva", icon=":material/save:", width="stretch"):
                    update_record("gis_resources", selected_id, {"status": status, "location": location.strip(), "notes": notes.strip()})
                    rerun_notice("Risorsa aggiornata")
                if delete_col.button("Elimina", icon=":material/delete:", width="stretch"):
                    delete_record("gis_resources", selected_id)
                    rerun_notice("Risorsa eliminata")

    with add_tab:
        with st.form("new_gis_resource", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Nome risorsa")
            resource_type = col2.selectbox("Tipo", RESOURCE_TYPES)
            client = col1.text_input("Cliente o progetto")
            status = col2.selectbox("Stato", STATUSES)
            location = st.text_input("Percorso locale o URL", placeholder=r"C:\Progetti\mappa.qgz oppure https://...")
            notes = st.text_area("Contenuto, fonti dati e note")
            if st.form_submit_button("Aggiungi risorsa", icon=":material/add:"):
                if not name.strip():
                    st.error("Inserisci il nome della risorsa.")
                else:
                    add_record("gis_resources", {"name": name.strip(), "type": resource_type, "client": client.strip(), "status": status, "location": location.strip(), "notes": notes.strip()})
                    rerun_notice("Risorsa GIS aggiunta")
        if resources:
            local_paths = [item for item in resources if item.get("location") and not str(item.get("location")).startswith(("http://", "https://"))]
            if local_paths:
                st.caption("I percorsi locali sono riferimenti della postazione corrente. Verifica che esistano prima di usarli da un altro computer.")
