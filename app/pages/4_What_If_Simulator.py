from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from app.state import format_money, get_repo
from core.simulator import simulate_payoff


st.set_page_config(
    page_title="What-If Simulator | MyFin",
    page_icon="S",
    layout="wide",
)

repo = get_repo()

st.title("What-If Simulator")
st.caption("Simulate payoff strategies without changing real data.")

with st.form("simulator"):
    col1, col2, col3 = st.columns(3)
    with col1:
        monthly_payment = st.number_input("Monthly Payment (CAD)", min_value=0.0)
    with col2:
        strategy = st.selectbox("Strategy", ["risk", "avalanche", "snowball"])
    with col3:
        start_date = st.date_input("Start Date", value=date.today())

    submitted = st.form_submit_button("Run Simulation")

st.divider()

if submitted:
    debts = repo.list_debts(status="active")
    cards = repo.list_credit_cards(status="active")
    if not debts and not cards:
        st.info("No active accounts.")
    else:
        result = simulate_payoff(
            debts=debts,
            cards=cards,
            start_date=start_date,
            monthly_payment_cad=monthly_payment,
            strategy=strategy,
        )

        st.subheader("Payoff Timeline")
        if result.timeline:
            timeline_df = pd.DataFrame(
                {
                    "Date": [row.as_of for row in result.timeline],
                    "Total Debt (CAD)": [row.total_debt_cad for row in result.timeline],
                    "Total Interest Paid (CAD)": [
                        row.total_interest_paid_cad for row in result.timeline
                    ],
                }
            )
            fig = px.line(timeline_df, x="Date", y="Total Debt (CAD)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No simulation output.")

        st.subheader("Summary")
        debt_free = result.debt_free_date.isoformat() if result.debt_free_date else "Not paid off"
        st.write(
            f"Debt-free date: {debt_free} | Total interest paid: {format_money(result.total_interest_paid_cad)}"
        )

        st.subheader("Strategy Comparison")
        strategies = ["risk", "avalanche", "snowball"]
        comparison_rows = []
        for strat in strategies:
            comp = simulate_payoff(
                debts=debts,
                cards=cards,
                start_date=start_date,
                monthly_payment_cad=monthly_payment,
                strategy=strat,
            )
            comparison_rows.append(
                {
                    "Strategy": strat,
                    "Debt-Free Date": comp.debt_free_date,
                    "Total Interest Paid": comp.total_interest_paid_cad,
                }
            )
        comparison_df = pd.DataFrame(comparison_rows)
        fig = px.bar(comparison_df, x="Strategy", y="Total Interest Paid")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Run a simulation to see results.")
