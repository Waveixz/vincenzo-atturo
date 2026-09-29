import json
from pathlib import Path

import streamlit as st

from core.module_registry import add_module, all_modules, delete_module, update_module
from core.storage import DATABASE_FILE, backup_database, load_data
from core.ui import module_header

ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT / "modules"


def _create_scaffold(module: dict) -> None:
    if module.get("open_mode") != "internal":
        return
    folder = MODULES_DIR / module["id"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "__init__.py").touch(exist_ok=True)
    module_file = folder / "module.py"
    if module_file.exists():
        return
    module_file.write_text(
        'import html\nimport streamlit as st\n\n\n'
        'def render(module):\n'
        '    st.markdown(\n'
        '        f\'<div class="hero"><h1>{html.escape(module["name"])}</h1>\'\n'
        '        f\'<p>{html.escape(module.get("description", ""))}</p></div>\',\n'
        '        unsafe_allow_html=True,\n'
        '    )\n'
        '    st.info("Modulo pronto per lo sviluppo.")\n',
        encoding="utf-8",
    )


def render() -> None:
    module_header("Impostazioni", "Gestione dei moduli, dell'archivio locale e delle preferenze della dashboard.", "SISTEMA")
    modules_tab, general_tab = st.tabs(["Module Manager", "Generali"])

    with modules_tab:
        st.markdown('<div class="section-title">Moduli installati</div>', unsafe_allow_html=True)
        st.caption("modules.json controlla navigazione, ordine, stato e modalità di apertura.")

        for module in all_modules():
            with st.expander(f'{module.get("icon", "MOD")} · {module["name"]}'):
                left, right = st.columns([3, 2])
                with left:
                    name = st.text_input("Nome", module["name"], key=f'name_{module["id"]}')
                    description = st.text_area("Descrizione", module.get("description", ""), key=f'desc_{module["id"]}')
                    features = st.text_area("Funzioni (una per riga)", "\n".join(module.get("features", [])), key=f'features_{module["id"]}')
                    entrypoint = st.text_input("Entrypoint Python", module.get("entrypoint", ""), key=f'entry_{module["id"]}')
                with right:
                    icon = st.text_input("Sigla", module.get("icon", "MOD"), key=f'icon_{module["id"]}')
                    mode = st.radio(
                        "Apertura",
                        ["internal", "external"],
                        index=0 if module.get("open_mode", "internal") == "internal" else 1,
                        format_func=lambda value: "Dentro la dashboard" if value == "internal" else "App / URL esterno",
                        key=f'mode_{module["id"]}',
                    )
                    allow_tab = st.toggle("Consenti nuova scheda", module.get("allow_new_tab", True), key=f'tab_{module["id"]}')
                    url = st.text_input("URL esterno", module.get("url", ""), disabled=mode != "external", key=f'url_{module["id"]}')
                    enabled = st.toggle("Attivo", module.get("enabled", True), key=f'enabled_{module["id"]}')
                    order = st.number_input("Ordine", min_value=0, step=10, value=int(module.get("order", 0)), key=f'order_{module["id"]}')

                save_col, delete_col = st.columns(2)
                if save_col.button("Salva modifiche", key=f'save_{module["id"]}', width="stretch"):
                    update_module(
                        module["id"],
                        name=name.strip(), icon=icon.strip() or "MOD", description=description.strip(),
                        features=[line.strip() for line in features.splitlines() if line.strip()],
                        entrypoint=entrypoint.strip(), open_mode=mode, allow_new_tab=allow_tab,
                        url=url.strip(), enabled=enabled, order=int(order),
                    )
                    st.rerun()

                if not module.get("system", False):
                    if delete_col.button("Elimina dal registro", key=f'delete_{module["id"]}', width="stretch"):
                        delete_module(module["id"])
                        st.rerun()

        st.markdown('<div class="section-title">Aggiungi modulo</div>', unsafe_allow_html=True)
        with st.form("new_module", clear_on_submit=True):
            left, right = st.columns([3, 2])
            with left:
                name = st.text_input("Nome modulo", placeholder="Es. Timesheet")
                description = st.text_area("Descrizione")
                features = st.text_area("Funzioni (una per riga)")
                entrypoint = st.text_input("Entrypoint (opzionale)", placeholder="modules.timesheet.module")
            with right:
                icon = st.text_input("Sigla", value="MOD")
                mode = st.radio("Apertura", ["internal", "external"], format_func=lambda value: "Dentro la dashboard" if value == "internal" else "App / URL esterno")
                allow_tab = st.checkbox("Consenti nuova scheda", value=True)
                url = st.text_input("URL esterno", disabled=mode != "external")
                enabled = st.checkbox("Attiva subito", value=True)
                scaffold = st.checkbox("Crea cartella e module.py", value=True, disabled=mode != "internal")

            if st.form_submit_button("Crea modulo", width="stretch"):
                clean_name = name.strip()
                if not clean_name:
                    st.error("Inserisci il nome del modulo.")
                elif any(m["name"].lower() == clean_name.lower() for m in all_modules()):
                    st.error("Esiste già un modulo con questo nome.")
                elif mode == "external" and not url.strip():
                    st.error("Inserisci l'URL del modulo esterno.")
                else:
                    module = add_module(
                        clean_name, icon, description,
                        [line.strip() for line in features.splitlines() if line.strip()],
                        enabled, mode, allow_tab, url, entrypoint,
                    )
                    if scaffold and mode == "internal":
                        _create_scaffold(module)
                    st.rerun()

        with st.expander("Registro JSON"):
            st.code(json.dumps({"version": 2, "modules": all_modules()}, ensure_ascii=False, indent=2), language="json")

    with general_tab:
        data = load_data()
        st.subheader("Archivio locale")
        st.code(str(DATABASE_FILE), language=None)
        counts = st.columns(4)
        counts[0].metric("Clienti", len(data["clients"]))
        counts[1].metric("Progetti", len(data["projects"]))
        counts[2].metric("Documenti", len(data["documents"]))
        counts[3].metric("Risorse GIS", len(data["gis_resources"]))
        if st.button("Crea backup del gestionale", icon=":material/backup:"):
            backup_path = backup_database()
            st.session_state["database_backup"] = backup_path.read_bytes()
            st.session_state["database_backup_name"] = backup_path.name
            st.success("Backup creato nella cartella data.")
        if st.session_state.get("database_backup"):
            st.download_button(
                "Scarica il backup",
                data=st.session_state["database_backup"],
                file_name=st.session_state["database_backup_name"],
                mime="application/vnd.sqlite3",
                icon=":material/download:",
            )
        st.caption("Il backup comprende clienti, commesse, pagamenti, appuntamenti e impostazioni operative. Le password non vengono archiviate nel database.")
