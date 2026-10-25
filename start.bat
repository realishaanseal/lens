@echo off
rem Varaxis Lens: set up on first run, then open the app in your browser.
cd /d "%~dp0"
if not exist .venv (
  echo First run: setting up, takes a minute...
  python -m venv .venv || goto :error
  .venv\Scripts\pip install -q -r requirements.txt || goto :error
)
.venv\Scripts\streamlit run app.py
goto :eof
:error
echo Setup failed. Install Python 3.10+ from python.org (tick "Add to PATH") and try again.
pause
