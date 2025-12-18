import streamlit as st


st.set_page_config(
    page_title="Debts & Credit Cards | MyFin",
    page_icon="??",
    layout="wide",
)

st.title("Debts & Credit Cards")
st.caption("Add, view, and manage loans and credit cards.")

st.subheader("Add Debt")
with st.form("add_debt"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Lender")
        st.selectbox("Debt Type", ["Personal", "Mortgage", "Auto", "Other"])
        st.selectbox("Currency", ["CAD", "INR"])
    with col2:
        st.number_input("Principal (Original)", min_value=0.0)
        st.number_input("Interest Rate (Annual)", min_value=0.0)
        st.number_input("Penal Rate (Annual)", min_value=0.0)
    with col3:
        st.date_input("Loan Start Date")
        st.number_input("Installment Amount", min_value=0.0)
        st.number_input("Installment Due Day", min_value=1, max_value=28)

    st.form_submit_button("Add Debt")

st.divider()

st.subheader("Add Credit Card")
with st.form("add_card"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Bank")
        st.text_input("Card Name")
        st.number_input("Credit Limit (CAD)", min_value=0.0)
    with col2:
        st.number_input("Statement Balance (CAD)", min_value=0.0)
        st.number_input("Interest Rate (Annual)", min_value=0.0)
        st.number_input("Late Fee (CAD)", min_value=0.0)
    with col3:
        st.date_input("Statement Date")
        st.date_input("Due Date")

    st.form_submit_button("Add Credit Card")

st.divider()

st.subheader("Current Debts")
st.info("Debts table placeholder")

st.subheader("Current Credit Cards")
st.info("Credit cards table placeholder")
