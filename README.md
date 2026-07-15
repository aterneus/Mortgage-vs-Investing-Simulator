# Mortgage vs Investing Strategy Simulator

This project is a Streamlit web app that lets you compare mortgage payoff strategies against investing strategies.

## Features

- Compare three strategies:
  - Minimum mortgage payment plus extra to principal
  - Minimum mortgage payment plus investing the rest
  - Adaptive strategy that switches to principal paydown when recent market returns exceed user-defined thresholds
- Use either:
  - A user-entered average monthly return
  - Historical S&P 500 monthly returns from the last 30 years via Yahoo Finance
- View a summary table and a net-worth chart over time

## Run locally

Program can be easily run through run_app.bat which automatically install any dependencies.

Alternatively,
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```


- The adaptive strategy uses lookback thresholds to decide when to pay extra principal.
- Capital gains tax is applied to investment returns.
