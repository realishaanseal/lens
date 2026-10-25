"""Varaxis Lens.  Run:  streamlit run app.py"""

import streamlit as st

from lens.settings import load_env

load_env()
st.set_page_config(page_title="Varaxis Lens", page_icon="🔍", layout="wide")

with st.sidebar:
    st.markdown("### Varaxis Lens")
    st.caption("Know if AI recommends you.")

st.navigation([
    st.Page("ui/dashboard.py", title="Dashboard", icon="📊", default=True),
    st.Page("ui/clients.py", title="Clients", icon="🏥"),
    st.Page("ui/settings.py", title="Settings", icon="⚙️"),
]).run()
