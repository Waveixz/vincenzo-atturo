import importlib
import streamlit as st


def render_module(module: dict) -> None:
    entrypoint = module.get("entrypoint", "").strip()
    if not entrypoint:
        st.error("Questo modulo non ha un entrypoint configurato.")
        return

    try:
        imported = importlib.import_module(entrypoint)
        renderer = getattr(imported, "render")
        renderer(module)
    except ModuleNotFoundError as exc:
        st.error(f"Modulo non installato: {entrypoint}")
        st.caption(str(exc))
    except AttributeError:
        st.error(f"Il modulo {entrypoint} non espone una funzione render(module).")
    except Exception as exc:
        st.error(f"Errore durante il caricamento di {module.get('name', 'modulo')}.")
        st.exception(exc)
