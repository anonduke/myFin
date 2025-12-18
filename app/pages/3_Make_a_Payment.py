from datetime import date

import pandas as pd
import streamlit as st

from app.state import format_money, get_repo, load_card_snapshots, load_debt_snapshots
from core.fx import convert_to_cad
from core.payments import apply_payment_waterfall, recommend_payment_allocations


st.set_page_config(
    page_title="Make a Payment | MyFin",
    page_icon="P",
    layout="wide",
)

repo = get_repo()
today = date.today()

st.title("Make a Payment")
st.caption("Record a payment and allocate automatically.")

debt_snaps = load_debt_snapshots(repo, today)
card_snaps = load_card_snapshots(repo, today)

options = {}
for snap in debt_snaps:
    label = f"Debt: {snap.debt.lender_name} (ID {snap.debt.id})"
    options[label] = ("loan", snap)
for snap in card_snaps:
    label = f"Card: {snap.card.card_name} (ID {snap.card.id})"
    options[label] = ("credit_card", snap)

with st.form("make_payment"):
    col1, col2, col3 = st.columns(3)
    with col1:
        target_label = st.selectbox("Target Account", list(options.keys())) if options else None
        payment_date = st.date_input("Payment Date", value=today)
    with col2:
        payment_amount = st.number_input("Payment Amount", min_value=0.0)
        payment_currency = st.selectbox("Payment Currency", ["CAD", "INR"])
    with col3:
        strategy = st.selectbox("Recommendation Strategy", ["risk", "avalanche", "snowball"])

    submitted = st.form_submit_button("Apply Payment")
    if submitted:
        if not target_label:
            st.error("No active accounts available.")
            st.stop()

        target_type, snap = options[target_label]
        rate_to_cad = 1.0
        if payment_currency != "CAD":
            fx = repo.get_fx_rate(payment_currency)
            if fx is None:
                st.error("Missing FX rate for currency. Add it in Settings.")
                st.stop()
            rate_to_cad = fx.rate_to_cad

        amount_cad = convert_to_cad(payment_amount, payment_currency, rate_to_cad)

        if target_type == "loan":
            penal_due = snap.penal_cad
            interest_due = snap.interest_cad
            principal_due = snap.debt.principal_outstanding_cad
        else:
            penal_due = snap.late_fee_cad
            interest_due = snap.interest_cad
            principal_due = snap.card.statement_balance_cad

        if amount_cad < (penal_due + interest_due):
            st.error("Payment must cover accrued penal and interest to avoid undercounting.")
            st.stop()

        result = apply_payment_waterfall(
            amount_cad=amount_cad,
            penal_due_cad=penal_due,
            interest_due_cad=interest_due,
            principal_due_cad=principal_due,
        )

        if target_type == "loan":
            new_principal = max(0.0, principal_due - result.applied_principal)
            repo.update_debt_principal(snap.debt.id, new_principal)
            repo.update_debt_last_payment(snap.debt.id, payment_date)
        else:
            new_balance = max(0.0, principal_due - result.applied_principal)
            repo.update_credit_card_balance(snap.card.id, new_balance)
            repo.update_credit_card_last_payment(snap.card.id, payment_date)

        repo.add_payment(
            payment_date=payment_date,
            target_type=target_type,
            target_id=snap.debt.id if target_type == "loan" else snap.card.id,
            payment_amount_original=payment_amount,
            payment_currency=payment_currency,
            payment_amount_cad=amount_cad,
            applied_penal=result.applied_penal,
            applied_interest=result.applied_interest,
            applied_principal=result.applied_principal,
        )

        st.success("Payment applied.")

st.divider()

st.subheader("Recommended Allocation")
items = []
for snap in debt_snaps:
    items.append(
        {
            "target_type": "loan",
            "target_id": snap.debt.id,
            "balance_cad": snap.debt.principal_outstanding_cad,
            "interest_rate_annual": snap.debt.interest_rate_annual,
            "risk_score": snap.risk_score,
        }
    )
for snap in card_snaps:
    items.append(
        {
            "target_type": "credit_card",
            "target_id": snap.card.id,
            "balance_cad": snap.card.statement_balance_cad,
            "interest_rate_annual": snap.card.interest_rate_annual,
            "risk_score": snap.risk_score,
        }
    )

if items:
    available_cad = payment_amount
    if payment_currency != "CAD":
        fx = repo.get_fx_rate(payment_currency)
        if fx is None:
            available_cad = 0.0
        else:
            available_cad = convert_to_cad(payment_amount, payment_currency, fx.rate_to_cad)

    allocations = recommend_payment_allocations(
        available_cad=available_cad,
        items=items,
        strategy=strategy,
    )
    if allocations:
        st.dataframe(pd.DataFrame(allocations), use_container_width=True)
    else:
        st.info("No allocation available.")
else:
    st.info("No active accounts.")
