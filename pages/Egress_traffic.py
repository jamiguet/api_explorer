import requests
import streamlit as st

external_ip = requests.get('https://ident.me').text

st.text(f"Egress IP: {external_ip}")
