import streamlit as st
from util import init_session, get_all_metrics
import json

init_session()
st.title("Metric Market Explorer")


st.json(json.dumps(get_all_metrics(), sort_keys=True, indent=4))

active_exchanges = st.sidebar.multiselect("Select Exchanges", options=['kucoin', 'okx', 'binance'])
tiers = set(map(lambda entry: entry['tier'], get_all_metrics()))
current_tier =st.sidebar.selectbox("Select metric tier", tiers)

filtered_metrics = list(filter(lambda item: item['tier'] in tiers ,get_all_metrics()))

metric_names = list(map(lambda entry: entry['name'], filtered_metrics))
metrics = st.sidebar.multiselect("Select Metrics", options=metric_names)

st.json(json.dumps(list(filter(lambda item: item['name'] in metrics, filtered_metrics)), sort_keys=True, indent=4))
resolutions = set(map(lambda entry: entry['resolutions'], filtered_metrics))
assets = set(map(lambda entry: entry['asset']['symbol'], filtered_metrics))


