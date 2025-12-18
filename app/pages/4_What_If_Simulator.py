import streamlit as st


st.set_page_config(
    page_title="What-If Simulator | MyFin",
    page_icon="??",
    layout="wide",
)

st.title("What-If Simulator")
st.caption("Simulate payoff strategies without changing real data.")

with st.form("simulator"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("Monthly Payment (CAD)", min_value=0.0)
    with col2:
        st.selectbox("Strategy", ["Risk-based", "Avalanche", "Snowball"])
    with col3:
        st.date_input("Start Date")

    st.form_submit_button("Run Simulation")

st.divider()

st.subheader("Payoff Timeline")
st.info("Simulation results placeholder")

st.subheader("Strategy Comparison")
st.info("Strategy comparison chart placeholder")
