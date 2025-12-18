import streamlit as st


st.set_page_config(
    page_title="Make a Payment | MyFin",
    page_icon="??",
    layout="wide",
)

st.title("Make a Payment")
st.caption("Record a payment and allocate automatically.")

with st.form("make_payment"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox("Target Type", ["Loan", "Credit Card"])
        st.selectbox("Target Account", [])
    with col2:
        st.number_input("Payment Amount", min_value=0.0)
        st.selectbox("Payment Currency", ["CAD", "INR"])
    with col3:
        st.date_input("Payment Date")

    st.form_submit_button("Apply Payment")

st.divider()

st.subheader("Recommended Allocation")
st.info("Allocation preview placeholder")
