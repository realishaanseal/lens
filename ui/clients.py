"""Clients page: see every business, add one, or edit one, without touching YAML."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lens.config import CATEGORIES, LANGUAGES, Client, Competitor, Listing, Service, save_client, slugify
from lens.prompts import build_prompts
from ui.common import LANG_NAMES, load_clients
from ui.theme import client_row, gap, header, heading, rule, section

NEW = "__new__"
SCHEMA_CHOICES = {"Not checked": None, "Yes": True, "No": False}
LANG_LABEL = {"en": "English", "bn": "Bengali (script)", "banglish": "Banglish (Bengali in English letters)"}


def lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def table_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for row in df.to_dict("records"):
        clean = {k: (str(v).strip() if v is not None and not pd.isna(v) else "") for k, v in row.items()}
        if any(clean.values()):
            rows.append(clean)
    return rows


clients = load_clients()
editing = st.session_state.get("editing")
if editing not in clients and editing != NEW:
    editing = None

# ---- Header and list -----------------------------------------------------------
head, action = st.columns([4, 1], vertical_alignment="bottom")
with head:
    header("Clients", "Each business has its own questions, competitors and monthly reports.")
if action.button("New client", type="primary", icon=":material/add:", width="stretch"):
    st.session_state["editing"] = editing = NEW
rule()

if editing is None:
    if not clients:
        st.caption("No clients yet. Add the first one with New client.")
    with st.container(border=True):
        for i, (cid, c) in enumerate(clients.items()):
            if i:
                st.html('<div style="border-top:1px solid #F4F4F5;margin:2px 0"></div>')
            left, mid, right = st.columns([5, 3, 1.4], vertical_alignment="center")
            with left:
                client_row(c.name, " · ".join(x for x in [c.category.title(), c.city, c.area] if x))
            mid.caption(f"{len(build_prompts(c))} questions · {len(c.services)} services · "
                        f"{len(c.competitors)} competitors")
            if right.button("Edit", key=f"edit-{cid}", width="stretch"):
                st.session_state["editing"] = cid
                st.session_state["client_id"] = cid
                st.rerun()
    st.stop()

# ---- Editor --------------------------------------------------------------------
c: Client | None = clients.get(editing)
back, title = st.columns([1, 6], vertical_alignment="center")
if back.button("Back", icon=":material/arrow_back:", width="stretch"):
    st.session_state["editing"] = None
    st.rerun()
title.markdown(f"**{c.name if c else 'New client'}**")
gap()

with st.form(f"client-{editing}", border=False):
    f = section("Business", "The name and location AI tools will be asked about.", first=True)
    a, b = f.columns(2)
    name = a.text_input("Business name", c.name if c else "", placeholder="e.g. Meridian Hospital")
    category = b.selectbox("Type", CATEGORIES, index=CATEGORIES.index(c.category) if c else 0, format_func=str.title)
    a, b = f.columns(2)
    city = a.text_input("City", c.city if c else "", placeholder="e.g. Pune")
    area = b.text_input("State or region", (c.area or "") if c else "", placeholder="Optional")
    website = f.text_input("Website", (c.website or "") if c else "", placeholder="https://")

    f = section("Languages", "Questions are asked in each selected language. Regional languages work best "
                "with the city and service names written in that script.")
    current_langs = c.active_languages if c else ["en"]
    langs = f.multiselect("Question languages", list(LANGUAGES), default=current_langs, format_func=LANG_LABEL.get)
    city_bn = f.text_input("City in regional script", (c.city_bn or "") if c else "", placeholder="Optional")

    f = section("Names AI might use", "Any of these in an answer counts as a mention. One per line.")
    aliases = f.text_area("Other names and spellings", "\n".join(c.aliases) if c else "", height=90)
    a, b = f.columns(2)
    doctors = a.text_area("People (doctors, teachers, chefs)", "\n".join(c.doctors) if c else "", height=90,
                          placeholder="Dr. Full Name")
    phones = b.text_area("Phone numbers", "\n".join(c.phones) if c else "", height=90)

    f = section("Services", "Each service becomes its own questions. Hospitals: specialties. Coaching: courses or "
                "exams. Restaurants: dishes or cuisines.")
    services = f.data_editor(
        pd.DataFrame([vars(s) for s in c.services] if c and c.services else [], columns=["name", "bn", "page"]),
        num_rows="dynamic", width="stretch", key=f"services-{editing}",
        column_config={
            "name": st.column_config.TextColumn("Service", required=True),
            "bn": st.column_config.TextColumn("Regional name", help="Optional, for regional-language questions"),
            "page": st.column_config.TextColumn("Page on website", help="e.g. /cardiology"),
        },
    )

    f = section("Competitors", "Businesses you compete with. Others named by AI are picked up automatically.")
    competitors = f.text_area(
        "One per line", "\n".join(
            comp.name + (" | " + ", ".join(comp.aliases) if comp.aliases else "") for comp in c.competitors
        ) if c else "", height=110,
        help="Add other spellings after a bar: Northgate Hospital | Northgate",
    )

    f = section("Listings and reviews", "Used for fix suggestions, such as phone numbers that differ "
                "between listings.")
    listings = f.data_editor(
        pd.DataFrame([vars(item) for item in c.listings] if c and c.listings else [], columns=["source", "phone"]),
        num_rows="dynamic", width="stretch", key=f"listings-{editing}",
        column_config={
            "source": st.column_config.TextColumn("Listing", help="Website, Google Business Profile, Justdial…"),
            "phone": st.column_config.TextColumn("Phone shown there"),
        },
    )
    a, b = f.columns(2)
    reviews = a.number_input("Google reviews", 0, 100000, (c.google_reviews or 0) if c else 0)
    schema_now = next(k for k, v in SCHEMA_CHOICES.items() if v == (c.has_physician_schema if c else None))
    schema = b.selectbox("Physician schema on website", list(SCHEMA_CHOICES),
                         index=list(SCHEMA_CHOICES).index(schema_now), help="Hospitals and clinics only.")

    f = section("Questions", "How many questions each AI tool is asked per check, plus any of your own.")
    max_prompts = f.number_input("Questions per check", 1, 200, c.max_prompts if c else 25,
                                 help="Each question is asked on every AI tool, so 25 × 3 = 75 requests.")
    extra = f.text_area("Your own questions, one per line", "\n".join(c.extra_prompts) if c else "",
                        placeholder="Typed the way a customer would ask", height=90)

    rule()
    _, save = st.columns([4, 1])
    submitted = save.form_submit_button("Save client", type="primary", width="stretch")

if submitted:
    missing = [label for label, value in [("Business name", name), ("City", city)] if not value.strip()]
    service_rows = [r for r in table_rows(services) if r.get("name")]
    if missing:
        st.error(f"Please fill in: {', '.join(missing)}")
    elif not service_rows:
        st.error("Add at least one service.")
    elif not langs:
        st.error("Choose at least one question language.")
    else:
        comps = []
        for line in lines(competitors):
            comp_name, _, alias_text = line.partition("|")
            comps.append(Competitor(comp_name.strip(), [x.strip() for x in alias_text.split(",") if x.strip()]))
        client_id = c.id if c else slugify(name)
        if not c and client_id in clients:
            client_id = f"{client_id}-{slugify(city)}"
        updated = Client(
            id=client_id, name=name.strip(), category=category, city=city.strip(),
            city_bn=city_bn.strip() or None, area=area.strip() or None, website=website.strip() or None,
            aliases=lines(aliases), doctors=lines(doctors), phones=lines(phones),
            services=[Service(r["name"], r.get("bn") or None, r.get("page") or None) for r in service_rows],
            competitors=comps,
            listings=[Listing(r["source"] or "Listing", r["phone"]) for r in table_rows(listings) if r.get("phone")],
            google_reviews=int(reviews) if reviews else None,
            has_physician_schema=SCHEMA_CHOICES[schema],
            max_prompts=int(max_prompts), extra_prompts=lines(extra), languages=list(langs),
        )
        save_client(updated)
        st.session_state["client_id"] = updated.id
        st.session_state["editing"] = updated.id
        st.toast(f"Saved {updated.name}", icon=":material/check:")
        c = updated

if c:
    prompts = build_prompts(c)
    gap()
    heading("Questions Lens will ask", f"{len(prompts)} total")
    st.dataframe(pd.DataFrame([{"Language": LANG_NAMES.get(p.language, p.language), "Question": p.text}
                               for p in prompts]), hide_index=True, width="stretch")
    st.page_link("ui/dashboard.py", label="Open dashboard", icon=":material/arrow_forward:")
