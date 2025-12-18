from datetime import date

import pandas as pd
import streamlit as st

from app.state import get_repo, load_card_snapshots, load_debt_snapshots, format_money
from core.fx import convert_to_cad
from models.types import CreditCard, Debt


st.set_page_config(
    page_title="Debts & Credit Cards | MyFin",
    page_icon="D",
    layout="wide",
)

repo = get_repo()
today = date.today()

st.title("Debts & Credit Cards")
st.caption("Add, view, and manage loans and credit cards.")

st.subheader("Add Debt")
with st.form("add_debt"):
    col1, col2, col3 = st.columns(3)
    with col1:
        lender = st.text_input("Lender")
        debt_type = st.selectbox("Debt Type", ["Personal", "Mortgage", "Auto", "Other"])
        currency = st.selectbox("Currency", ["CAD", "INR"])
    with col2:
        principal_original = st.number_input("Principal (Original)", min_value=0.0)
        interest_rate = st.number_input("Interest Rate (Annual)", min_value=0.0)
        penal_rate = st.number_input("Penal Rate (Annual)", min_value=0.0)
    with col3:
        loan_start = st.date_input("Loan Start Date")
        installment_amount = st.number_input("Installment Amount", min_value=0.0)
        installment_due_day = st.number_input("Installment Due Day", min_value=1, max_value=28)

    submitted = st.form_submit_button("Add Debt")
    if submitted:
        rate_to_cad = 1.0
        if currency != "CAD":
            fx = repo.get_fx_rate(currency)
            if fx is None:
                st.error("Missing FX rate for currency. Add it in Settings.")
                st.stop()
            rate_to_cad = fx.rate_to_cad

        principal_cad = convert_to_cad(principal_original, currency, rate_to_cad)
        debt = Debt(
            id=0,
            lender_name=lender,
            debt_type=debt_type,
            original_currency=currency,
            principal_original=principal_original,
            principal_outstanding_cad=principal_cad,
            interest_rate_annual=interest_rate,
            penal_rate_annual=penal_rate,
            loan_start_date=loan_start,
            installment_amount=installment_amount or None,
            installment_due_day=int(installment_due_day) if installment_due_day else None,
            last_payment_date=None,
            status="active",
        )
        repo.add_debt(debt)
        st.success("Debt added.")

st.divider()

st.subheader("Add Credit Card")
with st.form("add_card"):
    col1, col2, col3 = st.columns(3)
    with col1:
        bank = st.text_input("Bank")
        card_name = st.text_input("Card Name")
        credit_limit = st.number_input("Credit Limit (CAD)", min_value=0.0)
    with col2:
        statement_balance = st.number_input("Statement Balance (CAD)", min_value=0.0)
        card_interest = st.number_input("Interest Rate (Annual)", min_value=0.0)
        late_fee = st.number_input("Late Fee (CAD)", min_value=0.0)
    with col3:
        statement_date = st.date_input("Statement Date")
        due_date = st.date_input("Due Date")

    submitted = st.form_submit_button("Add Credit Card")
    if submitted:
        card = CreditCard(
            id=0,
            bank_name=bank,
            card_name=card_name,
            credit_limit_cad=credit_limit,
            statement_balance_cad=statement_balance,
            interest_rate_annual=card_interest,
            statement_date=statement_date,
            due_date=due_date,
            last_payment_date=None,
            flat_late_fee_cad=late_fee,
            status="active",
        )
        repo.add_credit_card(card)
        st.success("Credit card added.")

st.divider()

st.subheader("Current Debts")
debt_snapshots = load_debt_snapshots(repo, today)
if debt_snapshots:
    debt_rows = [
        {
            "Lender": snap.debt.lender_name,
            "Type": snap.debt.debt_type,
            "Currency": snap.debt.original_currency,
            "Principal (CAD)": format_money(snap.debt.principal_outstanding_cad),
            "Accrued Interest (CAD)": format_money(snap.interest_cad),
            "Accrued Penal (CAD)": format_money(snap.penal_cad),
            "Overdue Days": snap.overdue_days,
            "Risk Score": round(snap.risk_score, 1),
        }
        for snap in debt_snapshots
    ]
    st.dataframe(pd.DataFrame(debt_rows), use_container_width=True)
else:
    st.info("No active debts.")

st.subheader("Current Credit Cards")
card_snapshots = load_card_snapshots(repo, today)
if card_snapshots:
    card_rows = [
        {
            "Bank": snap.card.bank_name,
            "Card": snap.card.card_name,
            "Balance (CAD)": format_money(snap.card.statement_balance_cad),
            "Accrued Interest (CAD)": format_money(snap.interest_cad),
            "Late Fee (CAD)": format_money(snap.late_fee_cad),
            "Utilization": f"{snap.card.utilization * 100:.1f}%",
            "Overdue Days": snap.overdue_days,
            "Risk Score": round(snap.risk_score, 1),
        }
        for snap in card_snapshots
    ]
    st.dataframe(pd.DataFrame(card_rows), use_container_width=True)
else:
    st.info("No active credit cards.")
