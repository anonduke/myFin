from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from app.state import format_money, get_repo, load_card_snapshots, load_debt_snapshots
from core.utils import days_between, next_due_date


st.set_page_config(
    page_title="Dashboard | MyFin",
    page_icon="D",
    layout="wide",
)

repo = get_repo()
today = date.today()

debt_snaps = load_debt_snapshots(repo, today)
card_snaps = load_card_snapshots(repo, today)

payments = repo.list_payments()

total_debt = sum(
    d.debt.principal_outstanding_cad + d.interest_cad + d.penal_cad for d in debt_snaps
) + sum(c.card.statement_balance_cad + c.interest_cad + c.late_fee_cad for c in card_snaps)

total_savings = sum(s.balance_cad for s in repo.list_savings())
net_position = total_savings - total_debt

interest_paid = sum(p.applied_interest + p.applied_penal for p in payments)
principal_paid = sum(p.applied_principal for p in payments)

risk_candidates = []
for snap in debt_snaps:
    risk_candidates.append((snap.risk_score, snap.debt.lender_name))
for snap in card_snaps:
    risk_candidates.append((snap.risk_score, snap.card.card_name))
highest_risk = max(risk_candidates, key=lambda x: x[0]) if risk_candidates else (0.0, "-")

highest_risk_debt = None
if debt_snaps:
    highest_risk_debt = max(debt_snaps, key=lambda s: s.risk_score)

upcoming_items = []
for snap in debt_snaps:
    if snap.debt.installment_due_day:
        due_date = next_due_date(today, snap.debt.installment_due_day)
        days_to_due = days_between(today, due_date)
        upcoming_items.append((days_to_due, f"{snap.debt.lender_name}: {due_date}"))
for snap in card_snaps:
    days_to_due = (snap.card.due_date - today).days
    if days_to_due >= 0:
        upcoming_items.append((days_to_due, f"{snap.card.card_name}: {snap.card.due_date}"))

upcoming_items.sort(key=lambda x: x[0])
upcoming_dues = [item[1] for item in upcoming_items[:5]]

st.title("Dashboard")
st.caption("Executive overview of debts, savings, and risk.")

kpi_row1 = st.columns(4)
with kpi_row1[0]:
    st.metric("Total Debt (CAD)", format_money(total_debt))
with kpi_row1[1]:
    st.metric("Total Interest Paid", format_money(interest_paid))
with kpi_row1[2]:
    st.metric("Total Principal Paid", format_money(principal_paid))
with kpi_row1[3]:
    st.metric("Total Savings (CAD)", format_money(total_savings))

kpi_row2 = st.columns(3)
with kpi_row2[0]:
    st.metric("Net Position (CAD)", format_money(net_position))
with kpi_row2[1]:
    st.metric("Highest Risk", f"{highest_risk[1]} ({highest_risk[0]:.1f})")
with kpi_row2[2]:
    st.metric("Upcoming Dues", str(len(upcoming_dues)))

if upcoming_dues:
    st.caption("Next due items: " + ", ".join(upcoming_dues))

st.divider()

st.subheader("Highest Risk Debt")
if highest_risk_debt:
    balance = highest_risk_debt.debt.principal_outstanding_cad
    st.markdown(
        f"**{highest_risk_debt.debt.lender_name}** | {highest_risk_debt.debt.debt_type} | "
        f"Balance (CAD): {format_money(balance)} | Risk: {highest_risk_debt.risk_score:.1f}"
    )
else:
    st.info("No active debts.")

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

st.subheader("Risk Distribution")
if debt_snaps or card_snaps:
    risk_values = [row["Risk"] for row in risk_rows]
    risk_bins = pd.cut(
        risk_values,
        bins=[0, 20, 40, 60, 80, 100],
        labels=["Low", "Guarded", "Elevated", "High", "Critical"],
        include_lowest=True,
    )
    dist_df = pd.DataFrame({"Bucket": risk_bins}).value_counts().reset_index()
    dist_df.columns = ["Bucket", "Count"]
    fig = px.bar(dist_df, x="Bucket", y="Count")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No risk data available.")

st.subheader("Risk Table")
if debt_snaps or card_snaps:
    table_rows = []
    for snap in debt_snaps:
        table_rows.append(
            {
                "Account": snap.debt.lender_name,
                "Type": "Debt",
                "Balance (CAD)": format_money(snap.debt.principal_outstanding_cad),
                "Overdue Days": snap.overdue_days,
                "Penal Status": "Yes" if snap.penal_cad > 0 else "No",
                "Risk Score": round(snap.risk_score, 1),
            }
        )
    for snap in card_snaps:
        table_rows.append(
            {
                "Account": snap.card.card_name,
                "Type": "Card",
                "Balance (CAD)": format_money(snap.card.statement_balance_cad),
                "Overdue Days": snap.overdue_days,
                "Penal Status": "Yes" if snap.late_fee_cad > 0 else "No",
                "Risk Score": round(snap.risk_score, 1),
            }
        )
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
else:
    st.info("No risk data available.")

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
    fig = px.pie(type_df, names="Type", values="Balance", hole=0.35)
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
    fig = px.pie(currency_df, names="Currency", values="Balance", hole=0.35)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No active debts.")
