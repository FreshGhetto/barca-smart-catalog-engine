@echo off
setlocal

REM === Vai nella cartella dove si trova questo .bat ===
cd /d "%~dp0"

REM === Se esiste una virtualenv locale, attivala ===
IF EXIST ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) ELSE IF EXIST "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) ELSE (
    echo Nessuna virtualenv locale trovata. Uso Python di sistema.
)

REM === Avvia Streamlit ===
python -m streamlit run app
