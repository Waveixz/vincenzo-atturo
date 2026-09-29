import streamlit as st
from core.storage import load_data
from core.ui import module_header
from modules.clienti_progetti.module import _accounting

def render(module):
    module_header("Contabilità", "Contabilità gestionale, incassi, costi, scadenze e margini collegati a clienti e commesse.", "VA DIGITAL · CONTABILITÀ")
    if st.session_state.pop("flash_message", None):
        st.success("Operazione salvata.")
    _accounting(load_data())
