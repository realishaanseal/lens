"""Clients page: add a business or edit one, without touching YAML."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lens.config import CATEGORIES, Client, Competitor, Listing, Service, save_client, slugify
from lens.prompts import build_prompts
from ui.common import LANG_NAMES, load_clients

NEW = "__new__"
SCHEMA_CHOICES = {"Not checked": None, "Yes": True, "No": False}


def lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def table_rows(df: pd.DataFrame) -> list[dict]:
    rows = []
    for row in df.to_dict("records"):
        clean = {k: (str(v).strip() if v is not None and not pd.isna(v) else "") for k, v in row.items()}
        if any(clean.values()):
            rows.append(clean)
    return rows


st.title("Clients")
clients = load_clients()
options = [NEW, *clients]
default = st.session_state.get("client_id") if st.session_state.get("client_id") in clients else NEW
choice = st.selectbox("Edit", options, index=options.index(default),
                      format_func=lambda i: "➕ New client" if i == NEW else clients[i].name)
c: Client | None = clients.get(choice)

with st.form(f"client-{choice}"):
    st.subheader("The business")
    a, b = st.columns(2)
    name = a.text_input("Business name *", c.name if c else "", placeholder="SSHRI Hospital")
    category = b.selectbox("Type *", CATEGORIES, index=CATEGORIES.index(c.category) if c else 0,
                           format_func=str.title)
    a, b, d = st.columns(3)
    city = a.text_input("City *", c.city if c else "", placeholder="Krishnanagar")
    city_bn = b.text_input("City in Bengali", (c.city_bn or "") if c else "", placeholder="কৃষ্ণনগর",
                           help="Used for Bengali-script questions. Leave blank to use the English name.")
    area = d.text_input("District / area", (c.area or "") if c else "", placeholder="Nadia")
    website = st.text_input("Website", (c.website or "") if c else "", placeholder="https://")

    st.subheader("How AI might name them")
    st.caption("Any of these in an AI answer counts as a mention. One per line.")
    a, b, d = st.columns(3)
    aliases = a.text_area("Other names / spellings", "\n".join(c.aliases) if c else "",
                          placeholder="SSHRI Multispeciality Hospital")
    doctors = b.text_area("Doctors", "\n".join(c.doctors) if c else "", placeholder="Dr. Full Name",
                          disabled=False)
    phones = d.text_area("Phone numbers", "\n".join(c.phones) if c else "", placeholder="+91 98xxx xxxxx")

    st.subheader("Services")
    st.caption("Each service becomes questions in English, Bengali and Banglish. "
               "Hospitals: specialties. Coaching: courses or exams. Restaurants: dishes or cuisines.")
    services_df = pd.DataFrame(
        [vars(s) for s in c.services] if c and c.services else [],
        columns=["name", "bn", "page"],
    )
    services = st.data_editor(
        services_df, num_rows="dynamic", width="stretch", key=f"services-{choice}",
        column_config={
            "name": st.column_config.TextColumn("Service", required=True),
            "bn": st.column_config.TextColumn("In Bengali"),
            "page": st.column_config.TextColumn("Page on website", help="e.g. /cardiology"),
        },
    )

    st.subheader("Competitors")
    competitors = st.text_area(
        "Known competitors, one per line", "\n".join(
            comp.name + (" | " + ", ".join(comp.aliases) if comp.aliases else "") for comp in c.competitors
        ) if c else "",
        help="Add other spellings after a bar: City Care Nursing Home | City Care. "
             "Businesses AI names that aren't listed here are still picked up.",
    )

    st.subheader("For fix suggestions")
    st.caption("The phone number shown on each listing. Different numbers get flagged.")
    listings_df = pd.DataFrame([vars(item) for item in c.listings] if c and c.listings else [],
                               columns=["source", "phone"])
    listings = st.data_editor(
        listings_df, num_rows="dynamic", width="stretch", key=f"listings-{choice}",
        column_config={
            "source": st.column_config.TextColumn("Listing", help="Website, Google Business Profile, Justdial…"),
            "phone": st.column_config.TextColumn("Phone shown there"),
        },
    )
    a, b, d = st.columns(3)
    reviews = a.number_input("Google reviews", 0, 100000, (c.google_reviews or 0) if c else 0)
    schema_now = next(k for k, v in SCHEMA_CHOICES.items() if v == (c.has_physician_schema if c else None))
    schema = b.selectbox("Has Physician schema?", list(SCHEMA_CHOICES), index=list(SCHEMA_CHOICES).index(schema_now),
                         help="Only used for hospitals and clinics.")
    max_prompts = d.number_input("Questions per check", 1, 200, c.max_prompts if c else 25,
                                 help="Each question is asked on every AI tool, so 25 × 3 = 75 calls.")
    extra = st.text_area("Extra questions, one per line", "\n".join(c.extra_prompts) if c else "",
                         placeholder="Typed the way a customer would ask")

    submitted = st.form_submit_button("Save client", type="primary")

if submitted:
    missing = [label for label, value in [("Business name", name), ("City", city)] if not value.strip()]
    service_rows = [r for r in table_rows(services) if r.get("name")]
    if missing:
        st.error(f"Please fill in: {', '.join(missing)}")
    elif not service_rows:
        st.error("Add at least one service.")
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
            max_prompts=int(max_prompts), extra_prompts=lines(extra),
        )
        path = save_client(updated)
        st.session_state["client_id"] = updated.id
        st.success(f"Saved {updated.name}.")
        c = updated

if c:
    prompts = build_prompts(c)
    with st.expander(f"Questions Lens will ask ({len(prompts)})", expanded=submitted):
        st.dataframe(pd.DataFrame([{"Language": LANG_NAMES.get(p.language, p.language), "Question": p.text}
                                   for p in prompts]), hide_index=True, width="stretch")
    st.page_link("ui/dashboard.py", label="Go to dashboard", icon="📊")
