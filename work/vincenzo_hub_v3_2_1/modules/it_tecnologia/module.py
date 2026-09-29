import html
import feedparser
import streamlit as st

from core.storage import add_record, delete_record, load_data, update_record
from core.ui import empty_state, module_header, rerun_notice

TECH_SOURCES = {
    "Development": {"desc":"Python, GitHub e software engineering","items":[("Real Python","https://realpython.com/atom.xml"),("Python News","https://www.python.org/blogs/rss/")]},
    "GIS & Geospatial": {"desc":"QGIS, PostGIS e dati territoriali","items":[("QGIS Blog","https://blog.qgis.org/feed/"),("OpenStreetMap","https://blog.openstreetmap.org/feed/")]},
    "DevOps & Infrastructure": {"desc":"Docker, Linux e infrastruttura","items":[("Docker","https://www.docker.com/blog/feed/"),("The New Stack","https://thenewstack.io/feed/")]},
    "Cybersecurity": {"desc":"Alert, vulnerabilità e sicurezza IT","items":[("BleepingComputer","https://www.bleepingcomputer.com/feed/")]},
    "AI & Data": {"desc":"AI, modelli e data science","items":[("Hugging Face","https://huggingface.co/blog/feed.xml")]}
}

@st.cache_data(ttl=1800, show_spinner=False)
def get_feed(url):
    feed=feedparser.parse(url)
    return [{"title":e.get("title","Senza titolo"),"link":e.get("link","#"),"date":e.get("published",e.get("updated",""))} for e in feed.entries[:10]]

def render(module):
    module_header(module["name"], module.get("description", ""), "TECNOLOGIA E SISTEMI")
    tabs=st.tabs(["Aggiornamento Tech", "Inventario", "Nuova risorsa"])
    with tabs[0]:
        query=st.text_input("Cerca aggiornamenti", placeholder="Python, QGIS, Docker, sicurezza, AI…", label_visibility="collapsed")
        for cat,cfg in TECH_SOURCES.items():
            st.markdown(f"### {cat}")
            st.caption(cfg['desc'])
            for source,url in cfg['items']:
                try:
                    items = get_feed(url)[:3]
                except Exception:
                    items = []
                for item in items:
                    if query and query.lower() not in item['title'].lower():
                        continue
                    st.markdown(f"**{source}** · [{item['title']}]({item['link']})")
    with tabs[1]:
        assets = load_data()["it_assets"]
        if assets:
            st.dataframe([
                {"Risorsa": item.get("name", ""), "Tipo": item.get("type", ""), "Ambiente": item.get("environment", ""), "Stato": item.get("status", ""), "Riferimento": item.get("location", "")}
                for item in assets
            ], hide_index=True, width="stretch")
            with st.expander("Aggiorna risorsa", icon=":material/edit:"):
                options = {item["id"]: item["name"] for item in assets}
                selected_id = st.selectbox("Risorsa", options, format_func=options.get)
                selected = next(item for item in assets if item["id"] == selected_id)
                statuses = ["Operativa", "Da verificare", "Manutenzione", "Dismessa"]
                status = st.selectbox("Stato", statuses, index=statuses.index(selected.get("status", "Operativa")))
                notes = st.text_area("Note", selected.get("notes", ""))
                save_col, delete_col = st.columns(2)
                if save_col.button("Salva", icon=":material/save:", width="stretch"):
                    update_record("it_assets", selected_id, {"status": status, "notes": notes.strip()})
                    rerun_notice("Risorsa aggiornata")
                if delete_col.button("Elimina", icon=":material/delete:", width="stretch"):
                    delete_record("it_assets", selected_id)
                    rerun_notice("Risorsa eliminata")
        else:
            empty_state("Inventario vuoto", "Registra server, servizi cloud, software, dispositivi e ambienti.")
    with tabs[2]:
        with st.form("new_it_asset", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Nome risorsa")
            asset_type = col2.selectbox("Tipo", ["Server", "Docker", "Cloud", "Dominio", "Database", "Software", "Dispositivo", "Rete", "Altro"])
            environment = col1.text_input("Ambiente o cliente", value="VA Digital")
            status = col2.selectbox("Stato", ["Operativa", "Da verificare", "Manutenzione", "Dismessa"])
            location = st.text_input("URL, host o riferimento", placeholder="Non inserire password")
            notes = st.text_area("Note tecniche")
            if st.form_submit_button("Aggiungi risorsa", icon=":material/add:"):
                if not name.strip():
                    st.error("Inserisci il nome della risorsa.")
                else:
                    add_record("it_assets", {"name": name.strip(), "type": asset_type, "environment": environment.strip(), "status": status, "location": location.strip(), "notes": notes.strip()})
                    rerun_notice("Risorsa aggiunta")
