import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date

st.set_page_config(page_title="Mortgage vs Investing Simulator", page_icon="📈", layout="wide")
st.title("Mortgage vs Investing Strategy Simulator")
st.write("Compare how different monthly strategies affect your mortgage balance, investment balance, and net worth over time.")
st.markdown("""
<style>
div[data-testid='stVerticalBlock'] > div[style*='overflow: auto;'] {overflow: visible !important;}
section[data-testid='stSidebar'] {padding-top: 0.25rem; padding-bottom: 0.25rem;}
section[data-testid='stSidebar'] [data-testid='stSidebarContent'] {padding-top: 0.25rem; padding-bottom: 0.25rem;}
section[data-testid='stSidebar'] [data-testid='stHeader'] {height: 0.25rem;}

.stDataFrame table, .stDataFrame th, .stDataFrame td {
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=86400)
def load_sp500_monthly_returns():
    try:
        end_date = date.today().strftime("%Y-%m-%d")
        start_date = (date.today().replace(year=date.today().year - 30)).strftime("%Y-%m-%d")
        data = yf.download("SPY", start=start_date, end=end_date, progress=False, auto_adjust=False, interval="1mo")
        if data is None or getattr(data, "empty", True):
            raise ValueError("No data returned")

        if isinstance(data, pd.Series):
            series = data
        elif isinstance(data, pd.DataFrame):
            if "Adj Close" in data.columns:
                series = data["Adj Close"]
            elif "Close" in data.columns:
                series = data["Close"]
            else:
                raise ValueError("Yahoo Finance did not return an available price series")
        else:
            raise ValueError("Unexpected Yahoo Finance data structure")

        returns = series.pct_change().dropna()
        if isinstance(returns, pd.DataFrame):
            returns = returns.iloc[:, 0]

        return [float(value) for value in returns.tolist()]
    except Exception as exc:
        st.warning(f"Historical S&P 500 data could not be loaded automatically: {exc}")
        return None


def monthly_mortgage_payment(loan_amount, annual_rate, term_years):
    n_months = term_years * 12
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return loan_amount / n_months
    return loan_amount * monthly_rate / (1 - (1 + monthly_rate) ** (-n_months))


def format_period(month_number):
    start_date = date.today().replace(day=1)
    month_index = (start_date.year * 12 + start_date.month - 1) + (month_number - 1)
    year = month_index // 12
    month = (month_index % 12) + 1
    return date(year, month, 1).strftime("%b %Y")


def simulate_strategy(strategy_name, monthly_returns, loan_amount, annual_rate, term_years, monthly_budget, lookback_months=None, thresholds=None, threshold_mode="above", capital_gains_tax=0.22):
    minimum_payment = monthly_mortgage_payment(loan_amount, annual_rate, term_years)
    n_months = len(monthly_returns)
    balance = float(loan_amount)
    investment_balance = 0.0
    rows = []

    for month_index in range(n_months):
        monthly_return = float(monthly_returns[month_index])
        monthly_rate = annual_rate / 12
        payment_to_mortgage = 0.0
        mortgage_payment_this_period = 0.0

        if balance <= 1e-9:
            mortgage_payment_amount = 0.0
            invested_amount = monthly_budget
            extra_to_principal = 0.0
        else:
            if strategy_name == "A. Minimum payment + extra to principal":
                mortgage_payment_amount = min(minimum_payment, monthly_budget)
                extra_to_principal = max(0.0, monthly_budget - mortgage_payment_amount)
            elif strategy_name == "B. Minimum payment + invest rest":
                mortgage_payment_amount = min(minimum_payment, monthly_budget)
                extra_to_principal = 0.0
            else:
                mortgage_payment_amount = min(minimum_payment, monthly_budget)
                extra_to_principal = 0.0
                if lookback_months and thresholds is not None and month_index >= lookback_months:
                    history = monthly_returns[max(0, month_index - lookback_months):month_index]
                    if len(history) == lookback_months:
                        if threshold_mode == "above":
                            condition = all(
                                float(history[idx]) > float(thresholds[idx]) for idx in range(len(thresholds))
                            )
                        else:
                            condition = all(
                                float(history[idx]) < float(thresholds[idx]) for idx in range(len(thresholds))
                            )
                        if condition:
                            extra_to_principal = max(0.0, monthly_budget - mortgage_payment_amount)
            planned_mortgage_payment = mortgage_payment_amount + extra_to_principal
            interest_charge = balance * monthly_rate
            payment_to_mortgage = min(planned_mortgage_payment, balance + interest_charge)
            mortgage_payment_this_period = payment_to_mortgage
            balance = max(0.0, balance + interest_charge - payment_to_mortgage)
            if balance <= 1e-9:
                balance = 0.0
            invested_amount = max(0.0, monthly_budget - payment_to_mortgage)

        after_tax_return = monthly_return * (1 - capital_gains_tax)
        investment_balance = (investment_balance + invested_amount) * (1 + after_tax_return)
        net_worth = investment_balance - max(balance, 0.0)
        rows.append(
            {
                "period": format_period(month_index + 1),
                "mortgage_payment": mortgage_payment_this_period,
                "invested_amount": invested_amount,
                "mortgage_balance": max(balance, 0.0),
                "investment_balance": investment_balance,
                "net_worth": net_worth,
            }
        )

    return pd.DataFrame(rows), minimum_payment


st.sidebar.header("Inputs")
loan_amount = st.sidebar.number_input("Loan amount ($)", min_value=1000.0, value=300000.0, step=1000.0)
term_years = st.sidebar.selectbox("Mortgage term", [15, 30], index=1)
annual_rate = st.sidebar.number_input("Mortgage annual interest rate (%)", min_value=0.0, max_value=100.0, value=6.5, step=0.1) / 100
monthly_budget = st.sidebar.number_input("Monthly amount available for mortgage + investing ($)", min_value=0.0, value=2500.0, step=100.0)
horizon_years = st.sidebar.number_input("Simulation horizon (years)", min_value=1, max_value=40, value=30, step=1)

return_mode = st.sidebar.radio(
    "Investment return source",
    ["Historical S&P 500 monthly returns (last 30 years)", "User-entered annual return"],
    index=0,
)

required_months = max(1, horizon_years * 12)

if return_mode == "User-entered annual return":
    annual_return = st.sidebar.number_input("Annual return (%)", min_value=-100.0, max_value=100.0, value=8.0, step=0.1) / 100
    monthly_returns = [((1 + annual_return) ** (1 / 12) - 1)] * required_months
else:
    historical_returns = load_sp500_monthly_returns()
    if historical_returns is None:
        st.info("Using a flat 0.8% monthly return because historical data could not be loaded.")
        monthly_returns = [0.008] * required_months
    else:
        if len(historical_returns) >= required_months:
            monthly_returns = historical_returns[-required_months:]
        else:
            monthly_returns = historical_returns + [historical_returns[-1]] * (required_months - len(historical_returns))

capital_gains_tax = st.sidebar.number_input("Capital gains tax rate (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5) / 100
st.sidebar.subheader("Adaptive Strategy")
st.sidebar.caption("Choose whether extra cash is moved to principal when the previous returns are all above or all below their thresholds.")
lookback_months = st.sidebar.number_input("Lookback window x", min_value=1, max_value=24, value=2, step=1)
threshold_mode_choice = st.sidebar.radio("Trigger when returns are", ["Above threshold", "Below threshold"], index=1)
threshold_mode = "above" if threshold_mode_choice == "Above threshold" else "below"
thresholds_text = st.sidebar.text_input("Thresholds for the previous x months (%)", value="-3,-3")
try:
    thresholds = [float(item.strip()) / 100 for item in thresholds_text.split(",") if item.strip()]
    if len(thresholds) != lookback_months:
        st.sidebar.warning("The number of thresholds should match the lookback window x.")
except ValueError:
    st.sidebar.error("Enter thresholds as comma-separated percentages such as 0.5,0.8,1.2")
    thresholds = [0.0] * lookback_months

st.subheader("Strategy comparison")
results = {}
for strategy_name in [
    "A. Minimum payment + extra to principal",
    "B. Minimum payment + invest rest",
    "C. Adaptive strategy",
]:
    strategy_results, _ = simulate_strategy(
        strategy_name,
        monthly_returns,
        loan_amount,
        annual_rate,
        term_years,
        monthly_budget,
        lookback_months=lookback_months,
        thresholds=thresholds,
        threshold_mode=threshold_mode,
        capital_gains_tax=capital_gains_tax,
    )
    results[strategy_name] = strategy_results

minimum_payment = monthly_mortgage_payment(loan_amount, annual_rate, term_years)
st.metric("Minimum monthly mortgage payment", f"${minimum_payment:,.2f}")

def format_payoff_time(balance_series):
    payoff_index = next((idx for idx, value in enumerate(balance_series) if value <= 1e-6), len(balance_series) - 1)
    months = payoff_index + 1
    years, extra_months = divmod(months, 12)
    return f"{years} years {extra_months} months"

summary_rows = []
for label, df in results.items():
    summary_rows.append(
        {
            "Strategy": label,
            "Mortgage payoff time": format_payoff_time(df["mortgage_balance"]),
            "Final net worth": f"${df['net_worth'].iloc[-1]:,.2f}",
        }
    )

summary_df = pd.DataFrame(summary_rows).reset_index(drop=True)
st.dataframe(summary_df, height=140, hide_index=True)

plot_df = pd.DataFrame({label: df["net_worth"] for label, df in results.items()})
plot_df.index = range(1, len(plot_df) + 1)
st.line_chart(plot_df)

st.subheader("Monthly breakdown")
strategy_tabs = st.tabs(["Strategy A", "Strategy B", "Strategy C"])
for tab, strategy_name in zip(strategy_tabs, [
    "A. Minimum payment + extra to principal",
    "B. Minimum payment + invest rest",
    "C. Adaptive strategy",
]):
    with tab:
        selected_df = results[strategy_name][["period", "mortgage_payment", "invested_amount", "mortgage_balance", "net_worth"]].copy()
        selected_df = selected_df.rename(columns={
            "period": "Period",
            "mortgage_payment": "Amount paid to mortgage",
            "invested_amount": "Amount invested",
            "mortgage_balance": "Remaining mortgage balance",
            "net_worth": "Net worth",
        }).reset_index(drop=True)
        currency_columns = [col for col in selected_df.columns if col != "Period"]
        styled_df = selected_df.style.format({col: "${:,.0f}" for col in currency_columns})
        st.dataframe(styled_df, height=500, hide_index=True)

st.subheader("Assumptions")
st.write("- Mortgage payments are calculated using a fixed-rate amortization schedule.")
st.write("- Monthly returns are compounded monthly.")
st.write("- For the adaptive strategy, extra money is directed to principal only when the previous x monthly returns all exceed the user-defined thresholds.")
st.write("- Historical S&P 500 data is pulled from SPY using Yahoo Finance.")

csv_data = pd.concat(results.values(), axis=1)
if st.button("Download simulation data"):
    st.download_button(
        label="Download CSV",
        data=csv_data.to_csv().encode("utf-8"),
        file_name="mortgage_vs_investing_simulation.csv",
        mime="text/csv",
    )
