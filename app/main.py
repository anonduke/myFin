from datetime import date

import streamlit as st

from app.state import get_repo, load_card_snapshots, load_debt_snapshots
from db.repository import MonthlySnapshot


st.set_page_config(
    page_title="MyFin Intelligence",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _first_of_month(value: date) -> date:
    return value.replace(day=1)


def run_daily_automation() -> None:
    repo = get_repo()
    today = date.today()
    load_debt_snapshots(repo, today)
    load_card_snapshots(repo, today)

    snapshot_date = _first_of_month(today)
    existing = {s.snapshot_date for s in repo.list_monthly_snapshots()}
    if snapshot_date not in existing:
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
            snapshot_date=snapshot_date,
            total_debt_cad=total_debt,
            total_interest_cad=total_interest,
            total_savings_cad=total_savings,
            net_position_cad=net_position,
        )
        repo.add_monthly_snapshot(snapshot)


def main() -> None:
    run_daily_automation()
    if "redirected_to_dashboard" not in st.session_state:
        st.session_state["redirected_to_dashboard"] = True
        st.switch_page("pages/1_Dashboard.py")
    st.title("MyFin Financial Intelligence")
    st.caption("Local, private, multi-currency debt management")
    st.divider()

    st.markdown(
        """
        Use the sidebar to navigate:
        - Dashboard
        - Debts & Credit Cards
        - Make a Payment
        - What-If Simulator
        - History
        - Settings
        """
    )


if __name__ == "__main__":
    main()
