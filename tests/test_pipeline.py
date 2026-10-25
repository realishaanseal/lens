import pytest

from lens.metrics import latest_results, summarize, trend
from lens.providers import Answer, MockProvider
from lens.report import build_report
from lens.runner import run_check, seed_demo
from lens.suggest import suggest
from lens.traffic import import_csv


class Fixed:
    """Provider that returns a canned answer per prompt, or raises."""
    model = "fixed"

    def __init__(self, name, answers):
        self.name, self.answers = name, answers

    def ask(self, prompt):
        value = self.answers(prompt)
        if isinstance(value, Exception):
            raise value
        return Answer(value, self.model)


def test_mention_rate_excludes_errors_and_uses_latest(client, store):
    client.max_prompts = 4
    yes = Fixed("openai", lambda p: "Go to SSHRI Hospital or Hospital B.")
    no = Fixed("gemini", lambda p: "Hospital B is popular.")
    broken = Fixed("perplexity", lambda p: RuntimeError("boom"))
    run_check(client, [yes, no, broken], store, period="2026-09")
    s = summarize(store, client.id, "2026-09")
    assert s.answers == 8 and s.errors == 4
    assert s.mention_rate == 0.5
    assert s.by_provider == {"gemini": 0.0, "openai": 1.0}
    assert s.top_competitor == "Hospital B"

    # a re-run in the same month replaces the earlier answers for that tool
    run_check(client, [Fixed("gemini", lambda p: "SSHRI Hospital!")], store, period="2026-09")
    assert summarize(store, client.id, "2026-09").mention_rate == 1.0


def test_demo_trend_report_and_suggestions(client, store):
    months = seed_demo(client, store, months=3, end_period="2026-10")
    assert months == ["2026-08", "2026-09", "2026-10"]
    rows = trend(store, client.id)
    assert [r["period"] for r in rows] == months
    s = summarize(store, client.id, "2026-10")
    assert s.ai_visits == 9 and s.previous_rate is not None

    titles = [x.title for x in suggest(client, latest_results(store, client.id, "2026-10"))]
    assert "Fix phone number mismatch" in titles
    assert "Add Physician schema" in titles
    assert "Collect more reviews" in titles

    pdf = build_report(client, s, suggest(client, latest_results(store, client.id, "2026-10")), store)
    assert pdf.startswith(b"%PDF")


def test_faq_suggestion_for_service_never_mentioned(client, store):
    provider = Fixed("openai", lambda p: "Hospital B." if "Nephrology" in p or "কিডনি" in p else "SSHRI Hospital")
    run_check(client, [provider], store, period="2026-10")
    titles = [x.title for x in suggest(client, latest_results(store, client.id, "2026-10"))]
    assert "Add FAQs to the Nephrology page" in titles
    assert "Add FAQs to the Cardiology page" not in titles


def test_mock_provider_is_deterministic(client):
    a = MockProvider("openai", client, 0.5, seed="x").ask("q")
    b = MockProvider("openai", client, 0.5, seed="x").ask("q")
    assert a.text == b.text


def test_traffic_import(client, store, tmp_path):
    csv = tmp_path / "t.csv"
    csv.write_text("period,source,metric,value\n2026-10,ga4,ai_assistant_users,9\n")
    assert import_csv(store, client.id, csv) == 1
    bad = tmp_path / "bad.csv"
    bad.write_text("period,source,metric,value\nOct,ga4,x,1\n")
    with pytest.raises(ValueError):
        import_csv(store, client.id, bad)


def test_client_save_round_trip(client, tmp_path):
    from lens.config import load_client, save_client
    client.competitors[1].aliases = ["City Care"]
    loaded = load_client(save_client(client, tmp_path))
    assert loaded == client


def test_env_save_and_load(tmp_path, monkeypatch):
    from lens.settings import load_env, read_env, save_env
    env = tmp_path / ".env"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    save_env({"OPENAI_API_KEY": "sk-1", "LENS_OPENAI_MODEL": ""}, env)
    assert read_env(env) == {"OPENAI_API_KEY": "sk-1"}
    monkeypatch.delenv("OPENAI_API_KEY")
    load_env(env)
    import os
    assert os.environ["OPENAI_API_KEY"] == "sk-1"
    save_env({"OPENAI_API_KEY": ""}, env)
    assert read_env(env) == {} and "OPENAI_API_KEY" not in os.environ
