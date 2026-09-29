import streamlit as st
from core.storage import load_data
from core.ui import module_header
from modules.clienti_progetti.module import _agenda

def render(module):
    module_header("Agenda", "Calendario operativo collegato a clienti, progetti, attività e scadenze.", "VA DIGITAL · AGENDA")
    if st.session_state.pop("flash_message", None):
        st.success("Operazione salvata.")
    _agenda(load_data())
