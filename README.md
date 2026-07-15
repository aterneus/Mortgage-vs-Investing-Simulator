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

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Shareable deployment

1. Push this repository to GitHub.
2. Go to https://share.streamlit.io and sign in.
3. Connect your GitHub account and select this repo.
4. Choose `app.py` as the main file and deploy.

The app will then be available at a public Streamlit URL.

## Notes

- Use the sidebar to choose historical or user-entered returns.
- The adaptive strategy uses lookback thresholds to decide when to pay extra principal.
- Capital gains tax is applied to investment returns.
