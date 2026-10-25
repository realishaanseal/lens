"""Runs every prompt on every AI tool and stores what came back."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import Client
from .detect import detect_mention, extract_competitors
from .prompts import Prompt, build_prompts
from .providers import MockProvider, Provider
from .store import Store, current_period

ProgressFn = Callable[[int, int, str], None]


def run_check(client: Client, providers: list[Provider], store: Store, *, period: str | None = None,
              prompts: list[Prompt] | None = None, limit: int | None = None,
              workers: int = 4, progress: ProgressFn | None = None) -> int:
    """Ask each prompt on each provider, detect mentions, and store dated records.

    API calls run in a small thread pool; all database writes happen on the
    calling thread. A failed call is stored with its error and left out of the
    mention rate rather than counted as "not mentioned".
    """
    period = period or current_period()
    prompts = prompts or build_prompts(client)
    if limit:
        prompts = prompts[:limit]
    run_id = store.start_run(client.id, period, [p.name for p in providers])

    jobs = [(provider, prompt) for provider in providers for prompt in prompts]
    total, done = len(jobs), 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(provider.ask, prompt.text): (provider, prompt) for provider, prompt in jobs}
        for future in as_completed(futures):
            provider, prompt = futures[future]
            base = dict(run_id=run_id, client_id=client.id, period=period, provider=provider.name,
                        model=provider.model, prompt_id=prompt.id, prompt=prompt.text,
                        language=prompt.language, service=prompt.service)
            try:
                answer = future.result()
            except Exception as exc:  # one failed call should not sink the whole run
                store.add_result(**base, error=f"{type(exc).__name__}: {exc}")
            else:
                mention = detect_mention(client, answer.text)
                store.add_result(
                    **{**base, "model": answer.model}, answer=answer.text, citations=answer.citations,
                    mentioned=mention.found, matched_alias=mention.alias, match_score=mention.score,
                    snippet=mention.snippet, competitors=extract_competitors(client, answer.text),
                )
            done += 1
            if progress:
                progress(done, total, f"{provider.name}: {prompt.text}")
    return run_id


def _shift_period(period: str, months: int) -> str:
    year, month = map(int, period.split("-"))
    index = year * 12 + (month - 1) + months
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def seed_demo(client: Client, store: Store, *, months: int = 5, end_period: str | None = None) -> list[str]:
    """Fill the store with several months of mock checks and traffic, for demos.

    Mention rates climb month to month, as they would while fixes are applied.
    """
    end_period = end_period or current_period()
    periods = [_shift_period(end_period, -i) for i in reversed(range(months))]
    for i, period in enumerate(periods):
        rate = 0.15 + 0.3 * i / max(months - 1, 1)
        providers = [MockProvider(name, client, rate, seed=period) for name in ("openai", "gemini", "perplexity")]
        run_check(client, providers, store, period=period, workers=1)
        store.set_traffic(client.id, period, "ga4", "ai_assistant_users", round(9 * i / max(months - 1, 1)))
        store.set_traffic(client.id, period, "ga4", "organic_users", 620 + 70 * i)
        store.set_traffic(client.id, period, "gsc", "clicks", 410 + 55 * i)
        store.set_traffic(client.id, period, "gsc", "impressions", 15800 + 2100 * i)
    return periods
