import streamlit as st


st.set_page_config(
    page_title="MyFin Intelligence",
    page_icon="??",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
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
