import streamlit as st

MODULE = {
    "name": "Modulo esempio",
    "icon": "MOD",
    "description": "Esempio di modulo indipendente.",
    "order": 100,
}

def render():
    st.markdown('<div class="hero"><h1>Modulo esempio</h1><p>Pagina generata dal modulo.</p></div>', unsafe_allow_html=True)
    st.info("Inserisci qui le funzioni del modulo.")
