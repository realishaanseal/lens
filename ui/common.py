"""Shared helpers for the Streamlit pages."""

from __future__ import annotations

import streamlit as st

from lens.config import Client, list_client_files, load_client
from lens.store import Store

TOOL_NAMES = {"openai": "ChatGPT", "gemini": "Gemini", "perplexity": "Perplexity"}
LANG_NAMES = {"en": "English", "bn": "Bengali", "banglish": "Banglish", "custom": "Custom"}


@st.cache_resource
def get_store() -> Store:
    return Store()


def pct(value: float | None) -> str:
    return "–" if value is None else f"{value:.0%}"


def load_clients() -> dict[str, Client]:
    """Clients by id. A broken YAML file is reported, not fatal."""
    clients = {}
    for path in list_client_files():
        try:
            client = load_client(path)
        except Exception as exc:
            st.sidebar.warning(f"Skipped {path.name}: {exc}")
            continue
        clients[client.id] = client
    return clients


def client_picker() -> Client | None:
    """Sidebar client selector, shared across pages via session state."""
    clients = load_clients()
    if not clients:
        return None
    ids = list(clients)
    current = st.session_state.get("client_id")
    index = ids.index(current) if current in ids else 0
    chosen = st.sidebar.selectbox("Client", ids, index=index, format_func=lambda i: clients[i].name)
    st.session_state["client_id"] = chosen
    return clients[chosen]
