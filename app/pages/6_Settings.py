import streamlit as st


st.set_page_config(
    page_title="Settings | MyFin",
    page_icon="??",
    layout="wide",
)

st.title("Settings")
st.caption("FX rates, data maintenance, and system preferences.")

st.subheader("FX Rates")
with st.form("fx_rates"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Currency", value="INR")
    with col2:
        st.number_input("Rate to CAD", min_value=0.0)
    with col3:
        st.date_input("Last Updated")

    st.form_submit_button("Save FX Rate")

st.divider()

st.subheader("Maintenance")
col1, col2 = st.columns(2)
with col1:
    st.button("Run Daily Recalculation")
with col2:
    st.button("Create Monthly Snapshot")
