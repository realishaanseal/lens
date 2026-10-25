# Varaxis Lens

**Know if AI recommends you.** AI visibility tracking for local businesses: hospitals, clinics, coaching centres and restaurants.

Lens asks ChatGPT, Gemini and Perplexity the questions real customers ask ("Best kidney doctor in Krishnanagar?"), in English, Bengali and Banglish. It records whether the business is named and who is recommended instead, tracks the mention rate month to month next to GA4 and Search Console numbers, and turns the results into a dashboard and a one-page monthly PDF.

```
Prompt library → Scheduler → LLM APIs → Parser → Reports
 (per city,       (monthly    (OpenAI,    (mention +    (Streamlit dashboard,
  category,        cron)       Gemini,     competitor     PDF, GA4 + GSC)
  language)                    Perplexity) detection)
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Try it offline with five months of mock data
python -m lens demo --client clients/sshri.yaml
streamlit run app.py
```

## Real checks

Set a key for each AI tool you want to check:

```bash
export OPENAI_API_KEY=...       # ChatGPT (Responses API with web search)
export GEMINI_API_KEY=...       # Gemini (with Google Search grounding)
export PERPLEXITY_API_KEY=...   # Perplexity (sonar)

python -m lens prompts --client clients/sshri.yaml          # see the questions
python -m lens run --client clients/sshri.yaml --limit 3    # cheap test run
python -m lens run --client clients/sshri.yaml              # full monthly check
python -m lens report --client clients/sshri.yaml           # writes reports/<id>-<month>.pdf
```

`run` uses every provider with a key unless you pass `--providers openai,gemini`. Models can be changed with `LENS_OPENAI_MODEL`, `LENS_GEMINI_MODEL` and `LENS_PERPLEXITY_MODEL`. Results go to `data/lens.db` (override with `LENS_DB` or `--db`).

### Monthly schedule

Run the check on the 1st of each month with cron:

```cron
0 6 1 * * cd /path/to/lens && .venv/bin/python -m lens run --client clients/sshri.yaml && .venv/bin/python -m lens report --client clients/sshri.yaml
```

### GA4 and Search Console

Export monthly numbers to a CSV with the columns `period,source,metric,value`:

```csv
period,source,metric,value
2026-10,ga4,ai_assistant_users,9
2026-10,ga4,organic_users,900
2026-10,gsc,clicks,630
2026-10,gsc,impressions,24200
```

```bash
python -m lens import-traffic --client clients/sshri.yaml traffic.csv
```

## Adding a client

Copy `clients/sshri.yaml` and fill in:

- **name, aliases, doctors, phones**: every way AI might refer to the business. Any of them counts as a mention.
- **services**: each one becomes several questions. Add a Bengali name (`bn`) to get Bengali-script questions.
- **competitors**: known rivals, merged with their aliases. Lens also picks up other businesses and doctors named in answers.
- **listings, google_reviews, has_physician_schema**: inputs for fix suggestions.

The question templates for each category are in `lens/data/prompt_library.yaml`.

## How it measures

- **Mention detection**: exact match on the name, aliases, doctor names and phone numbers, then fuzzy matching (88% similarity) for names of 8+ characters, so spelling variants still count.
- **Competitor extraction**: known competitors plus any "<Name> Hospital / Nursing Home / Academy / Restaurant…" and "Dr. <Name>" in the answer.
- **Mention rate**: answers naming the business ÷ answers checked, per AI tool and per month. Failed API calls are left out, and if a question is re-run in the same month only the latest answer counts.
- **Fix suggestions**: rules for services AI never connects to the business, missing Physician schema, phone numbers that differ between listings, Bengali-language gaps, the competitor AI picks instead, and low review counts.

AI answers vary from run to run and over time. Lens stores every answer with its date, so each month is a snapshot rather than a guarantee.

## Project layout

```
app.py                     Streamlit dashboard
clients/                   one YAML per client
lens/
  config.py                client config loader
  prompts.py               question builder (+ data/prompt_library.yaml)
  providers.py             OpenAI, Gemini, Perplexity and offline mock
  detect.py                mention and competitor detection
  runner.py                runs a check, seeds demo data
  store.py                 SQLite storage
  metrics.py               mention rate, trends, competitor counts
  suggest.py               fix suggestions
  report.py                monthly PDF
  traffic.py               GA4 / Search Console CSV import
  cli.py                   python -m lens ...
tests/
```

Run the tests with `pytest`.

## Team Varaxis

Ishaan Seal (team lead), Ankit Shil, Yogish Keswani. Krishnanagar, West Bengal.
