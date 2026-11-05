"""Varaxis Lens.  Run:  streamlit run app.py"""

import os

import streamlit as st

from lens.settings import load_env
from ui.auth import require_login
from ui.theme import brand, inject, loading_screen

load_env()
try:  # Streamlit Cloud: top-level secrets (API keys, models) act like environment variables
    for _key, _value in st.secrets.items():
        if isinstance(_value, (str, int, float)):
            os.environ.setdefault(_key, str(_value))
except Exception:  # no secrets configured
    pass
st.set_page_config(page_title="Varaxis Lens", page_icon="ui/assets/icon.svg", layout="wide", initial_sidebar_state="expanded")
inject()
require_login()
if not st.session_state.get("_booted"):  # first view after opening or signing in
    st.session_state["_booted"] = True
    loading_screen()
brand()

st.navigation([
    st.Page("ui/dashboard.py", title="Dashboard", icon=":material/insights:", default=True),
    st.Page("ui/clients.py", title="Clients", icon=":material/storefront:"),
    st.Page("ui/settings.py", title="Settings", icon=":material/tune:"),
]).run()
