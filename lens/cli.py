"""Command line: python -m lens <command> --client clients/<id>.yaml"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_client
from .metrics import latest_results, periods, summarize
from .prompts import build_prompts
from .providers import PROVIDERS, MockProvider, ProviderError, available_providers, get_provider
from .report import build_report
from .runner import run_check, seed_demo
from .settings import load_env
from .store import Store, current_period
from .suggest import suggest
from .traffic import import_csv


def _progress(done: int, total: int, label: str):
    print(f"\r[{done}/{total}] {label[:70]:<70}", end="", file=sys.stderr, flush=True)
    if done == total:
        print(file=sys.stderr)


def cmd_prompts(args, client, store):
    for p in build_prompts(client):
        print(f"{p.id}  {p.language:<8}  {p.text}")


def cmd_run(args, client, store):
    names = args.providers.split(",") if args.providers else available_providers()
    if not names:
        sys.exit("No API keys found. Set OPENAI_API_KEY, GEMINI_API_KEY or PERPLEXITY_API_KEY, "
                 "or pass --providers mock to try it offline.")
    try:
        providers = [MockProvider(n, client) if args.mock else get_provider(n, client) for n in names]
    except (ValueError, ProviderError) as exc:
        sys.exit(str(exc))
    period = args.period or current_period()
    run_check(client, providers, store, period=period, limit=args.limit, progress=_progress)
    _print_summary(client, store, period)


def cmd_demo(args, client, store):
    months = seed_demo(client, store, months=args.months, end_period=args.period)
    print(f"Seeded mock checks for {', '.join(months)}")
    _print_summary(client, store, months[-1])


def cmd_summary(args, client, store):
    period = args.period or (periods(store, client.id) or [current_period()])[-1]
    _print_summary(client, store, period)


def cmd_report(args, client, store):
    period = args.period or (periods(store, client.id) or [None])[-1]
    if not period:
        sys.exit("No results yet. Run `python -m lens run` first.")
    summary = summarize(store, client.id, period)
    pdf = build_report(client, summary, suggest(client, latest_results(store, client.id, period)), store)
    out = Path(args.out or f"reports/{client.id}-{period}.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pdf)
    print(f"Wrote {out}")


def cmd_import(args, client, store):
    print(f"Imported {import_csv(store, client.id, args.csv)} rows")


def _print_summary(client, store, period):
    s = summarize(store, client.id, period)
    pct = lambda v: "-" if v is None else f"{v:.0%}"
    print(f"\n{client.name} - {period}")
    print(f"  Mention rate     {pct(s.mention_rate)}  ({s.mentioned}/{s.answers} answers"
          + (f", {s.errors} failed)" if s.errors else ")"))
    for provider, value in s.by_provider.items():
        print(f"    {provider:<12} {pct(value)}")
    print(f"  Questions tested {s.prompts_tested}")
    print(f"  Top competitor   {s.top_competitor or '-'}")
    if s.ai_visits is not None:
        print(f"  AI visits        {s.ai_visits:.0f}")
    for item in suggest(client, latest_results(store, client.id, period)):
        print(f"  * {item.title}: {item.detail}")


def main(argv: list[str] | None = None):
    load_env()
    parser = argparse.ArgumentParser(prog="lens", description="Varaxis Lens - know if AI recommends you.")
    parser.add_argument("--db", help="SQLite file (default: $LENS_DB or data/lens.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, fn, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--client", required=True, help="client YAML, e.g. clients/sshri.yaml")
        p.set_defaults(fn=fn)
        return p

    add("prompts", cmd_prompts, "list the questions that will be asked")
    p = add("run", cmd_run, "ask every question on each AI tool and store results")
    p.add_argument("--providers", help=f"comma-separated: {','.join(PROVIDERS)} (default: all with keys)")
    p.add_argument("--mock", action="store_true", help="use offline mock answers instead of real APIs")
    p.add_argument("--period", help="month to file results under, YYYY-MM (default: this month)")
    p.add_argument("--limit", type=int, help="only the first N questions (cheap test run)")
    p = add("demo", cmd_demo, "fill the database with several months of mock data")
    p.add_argument("--months", type=int, default=5)
    p.add_argument("--period", help="last month of the demo, YYYY-MM")
    p = add("summary", cmd_summary, "print the month's numbers")
    p.add_argument("--period")
    p = add("report", cmd_report, "write the monthly PDF")
    p.add_argument("--period")
    p.add_argument("--out")
    p = add("import-traffic", cmd_import, "import GA4 / Search Console numbers from CSV")
    p.add_argument("csv")

    args = parser.parse_args(argv)
    if args.command == "run" and args.mock and not args.providers:
        args.providers = ",".join(PROVIDERS)
    client = load_client(args.client)
    args.fn(args, client, Store(args.db))


if __name__ == "__main__":
    main()
