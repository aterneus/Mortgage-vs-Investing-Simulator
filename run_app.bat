@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv" (
    echo Creating virtual environment...
    py -3 -m venv .venv
)

set PYTHON_EXE=.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    echo Python executable not found. Trying fallback...
    set PYTHON_EXE=.venv\Scripts\python
)

echo Installing dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r requirements.txt

echo Starting Streamlit app...
start "" http://localhost:8501
"%PYTHON_EXE%" -m streamlit run app.py --server.headless true --server.port 8501
