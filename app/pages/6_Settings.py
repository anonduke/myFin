from datetime import date

import pandas as pd
import streamlit as st

from app.state import format_money, get_repo, load_card_snapshots, load_debt_snapshots
from db.repository import MonthlySnapshot
from models.types import FxRate


st.set_page_config(
    page_title="Settings | MyFin",
    page_icon="S",
    layout="wide",
)

repo = get_repo()

st.title("Settings")
st.caption("FX rates, data maintenance, and system preferences.")

st.subheader("FX Rates")
with st.form("fx_rates"):
    col1, col2, col3 = st.columns(3)
    with col1:
        currency = st.text_input("Currency", value="INR")
    with col2:
        rate_to_cad = st.number_input("Rate to CAD", min_value=0.0)
    with col3:
        last_updated = st.date_input("Last Updated")

    submitted = st.form_submit_button("Save FX Rate")
    if submitted:
        fx = FxRate(
            currency=currency.upper(),
            rate_to_cad=rate_to_cad,
            last_updated=last_updated,
            source="manual",
        )
        repo.upsert_fx_rate(fx)
        st.success("FX rate saved.")

fx_rates = repo.list_fx_rates()
if fx_rates:
    fx_rows = [
        {
            "Currency": fx.currency,
            "Rate to CAD": fx.rate_to_cad,
            "Last Updated": fx.last_updated,
            "Source": fx.source,
        }
        for fx in fx_rates
    ]
    st.dataframe(pd.DataFrame(fx_rows), use_container_width=True)

st.divider()

st.subheader("Maintenance")
col1, col2 = st.columns(2)
with col1:
    if st.button("Run Daily Recalculation"):
        st.success("Recalculation completed on load. No data written.")

with col2:
    if st.button("Create Monthly Snapshot"):
        today = date.today()
        debt_snaps = load_debt_snapshots(repo, today)
        card_snaps = load_card_snapshots(repo, today)
        total_debt = sum(
            d.debt.principal_outstanding_cad + d.interest_cad + d.penal_cad for d in debt_snaps
        ) + sum(
            c.card.statement_balance_cad + c.interest_cad + c.late_fee_cad for c in card_snaps
        )
        total_interest = sum(d.interest_cad + d.penal_cad for d in debt_snaps) + sum(
            c.interest_cad + c.late_fee_cad for c in card_snaps
        )
        total_savings = sum(s.balance_cad for s in repo.list_savings())
        net_position = total_savings - total_debt

        snapshot = MonthlySnapshot(
            snapshot_date=today,
            total_debt_cad=total_debt,
            total_interest_cad=total_interest,
            total_savings_cad=total_savings,
            net_position_cad=net_position,
        )
        try:
            repo.add_monthly_snapshot(snapshot)
            st.success("Monthly snapshot saved.")
        except Exception:
            st.warning("Snapshot already exists for this date.")
