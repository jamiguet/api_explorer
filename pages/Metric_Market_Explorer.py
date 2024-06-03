import streamlit as st
from util import init_session, get_all_metrics
import json

init_session()
st.title("Metric Market Explorer")

active_exchanges = st.sidebar.multiselect("Select Exchanges", options=['kucoin', 'okx', 'binance'])
tiers = set(map(lambda entry: entry['tier'], get_all_metrics()))
current_tier =st.sidebar.selectbox("Select metric tier", tiers)

filtered_metrics = list(filter(lambda item: item['tier'] in tiers ,get_all_metrics()))

metric_names = list(map(lambda entry: entry['name'], filtered_metrics))
metrics = st.sidebar.multiselect("Select Metrics", options=metric_names)
filtered_metrics = list(filter(lambda item: item['name'] in metrics, filtered_metrics))

if len(filtered_metrics) == 0:
    st.warning("Select at least one metric")
    st.stop()

st.json(json.dumps(filtered_metrics, sort_keys=True, indent=4))
st.json(json.dumps(list(map(lambda entry: entry['resolutions'], filtered_metrics))))

resolutions = set(list(map(lambda entry: entry['resolutions'], filtered_metrics))[0])
assets = list()
for entry in map(lambda entry: entry['assets'], filtered_metrics):
    assets.extend(list(map(lambda item: item['symbol'], entry)))

asset = st.sidebar.selectbox("Select coin",options=assets)
resolution = st.sidebar.selectbox("Select resolution",options=resolutions)

for current_metric in metrics:
    st.subheader(current_metric.replace('_','').title())