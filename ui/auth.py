"""Optional password screen. Set LENS_PASSWORD (env var or Streamlit secret) to turn it on."""

from __future__ import annotations

import base64
import hmac
import os
from pathlib import Path

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
    st.html("<style>[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'], "
            "[data-testid='stExpandSidebarButton'] { display:none !important; }"
            ".lx-signin-logo { display:flex; justify-content:center; animation: lxFocusIn 1s var(--e-out) both; }"
            "[data-testid='stVerticalBlockBorderWrapper'] { animation: lxRise .9s var(--e-out) .12s both; }</style>")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.html('<div style="height:12vh"></div>')
        logo = base64.b64encode(Path("ui/assets/logo-endorsed.svg").read_bytes()).decode()
        st.html(f'<div class="lx-signin-logo"><img src="data:image/svg+xml;base64,{logo}" alt="Lens by Varaxis" width="200"></div>')
        st.html('<div style="height:20px"></div>')
        with st.container(border=True), st.form("login", border=False):
            st.markdown("**Sign in**")
            st.caption("Enter the workspace password to continue.")
            entered = st.text_input("Password", type="password", label_visibility="collapsed",
                                    placeholder="Password")
            if st.form_submit_button("Continue", type="primary", width="stretch"):
                if hmac.compare_digest(entered.encode(), expected.encode()):
                    st.session_state["authenticated"] = True
                    st.session_state.pop("_booted", None)  # show the loading screen next
                    st.rerun()
                st.error("Incorrect password.")
    st.stop()
