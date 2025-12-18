import streamlit as st


st.set_page_config(
    page_title="Dashboard | MyFin",
    page_icon="??",
    layout="wide",
)

st.title("Dashboard")
st.caption("Executive overview of debts, savings, and risk.")

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("Total Debt (CAD)", "-")
with kpi_cols[1]:
    st.metric("Total Savings (CAD)", "-")
with kpi_cols[2]:
    st.metric("Net Position (CAD)", "-")
with kpi_cols[3]:
    st.metric("Highest Risk Debt", "-")

st.divider()

st.subheader("Risk Heatmap")
st.info("Risk heatmap placeholder")

st.subheader("Debt vs Savings Over Time")
st.info("Time series placeholder")

st.subheader("Debt by Type")
st.info("Pie chart placeholder")

st.subheader("Debt by Currency")
st.info("Pie chart placeholder")
