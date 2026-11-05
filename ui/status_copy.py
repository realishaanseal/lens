"""Friendly status lines shown while a check runs, instead of raw "gemini: <question>" labels.

Lines are short sentences built from what is actually happening (which AI tool, which city,
which service, which business), on a lens / focus theme. They rotate as answers come in."""

from __future__ import annotations

import random

from lens.config import Client

TOOLS = {"openai": "ChatGPT", "gemini": "Gemini", "perplexity": "Perplexity"}

# {tool} AI tool, {city} client city, {name} business, {service} service in this question (or "local care" etc.)
LINES = [
    "Asking {tool} what a customer in {city} would ask",
    "Bringing {city} into focus with {tool}",
    "Listening to who {tool} recommends for {service}",
    "Reading {tool}'s answer for any mention of {name}",
    "Noting which names {tool} puts first",
    "Following the sources {tool} leans on in {city}",
    "Checking whether {tool} knows {name} by name",
    "Adjusting the lens on {service} in {city}",
    "Comparing {tool}'s picks with your competitors",
    "Reading between the lines of {tool}'s answer",
    "Seeing {city} the way {tool} sees it",
    "Weighing how often {name} makes the shortlist",
    "Tracing where {tool} sends people looking for {service}",
    "Sharpening the picture of {service} in {city}",
    "Keeping a tally of every business {tool} names",
    "Looking for {name} in {tool}'s recommendations",
]

OPENERS = ["Polishing the lens", "Lining up the questions", "Getting {city} in focus"]
CLOSERS = ["Counting the mentions", "Putting the month's picture together", "Almost in focus"]

GENERIC_SERVICE = {"hospital": "care", "clinic": "a good doctor", "coaching": "coaching", "restaurant": "a good meal"}


class StatusCopy:
    """Turns runner progress into a rotating, human status line."""

    def __init__(self, client: Client, seed: int | None = None):
        self.client = client
        self.order = LINES[:]
        random.Random(seed).shuffle(self.order)

    def opener(self) -> str:
        return random.choice(OPENERS).format(city=self.client.city) + "…"

    def line(self, done: int, total: int, label: str) -> str:
        """`label` is the runner's "<provider>: <question>"."""
        provider, _, question = label.partition(": ")
        if "skipped" in question or done >= total:
            text = CLOSERS[done % len(CLOSERS)]
        else:
            service = next((s.name for s in self.client.services if s.name.lower() in question.lower()),
                           GENERIC_SERVICE.get(self.client.category, "the right place"))
            text = self.order[done % len(self.order)].format(
                tool=TOOLS.get(provider, provider.title() or "the AI"), city=self.client.city,
                name=self.client.name, service=service)
        return f"{text}…  ·  {done} of {total}"
