import streamlit as st
from util import init_session

st.set_page_config(
    page_title="Glassnode API explorer"
)

init_session()

st.write("# Glassnode explorer dashboard")

st.sidebar.success("Select a page above.")

