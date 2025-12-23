from datetime import date

import pandas as pd
import streamlit as st

from app.state import format_money, get_repo, load_card_snapshots, load_debt_snapshots
from core.fx import convert_to_cad
from core.utils import next_due_date
from models.types import CreditCard, Debt, SavingsAccount


st.set_page_config(
    page_title="Debts & Credit Cards | MyFin",
    page_icon="D",
    layout="wide",
)

repo = get_repo()
today = date.today()

st.title("Debts & Credit Cards")
st.caption("Add, view, and manage loans, credit cards, and savings.")

st.subheader("Add Debt")
with st.form("add_debt"):
    col1, col2, col3 = st.columns(3)
    with col1:
        lender = st.text_input("Lender")
        debt_type = st.selectbox("Debt Type", ["Personal", "Mortgage", "Auto", "Other"])
        currency = st.selectbox("Currency", ["CAD", "INR"])
    with col2:
        sanctioned_amount = st.number_input("Sanctioned Amount (Original)", min_value=0.0)
        current_balance = st.number_input("Current Balance (Original)", min_value=0.0)
        interest_rate = st.number_input("Interest Rate (Annual)", min_value=0.0)
    with col3:
        penal_rate = st.number_input("Penal Rate (Annual)", min_value=0.0)
        loan_start = st.date_input("Loan Start Date")
        installment_amount = st.number_input("Installment Amount", min_value=0.0)
        installment_date = st.date_input("Installment Date")

    submitted = st.form_submit_button("Add Debt")
    if submitted:
        rate_to_cad = 1.0
        if currency != "CAD":
            fx = repo.get_fx_rate(currency)
            if fx is None:
                st.error("Missing FX rate for currency. Add it in Settings.")
                st.stop()
            rate_to_cad = fx.rate_to_cad

        current_balance_cad = convert_to_cad(current_balance, currency, rate_to_cad)
        debt = Debt(
            id=0,
            lender_name=lender,
            debt_type=debt_type,
            original_currency=currency,
            principal_original=sanctioned_amount,
            principal_outstanding_cad=current_balance_cad,
            interest_rate_annual=interest_rate,
            penal_rate_annual=penal_rate,
            loan_start_date=loan_start,
            installment_amount=installment_amount or None,
            installment_due_day=installment_date.day,
            last_payment_date=None,
            status="active",
        )
        repo.add_debt(debt)
        st.success("Debt added.")

st.divider()

st.subheader("Edit Debt")
all_debts = repo.list_debts()
if all_debts:
    debt_options = {f"{d.lender_name} (ID {d.id})": d for d in all_debts}
    selected_label = st.selectbox("Select Debt", list(debt_options.keys()))
    selected_debt = debt_options[selected_label]
    fx_for_edit = repo.get_fx_rate(selected_debt.original_currency) if selected_debt.original_currency != "CAD" else None
    if fx_for_edit and fx_for_edit.rate_to_cad > 0:
        default_balance_original = selected_debt.principal_outstanding_cad / fx_for_edit.rate_to_cad
    else:
        default_balance_original = (
            selected_debt.principal_outstanding_cad if selected_debt.original_currency == "CAD" else 0.0
        )

    with st.form("edit_debt"):
        col1, col2, col3 = st.columns(3)
        with col1:
            lender = st.text_input("Lender", value=selected_debt.lender_name)
            debt_type_options = ["Personal", "Mortgage", "Auto", "Other"]
            if selected_debt.debt_type not in debt_type_options:
                debt_type_options.append(selected_debt.debt_type)
            debt_type = st.selectbox(
                "Debt Type",
                debt_type_options,
                index=debt_type_options.index(selected_debt.debt_type),
            )
            currency_options = ["CAD", "INR"]
            if selected_debt.original_currency not in currency_options:
                currency_options.append(selected_debt.original_currency)
            currency = st.selectbox(
                "Currency",
                currency_options,
                index=currency_options.index(selected_debt.original_currency),
            )
        with col2:
            sanctioned_amount = st.number_input(
                "Sanctioned Amount (Original)",
                min_value=0.0,
                value=float(selected_debt.principal_original),
            )
            current_balance = st.number_input(
                "Current Balance (Original)",
                min_value=0.0,
                value=float(default_balance_original),
                help="For non-CAD, enter original-currency balance; CAD uses the value directly.",
            )
            interest_rate = st.number_input(
                "Interest Rate (Annual)", min_value=0.0, value=float(selected_debt.interest_rate_annual)
            )
        with col3:
            penal_rate = st.number_input(
                "Penal Rate (Annual)", min_value=0.0, value=float(selected_debt.penal_rate_annual)
            )
            loan_start = st.date_input("Loan Start Date", value=selected_debt.loan_start_date)
            installment_amount = st.number_input(
                "Installment Amount", min_value=0.0, value=float(selected_debt.installment_amount or 0.0)
            )
            installment_date = st.date_input(
                "Installment Date",
                value=next_due_date(today, selected_debt.installment_due_day)
                if selected_debt.installment_due_day
                else today,
            )
            status = st.selectbox("Status", ["active", "closed"], index=["active", "closed"].index(selected_debt.status))

        submitted = st.form_submit_button("Update Debt")
        if submitted:
            rate_to_cad = 1.0
            if currency != "CAD":
                fx = repo.get_fx_rate(currency)
                if fx is None:
                    st.error("Missing FX rate for currency. Add it in Settings.")
                    st.stop()
                rate_to_cad = fx.rate_to_cad

            if currency == "CAD" and current_balance == 0.0:
                current_balance = selected_debt.principal_outstanding_cad

            current_balance_cad = convert_to_cad(current_balance, currency, rate_to_cad)
            updated = Debt(
                id=selected_debt.id,
                lender_name=lender,
                debt_type=debt_type,
                original_currency=currency,
                principal_original=sanctioned_amount,
                principal_outstanding_cad=current_balance_cad,
                interest_rate_annual=interest_rate,
                penal_rate_annual=penal_rate,
                loan_start_date=loan_start,
                installment_amount=installment_amount or None,
                installment_due_day=installment_date.day,
                last_payment_date=selected_debt.last_payment_date,
                status=status,
            )
            repo.update_debt(updated)
            st.success("Debt updated.")
else:
    st.info("No debts available to edit.")

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

st.subheader("Edit Credit Card")
all_cards = repo.list_credit_cards()
if all_cards:
    card_options = {f"{c.card_name} (ID {c.id})": c for c in all_cards}
    selected_label = st.selectbox("Select Credit Card", list(card_options.keys()))
    selected_card = card_options[selected_label]

    with st.form("edit_card"):
        col1, col2, col3 = st.columns(3)
        with col1:
            bank = st.text_input("Bank", value=selected_card.bank_name)
            card_name = st.text_input("Card Name", value=selected_card.card_name)
            credit_limit = st.number_input(
                "Credit Limit (CAD)", min_value=0.0, value=float(selected_card.credit_limit_cad)
            )
        with col2:
            statement_balance = st.number_input(
                "Statement Balance (CAD)", min_value=0.0, value=float(selected_card.statement_balance_cad)
            )
            card_interest = st.number_input(
                "Interest Rate (Annual)", min_value=0.0, value=float(selected_card.interest_rate_annual)
            )
            late_fee = st.number_input(
                "Late Fee (CAD)", min_value=0.0, value=float(selected_card.flat_late_fee_cad)
            )
        with col3:
            statement_date = st.date_input("Statement Date", value=selected_card.statement_date)
            due_date = st.date_input("Due Date", value=selected_card.due_date)
            status = st.selectbox("Status", ["active", "closed"], index=["active", "closed"].index(selected_card.status))

        submitted = st.form_submit_button("Update Credit Card")
        if submitted:
            updated = CreditCard(
                id=selected_card.id,
                bank_name=bank,
                card_name=card_name,
                credit_limit_cad=credit_limit,
                statement_balance_cad=statement_balance,
                interest_rate_annual=card_interest,
                statement_date=statement_date,
                due_date=due_date,
                last_payment_date=selected_card.last_payment_date,
                flat_late_fee_cad=late_fee,
                status=status,
            )
            repo.update_credit_card(updated)
            st.success("Credit card updated.")
else:
    st.info("No credit cards available to edit.")

st.divider()

st.subheader("Savings")
with st.form("add_savings"):
    col1, col2, col3 = st.columns(3)
    with col1:
        savings_name = st.text_input("Account Name")
    with col2:
        savings_currency = st.selectbox("Currency", ["CAD", "INR"], key="savings_currency")
    with col3:
        savings_balance = st.number_input("Balance (Original)", min_value=0.0)

    submitted = st.form_submit_button("Add Savings Account")
    if submitted:
        rate_to_cad = 1.0
        if savings_currency != "CAD":
            fx = repo.get_fx_rate(savings_currency)
            if fx is None:
                st.error("Missing FX rate for currency. Add it in Settings.")
                st.stop()
            rate_to_cad = fx.rate_to_cad

        balance_cad = convert_to_cad(savings_balance, savings_currency, rate_to_cad)
        repo.add_savings_account(savings_name, savings_currency, balance_cad)
        st.success("Savings account added.")

savings_accounts = repo.list_savings()
if savings_accounts:
    savings_options = {f"{s.account_name} (ID {s.id})": s for s in savings_accounts}
    selected_label = st.selectbox("Select Savings Account", list(savings_options.keys()))
    selected_savings = savings_options[selected_label]
    fx_savings = repo.get_fx_rate(selected_savings.currency) if selected_savings.currency != "CAD" else None
    if fx_savings and fx_savings.rate_to_cad > 0:
        savings_balance_default = selected_savings.balance_cad / fx_savings.rate_to_cad
    else:
        savings_balance_default = selected_savings.balance_cad if selected_savings.currency == "CAD" else 0.0
    with st.form("edit_savings"):
        col1, col2, col3 = st.columns(3)
        with col1:
            savings_name = st.text_input("Account Name", value=selected_savings.account_name)
        with col2:
            savings_currency = st.selectbox(
                "Currency",
                ["CAD", "INR"],
                index=["CAD", "INR"].index(selected_savings.currency),
                key="edit_savings_currency",
            )
        with col3:
            savings_balance = st.number_input("Balance (Original)", min_value=0.0, value=float(savings_balance_default))

        submitted = st.form_submit_button("Update Savings")
        if submitted:
            rate_to_cad = 1.0
            if savings_currency != "CAD":
                fx = repo.get_fx_rate(savings_currency)
                if fx is None:
                    st.error("Missing FX rate for currency. Add it in Settings.")
                    st.stop()
                rate_to_cad = fx.rate_to_cad

            balance_cad = convert_to_cad(savings_balance, savings_currency, rate_to_cad)
            updated = SavingsAccount(
                id=selected_savings.id,
                account_name=savings_name,
                currency=savings_currency,
                balance_cad=balance_cad,
            )
            repo.update_savings(updated)
            st.success("Savings updated.")

    savings_rows = [
        {
            "Account": s.account_name,
            "Currency": s.currency,
            "Balance (CAD)": format_money(s.balance_cad),
        }
        for s in savings_accounts
    ]
    st.dataframe(pd.DataFrame(savings_rows), use_container_width=True)
else:
    st.info("No savings accounts yet.")

st.divider()

st.subheader("Current Debts")
debt_snapshots = load_debt_snapshots(repo, today)
if debt_snapshots:
    debt_rows = []
    for snap in debt_snapshots:
        due_date = next_due_date(today, snap.debt.installment_due_day) if snap.debt.installment_due_day else None
        debt_rows.append(
            {
                "Lender": snap.debt.lender_name,
                "Type": snap.debt.debt_type,
                "Currency": snap.debt.original_currency,
                "Sanctioned (Original)": format_money(snap.debt.principal_original),
                "Current Balance (CAD)": format_money(snap.debt.principal_outstanding_cad),
                "Installment Date": due_date,
                "Accrued Interest (CAD)": format_money(snap.interest_cad),
                "Accrued Penal (CAD)": format_money(snap.penal_cad),
                "Overdue Days": snap.overdue_days,
                "Risk Score": round(snap.risk_score, 1),
            }
        )
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
