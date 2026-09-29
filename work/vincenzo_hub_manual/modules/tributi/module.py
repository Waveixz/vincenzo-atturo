import streamlit as st

def render(module):
    st.markdown(f'<div class="hero"><h1>{module["name"]}</h1><p>{module.get("description", "")}</p></div>', unsafe_allow_html=True)
    if module.get("features"):
        cols = st.columns(2)
        for i, feature in enumerate(module["features"]):
            with cols[i % 2]:
                st.markdown(f'<div class="source-card"><div class="source-title">{feature}</div><div class="source-meta">Area del modulo pronta per lo sviluppo.</div></div>', unsafe_allow_html=True)
