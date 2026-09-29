from datetime import date

import streamlit as st

from core.storage import add_record, delete_record, load_data, update_record
from core.ui import empty_state, module_header, rerun_notice


CHANNELS = ["LinkedIn", "Instagram", "Facebook", "Sito web", "Google Business", "Altro"]


def render(module):
    module_header(module["name"], module.get("description", ""), "VISIBILITÀ E RISULTATI")
    data = load_data()
    snapshots = data["social_snapshots"]
    overview_tab, record_tab = st.tabs(["Andamento", "Registra dati"])

    with overview_tab:
        if not snapshots:
            empty_state("Nessun dato registrato", "Inserisci periodicamente i KPI per costruire uno storico confrontabile.")
        else:
            latest = sorted(snapshots, key=lambda item: item.get("date", ""), reverse=True)[0]
            cols = st.columns(4)
            cols[0].metric("Canale", latest.get("channel", ""))
            cols[1].metric("Follower o utenti", int(latest.get("audience") or 0))
            cols[2].metric("Interazioni", int(latest.get("engagement") or 0))
            cols[3].metric("Contatti", int(latest.get("leads") or 0))
            channel = st.selectbox("Canale", ["Tutti", *CHANNELS])
            filtered = snapshots if channel == "Tutti" else [item for item in snapshots if item.get("channel") == channel]
            st.dataframe([
                {"Data": item.get("date", ""), "Canale": item.get("channel", ""), "Follower o utenti": item.get("audience", 0), "Visualizzazioni": item.get("views", 0), "Interazioni": item.get("engagement", 0), "Contatti": item.get("leads", 0), "Note": item.get("notes", "")}
                for item in sorted(filtered, key=lambda entry: entry.get("date", ""), reverse=True)
            ], hide_index=True, width="stretch")
            with st.expander("Gestisci rilevazione · modifica / elimina", icon=":material/edit:"):
                options = {item["id"]: f"{item.get('date', '')} · {item.get('channel', '')}" for item in snapshots}
                selected_id = st.selectbox("Rilevazione", options, format_func=options.get, key="social_manage_id")
                selected = next(item for item in snapshots if item["id"] == selected_id)
                c1, c2 = st.columns(2)
                edit_date = c1.date_input("Data", value=date.fromisoformat(selected.get("date") or date.today().isoformat()), key="social_edit_date")
                edit_channel = c2.selectbox("Canale", CHANNELS, index=CHANNELS.index(selected.get("channel")) if selected.get("channel") in CHANNELS else 0, key="social_edit_channel")
                audience_e = c1.number_input("Follower o utenti", min_value=0, step=1, value=int(selected.get("audience") or 0), key="social_edit_audience")
                views_e = c2.number_input("Visualizzazioni o impression", min_value=0, step=1, value=int(selected.get("views") or 0), key="social_edit_views")
                engagement_e = c1.number_input("Interazioni", min_value=0, step=1, value=int(selected.get("engagement") or 0), key="social_edit_engagement")
                leads_e = c2.number_input("Contatti ricevuti", min_value=0, step=1, value=int(selected.get("leads") or 0), key="social_edit_leads")
                notes_e = st.text_area("Note", value=selected.get("notes", ""), key="social_edit_notes")
                if st.button("Salva modifiche", icon=":material/save:", key="social_save_edit"):
                    update_record("social_snapshots", selected_id, {"date": edit_date.isoformat(), "channel": edit_channel, "audience": audience_e, "views": views_e, "engagement": engagement_e, "leads": leads_e, "notes": notes_e.strip()})
                    rerun_notice("Rilevazione aggiornata")
                confirm = st.checkbox("Confermo l’eliminazione della rilevazione", key=f"social_confirm_{selected_id}")
                if st.button("Elimina definitivamente", icon=":material/delete:", disabled=not confirm, key="social_delete"):
                    delete_record("social_snapshots", selected_id)
                    rerun_notice("Rilevazione eliminata")

    with record_tab:
        with st.form("new_social_snapshot", clear_on_submit=True):
            col1, col2 = st.columns(2)
            snapshot_date = col1.date_input("Data", value=date.today())
            channel = col2.selectbox("Canale", CHANNELS)
            audience = col1.number_input("Follower o utenti", min_value=0, step=1)
            views = col2.number_input("Visualizzazioni o impression", min_value=0, step=1)
            engagement = col1.number_input("Interazioni", min_value=0, step=1)
            leads = col2.number_input("Contatti ricevuti", min_value=0, step=1)
            notes = st.text_area("Contenuti pubblicati o note")
            if st.form_submit_button("Registra KPI", icon=":material/save:"):
                add_record("social_snapshots", {"date": snapshot_date.isoformat(), "channel": channel, "audience": audience, "views": views, "engagement": engagement, "leads": leads, "notes": notes.strip()})
                rerun_notice("KPI registrati")
