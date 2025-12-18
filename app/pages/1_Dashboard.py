from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from app.state import format_money, get_repo, load_card_snapshots, load_debt_snapshots


st.set_page_config(
    page_title="Dashboard | MyFin",
    page_icon="D",
    layout="wide",
)

repo = get_repo()
today = date.today()

debt_snaps = load_debt_snapshots(repo, today)
card_snaps = load_card_snapshots(repo, today)

total_debt = sum(
    d.debt.principal_outstanding_cad + d.interest_cad + d.penal_cad for d in debt_snaps
) + sum(c.card.statement_balance_cad + c.interest_cad + c.late_fee_cad for c in card_snaps)

total_savings = sum(s.balance_cad for s in repo.list_savings())
net_position = total_savings - total_debt

risk_candidates = []
for snap in debt_snaps:
    risk_candidates.append((snap.risk_score, snap.debt.lender_name))
for snap in card_snaps:
    risk_candidates.append((snap.risk_score, snap.card.card_name))
highest_risk = max(risk_candidates, key=lambda x: x[0]) if risk_candidates else (0.0, "-")

upcoming_dues = []
for snap in debt_snaps:
    if snap.debt.installment_due_day:
        upcoming_dues.append(f"{snap.debt.lender_name}: day {snap.debt.installment_due_day}")
for snap in card_snaps:
    upcoming_dues.append(f"{snap.card.card_name}: {snap.card.due_date}")

st.title("Dashboard")
st.caption("Executive overview of debts, savings, and risk.")

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("Total Debt (CAD)", format_money(total_debt))
with kpi_cols[1]:
    st.metric("Total Savings (CAD)", format_money(total_savings))
with kpi_cols[2]:
    st.metric("Net Position (CAD)", format_money(net_position))
with kpi_cols[3]:
    st.metric("Highest Risk", f"{highest_risk[1]} ({highest_risk[0]:.1f})")

st.divider()

st.subheader("Risk Heatmap")
if debt_snaps or card_snaps:
    risk_rows = [
        {"Account": snap.debt.lender_name, "Risk": snap.risk_score, "Type": "Debt"}
        for snap in debt_snaps
    ] + [
        {"Account": snap.card.card_name, "Risk": snap.risk_score, "Type": "Card"}
        for snap in card_snaps
    ]
    risk_df = pd.DataFrame(risk_rows)
    fig = px.bar(risk_df, x="Account", y="Risk", color="Type", range_y=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No active accounts.")

st.subheader("Debt vs Savings Over Time")
if repo.list_monthly_snapshots():
    snapshots = repo.list_monthly_snapshots()
    snapshot_df = pd.DataFrame(
        {
            "Date": [s.snapshot_date for s in snapshots],
            "Debt": [s.total_debt_cad for s in snapshots],
            "Savings": [s.total_savings_cad for s in snapshots],
        }
    )
    fig = px.line(snapshot_df, x="Date", y=["Debt", "Savings"])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No snapshots yet.")

st.subheader("Debt by Type")
if debt_snaps:
    type_df = pd.DataFrame(
        {
            "Type": [d.debt.debt_type for d in debt_snaps],
            "Balance": [d.debt.principal_outstanding_cad for d in debt_snaps],
        }
    )
    fig = px.pie(type_df, names="Type", values="Balance")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No active debts.")

st.subheader("Debt by Currency")
if debt_snaps:
    currency_df = pd.DataFrame(
        {
            "Currency": [d.debt.original_currency for d in debt_snaps],
            "Balance": [d.debt.principal_outstanding_cad for d in debt_snaps],
        }
    )
    fig = px.pie(currency_df, names="Currency", values="Balance")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No active debts.")

if upcoming_dues:
    st.subheader("Upcoming Dues")
    st.write(", ".join(upcoming_dues))
