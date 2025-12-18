import pandas as pd
import streamlit as st

from app.state import get_repo, format_money


st.set_page_config(
    page_title="History | MyFin",
    page_icon="H",
    layout="wide",
)

repo = get_repo()

st.title("History")
st.caption("Payments and monthly snapshots.")

st.subheader("Payments")
payments = repo.list_payments()
if payments:
    payment_rows = [
        {
            "Date": p.payment_date,
            "Target Type": p.target_type,
            "Target ID": p.target_id,
            "Amount (CAD)": format_money(p.payment_amount_cad),
            "Penal": format_money(p.applied_penal),
            "Interest": format_money(p.applied_interest),
            "Principal": format_money(p.applied_principal),
        }
        for p in payments
    ]
    st.dataframe(pd.DataFrame(payment_rows), use_container_width=True)
else:
    st.info("No payments recorded.")

st.subheader("Monthly Snapshots")
snapshots = repo.list_monthly_snapshots()
if snapshots:
    snapshot_rows = [
        {
            "Date": s.snapshot_date,
            "Total Debt": format_money(s.total_debt_cad),
            "Total Interest": format_money(s.total_interest_cad),
            "Total Savings": format_money(s.total_savings_cad),
            "Net Position": format_money(s.net_position_cad),
        }
        for s in snapshots
    ]
    st.dataframe(pd.DataFrame(snapshot_rows), use_container_width=True)
else:
    st.info("No snapshots recorded.")
