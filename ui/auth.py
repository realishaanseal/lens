"""Optional password screen. Set LENS_PASSWORD (env var or Streamlit secret) to turn it on."""

from __future__ import annotations

import hmac
import os

import streamlit as st



def _password() -> str | None:
    try:
        if "LENS_PASSWORD" in st.secrets:
            return str(st.secrets["LENS_PASSWORD"])
    except Exception:  # no secrets file
        pass
    return os.environ.get("LENS_PASSWORD") or None


def require_login() -> None:
    """Stop the page until the right password is entered. No-op when no password is set."""
    expected = _password()
    if not expected or st.session_state.get("authenticated"):
        return
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.html('<div style="height:12vh"></div>')
        st.image("ui/assets/logo.svg", width=150)
        st.html('<div style="height:20px"></div>')
        with st.container(border=True), st.form("login", border=False):
            st.markdown("**Sign in**")
            entered = st.text_input("Password", type="password", label_visibility="collapsed",
                                    placeholder="Password")
            if st.form_submit_button("Continue", type="primary", width="stretch"):
                if hmac.compare_digest(entered.encode(), expected.encode()):
                    st.session_state["authenticated"] = True
                    st.rerun()
                st.error("Incorrect password.")
    st.stop()
