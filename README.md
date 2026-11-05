# Varaxis Lens

**Know if AI recommends you.** AI visibility tracking for businesses that customers find through AI assistants: hospitals, clinics, coaching centres, restaurants and more.

A Varaxis product.

Lens asks ChatGPT, Gemini and Perplexity the questions real customers ask ("Best kidney doctor in <city>?"), in English and in regional languages (Bengali and Banglish built in, plus custom questions in any language). It records whether the business is named and who is recommended instead, tracks the mention rate month to month next to GA4 and Search Console numbers, and turns the results into a dashboard and a one-page monthly PDF.

```
Prompt library → Scheduler → LLM APIs → Parser → Reports
 (per city,       (monthly    (OpenAI,    (mention +    (Streamlit dashboard,
  category,        cron)       Gemini,     competitor     PDF, GA4 + GSC)
  language)                    Perplexity) detection)
```

## Quick start

**Windows:** double-click `start.bat`.  **Mac / Linux:** run `./start.sh`.

The first run installs everything (needs Python 3.10+); after that it opens Lens in your browser.

1. **Settings**: paste your OpenAI, Gemini and/or Perplexity API keys. They are saved to a local `.env` file.
2. **Clients**: add a business: name, city, other spellings, doctors, services, competitors.
3. **Dashboard**: press **Run check**. Lens asks every question on each AI tool and shows the mention rate, who AI recommends instead, what to fix, and every answer. Download the monthly PDF from the sidebar.

No keys yet? Switch on **Offline mock answers** in the sidebar, or press **Load demo data**, to see how it works.

Manual setup instead of the launcher:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Hosting (Streamlit Community Cloud)

1. At share.streamlit.io, create an app from this repo with main file `app.py`.
2. In **Advanced settings → Secrets**, add:

   ```toml
   LENS_PASSWORD = "choose-a-password"
   OPENAI_API_KEY = "..."
   GEMINI_API_KEY = "..."
   PERPLEXITY_API_KEY = "..."
   ```

3. Deploy. With `LENS_PASSWORD` set, the app asks for it before showing anything.

Streamlit Cloud's disk is temporary: results and clients added in the app reset when it restarts. Client files committed under `clients/` are kept.

## Command line

Everything in the app also works from the terminal (handy for scheduling). Keys come from `.env` or the environment:

```bash
export OPENAI_API_KEY=...       # ChatGPT (Responses API with web search)
export GEMINI_API_KEY=...       # Gemini (with Google Search grounding)
export PERPLEXITY_API_KEY=...   # Perplexity (sonar)

python -m lens prompts --client clients/meridian-hospital.yaml          # see the questions
python -m lens run --client clients/meridian-hospital.yaml --limit 3    # cheap test run
python -m lens run --client clients/meridian-hospital.yaml              # full monthly check
python -m lens report --client clients/meridian-hospital.yaml           # writes reports/<id>-<month>.pdf
```

`run` uses every provider with a key unless you pass `--providers openai,gemini`. Models can be changed with `LENS_OPENAI_MODEL`, `LENS_GEMINI_MODEL` and `LENS_PERPLEXITY_MODEL`. Results go to `data/lens.db` (override with `LENS_DB` or `--db`).

### Monthly schedule

Run the check on the 1st of each month with cron:

```cron
0 6 1 * * cd /path/to/lens && .venv/bin/python -m lens run --client clients/meridian-hospital.yaml && .venv/bin/python -m lens report --client clients/meridian-hospital.yaml
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
python -m lens import-traffic --client clients/meridian-hospital.yaml traffic.csv
```

## Client settings

Clients are added on the **Clients** page and saved as YAML in `clients/` (`clients/meridian-hospital.yaml` and `clients/saffron-table.yaml` are fictional samples). The fields:

- **name, aliases, doctors, phones**: every way AI might refer to the business. Any of them counts as a mention.
- **languages**: which question languages to use (`en`, `bn`, `banglish`). English only by default.
- **services**: each one becomes several questions. Add a regional-language name (`bn`) for regional-script questions.
- **competitors**: known rivals, merged with their aliases. Lens also picks up other businesses and doctors named in answers.
- **listings, google_reviews, has_physician_schema**: inputs for fix suggestions.

The question templates for each category are in `lens/data/prompt_library.yaml`.

## How it measures

- **Mention detection**: exact match on the name, aliases, doctor names and phone numbers, then fuzzy matching (88% similarity) for names of 8+ characters, so spelling variants still count.
- **Competitor extraction**: known competitors plus any "<Name> Hospital / Nursing Home / Academy / Restaurant…" and "Dr. <Name>" in the answer.
- **Mention rate**: answers naming the business ÷ answers checked, per AI tool and per month. Failed API calls are left out, and if a question is re-run in the same month only the latest answer counts.
- **Fix suggestions**: rules for services AI never connects to the business, missing Physician schema, phone numbers that differ between listings, regional-language gaps, the competitor AI picks instead, and low review counts.

AI answers vary from run to run and over time. Lens stores every answer with its date, so each month is a snapshot rather than a guarantee.

## Project layout

```
app.py                     Streamlit app (start.sh / start.bat launch it)
ui/                        app pages (dashboard, clients, settings), theme and password screen
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
  settings.py              API keys in .env
  cli.py                   python -m lens ...
tests/
```

Run the tests with `pytest`.

## Team Varaxis

Ishaan Seal (team lead), Ankit Shil, Yogish Keswani.
