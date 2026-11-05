"""Varaxis Lens.  Run:  streamlit run app.py"""

import streamlit as st

from lens.settings import load_env
from ui.theme import brand, inject

load_env()
st.set_page_config(page_title="Varaxis Lens", page_icon="ui/assets/icon.svg", layout="wide", initial_sidebar_state="expanded")
inject()
brand()

st.navigation([
    st.Page("ui/dashboard.py", title="Dashboard", icon=":material/insights:", default=True),
    st.Page("ui/clients.py", title="Clients", icon=":material/storefront:"),
    st.Page("ui/settings.py", title="Settings", icon=":material/tune:"),
]).run()
