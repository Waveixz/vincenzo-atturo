from datetime import date, timedelta
import streamlit as st
try:
    import feedparser
except Exception:
    feedparser = None

from core.storage import add_record, delete_record, load_data, update_record
from core.ui import empty_state, module_header, parse_date, rerun_notice

TECH_SOURCES={
 "Development":[("Real Python","https://realpython.com/atom.xml"),("Python News","https://www.python.org/blogs/rss/")],
 "GIS & Geospatial":[("QGIS Blog","https://blog.qgis.org/feed/")],
 "DevOps & Infrastructure":[("Docker","https://www.docker.com/blog/feed/")],
 "Cybersecurity":[("BleepingComputer","https://www.bleepingcomputer.com/feed/")],
}

@st.cache_data(ttl=1800,show_spinner=False)
def get_feed(url):
    if feedparser is None: return []
    try:
        f=feedparser.parse(url)
        return [{"title":e.get("title","Senza titolo"),"link":e.get("link","#")} for e in f.entries[:6]]
    except Exception: return []

def _days_left(value):
    d=parse_date(value)
    return (d-date.today()).days if d else None


@st.dialog("Nuovo dispositivo", width="large")
def _drawer_device():
    with st.form("drawer_device",clear_on_submit=True):
        a,b,c=st.columns(3); name=a.text_input("Nome *"); typ=b.selectbox("Tipo",["PC","Notebook","Server/NAS","Smartphone","Tablet","Monitor","Rete","Stampante","Accessorio","Altro"]); status=c.selectbox("Stato",["Operativo","Scorta","Manutenzione","Dismesso"]); brand=a.text_input("Marca/modello"); serial=b.text_input("Seriale / asset tag"); location=c.text_input("Posizione / utilizzatore"); purchase=a.date_input("Data acquisto",value=date.today()); warranty=b.date_input("Fine garanzia",value=date.today()+timedelta(days=730)); notes=st.text_area("Note")
        if st.form_submit_button("Salva dispositivo",type="primary",width="stretch"):
            if not name.strip(): st.warning("Inserisci il nome.")
            else: add_record("it_assets",{"name":name.strip(),"type":typ,"status":status,"brand_model":brand.strip(),"serial":serial.strip(),"location":location.strip(),"purchase_date":purchase.isoformat(),"warranty_date":warranty.isoformat(),"notes":notes.strip()}); rerun_notice("Dispositivo aggiunto")

@st.dialog("Nuovo software", width="large")
def _drawer_software():
    with st.form("drawer_software",clear_on_submit=True):
        a,b,c=st.columns(3); name=a.text_input("Programma *"); vendor=b.text_input("Produttore"); category=c.selectbox("Categoria",["Sviluppo","GIS","Office","Grafica","Sicurezza","Cloud","Gestionale","Utility","Altro"]); version=a.text_input("Versione"); installed=b.text_input("Installato su"); status=c.selectbox("Stato",["In uso","Test","Da aggiornare","Dismesso"]); notes=st.text_area("Note software")
        if st.form_submit_button("Salva software",type="primary",width="stretch"):
            if not name.strip(): st.warning("Inserisci il nome.")
            else: add_record("software_assets",{"name":name.strip(),"vendor":vendor.strip(),"category":category,"version":version.strip(),"installed_on":installed.strip(),"status":status,"notes":notes.strip()}); rerun_notice("Software aggiunto")

@st.dialog("Nuova licenza / abbonamento", width="large")
def _drawer_license():
    with st.form("drawer_license",clear_on_submit=True):
        a,b,c=st.columns(3); name=a.text_input("Licenza / servizio *"); vendor=b.text_input("Fornitore"); typ=c.selectbox("Tipo",["Licenza software","SaaS/Cloud","Dominio","Hosting","Certificato","Supporto","Altro"]); seats=a.number_input("Postazioni",min_value=1,value=1); cost=b.number_input("Costo rinnovo €",min_value=0.0,step=10.0); cycle=c.selectbox("Rinnovo",["Mensile","Annuale","Biennale","Una tantum","Altro"]); expiry=a.date_input("Scadenza",value=date.today()+timedelta(days=365)); auto=b.checkbox("Rinnovo automatico"); status=c.selectbox("Stato",["Attiva","Da rinnovare","Sospesa","Terminata"]); ref=st.text_input("Account / riferimento (non inserire password)"); notes=st.text_area("Note licenza")
        if st.form_submit_button("Salva licenza",type="primary",width="stretch"):
            if not name.strip(): st.warning("Inserisci il nome.")
            else: add_record("licenses",{"name":name.strip(),"vendor":vendor.strip(),"type":typ,"seats":seats,"cost":cost,"cycle":cycle,"expiry_date":expiry.isoformat(),"auto_renew":auto,"status":status,"reference":ref.strip(),"notes":notes.strip()}); rerun_notice("Licenza aggiunta")



def _asset_manager(collection, items, label):
    if not items: return
    with st.expander(f"Gestisci {label.lower()} · modifica / elimina", icon=":material/edit:"):
        opts={x["id"]:x.get("name","Senza nome") for x in items}; rid=st.selectbox(label,opts,format_func=opts.get,key=f"mgr_{collection}"); x=next(z for z in items if z["id"]==rid)
        with st.form(f"edit_{collection}"):
            name=st.text_input("Nome",x.get("name","")); notes=st.text_area("Note",x.get("notes",""))
            if collection=="it_assets":
                a,b=st.columns(2); status=a.selectbox("Stato",["Operativo","Scorta","Manutenzione","Dismesso"],index=["Operativo","Scorta","Manutenzione","Dismesso"].index(x.get("status","Operativo")) if x.get("status") in ["Operativo","Scorta","Manutenzione","Dismesso"] else 0); location=b.text_input("Posizione / utilizzatore",x.get("location","")); serial=a.text_input("Seriale / asset tag",x.get("serial","")); model=b.text_input("Marca/modello",x.get("brand_model","")); values={"name":name.strip(),"notes":notes.strip(),"status":status,"location":location.strip(),"serial":serial.strip(),"brand_model":model.strip()}
            elif collection=="software_assets":
                a,b=st.columns(2); version=a.text_input("Versione",x.get("version","")); installed=b.text_input("Installato su",x.get("installed_on","")); status=a.selectbox("Stato",["In uso","Test","Da aggiornare","Dismesso"],index=["In uso","Test","Da aggiornare","Dismesso"].index(x.get("status","In uso")) if x.get("status") in ["In uso","Test","Da aggiornare","Dismesso"] else 0); values={"name":name.strip(),"notes":notes.strip(),"version":version.strip(),"installed_on":installed.strip(),"status":status}
            else:
                a,b=st.columns(2); expiry=a.date_input("Scadenza",parse_date(x.get("expiry_date")) or date.today(),format="DD/MM/YYYY"); cost=b.number_input("Costo rinnovo €",min_value=0.0,value=float(x.get("cost") or 0),step=10.0); status=a.selectbox("Stato",["Attiva","Da rinnovare","Sospesa","Terminata"],index=["Attiva","Da rinnovare","Sospesa","Terminata"].index(x.get("status","Attiva")) if x.get("status") in ["Attiva","Da rinnovare","Sospesa","Terminata"] else 0); auto=b.checkbox("Rinnovo automatico",value=bool(x.get("auto_renew"))); values={"name":name.strip(),"notes":notes.strip(),"expiry_date":expiry.isoformat(),"cost":cost,"status":status,"auto_renew":auto}
            if st.form_submit_button("Salva modifiche",type="primary"):
                update_record(collection,rid,values); rerun_notice(f"{label} aggiornato")
        confirm=st.checkbox(f"Confermo eliminazione: {x.get('name','')}",key=f"confirm_del_{collection}_{rid}")
        if st.button("Elimina definitivamente",icon=":material/delete:",key=f"del_{collection}_{rid}",disabled=not confirm):
            delete_record(collection,rid); rerun_notice(f"{label} eliminato")

def render(module):
    module_header(module["name"],module.get("description",""),"TECNOLOGIA · INVENTARIO · LICENZE")
    data=load_data(); devices=data.get("it_assets",[]); software=data.get("software_assets",[]); licenses=data.get("licenses",[])
    expiring=[x for x in licenses if _days_left(x.get("expiry_date")) is not None and _days_left(x.get("expiry_date"))<=30 and x.get("status","Attiva")!="Terminata"]
    c1,c2,c3,c4=st.columns(4); c1.metric("Dispositivi",len(devices)); c2.metric("Software",len(software)); c3.metric("Licenze",len(licenses)); c4.metric("Scadenze ≤30 gg",len(expiring))
    tabs=st.tabs(["Inventario dispositivi","Software & programmi","Licenze & scadenze","Aggiornamento Tech"])
    with tabs[0]:
        if st.button("+ Nuovo dispositivo", type="primary", key="open_device_drawer"):
            _drawer_device()
        if devices:
            st.dataframe([{"Dispositivo":x.get("name"),"Tipo":x.get("type"),"Modello":x.get("brand_model",x.get("environment","")),"Stato":x.get("status"),"Posizione":x.get("location"),"Garanzia":x.get("warranty_date","")} for x in devices],hide_index=True,width="stretch")
        else: empty_state("Nessun dispositivo","Inserisci PC, NAS, rete, smartphone e altra attrezzatura.")
        _asset_manager("it_assets",devices,"Dispositivo")
    with tabs[1]:
        if st.button("+ Nuovo software", type="primary", key="open_software_drawer"):
            _drawer_software()
        if software: st.dataframe([{"Software":x.get("name"),"Produttore":x.get("vendor"),"Categoria":x.get("category"),"Versione":x.get("version"),"Installato su":x.get("installed_on"),"Stato":x.get("status")} for x in software],hide_index=True,width="stretch")
        else: empty_state("Nessun software","Crea l'inventario dei programmi che utilizzi.")
        _asset_manager("software_assets",software,"Software")
    with tabs[2]:
        if expiring:
            st.warning(f"Hai {len(expiring)} licenze in scadenza entro 30 giorni o già scadute.")
        if st.button("+ Nuova licenza / abbonamento", type="primary", key="open_license_drawer"):
            _drawer_license()
        if licenses:
            rows=[]
            for x in sorted(licenses,key=lambda z:z.get("expiry_date", "9999")):
                left=_days_left(x.get("expiry_date")); alert="SCADUTA" if left is not None and left<0 else f"{left} gg" if left is not None else "-"
                rows.append({"Licenza":x.get("name"),"Fornitore":x.get("vendor"),"Tipo":x.get("type"),"Scadenza":x.get("expiry_date"),"Mancano":alert,"Costo":f"€ {float(x.get('cost') or 0):,.2f}","Rinnovo auto":"Sì" if x.get("auto_renew") else "No","Stato":x.get("status")})
            st.dataframe(rows,hide_index=True,width="stretch")
        else: empty_state("Nessuna licenza","Registra licenze, domini, hosting e abbonamenti per controllarne le scadenze.")
        _asset_manager("licenses",licenses,"Licenza")
    with tabs[3]:
        if feedparser is None: st.info("Per gli aggiornamenti Tech installa le dipendenze con: pip install -r requirements.txt")
        query=st.text_input("Cerca negli aggiornamenti",placeholder="Python, QGIS, Docker…")
        shown=0
        for cat,sources in TECH_SOURCES.items():
            st.markdown(f"### {cat}")
            for source,url in sources:
                items=get_feed(url)
                for item in items[:3]:
                    if query and query.casefold() not in item["title"].casefold(): continue
                    st.markdown(f"**{source}** · [{item['title']}]({item['link']})"); shown+=1
        if not shown: st.caption("Nessun aggiornamento disponibile al momento. L'inventario resta comunque utilizzabile offline.")
