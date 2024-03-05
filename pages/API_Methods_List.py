import datetime
import time
import json
import streamlit as st
from util import call, get_all_metrics


def supply_distribution_relative():
    three_months_ago = datetime.datetime.now() - datetime.timedelta(days=3 * 30)
    tmau = int(time.mktime(three_months_ago.timetuple()))
    nu = int(time.mktime(datetime.datetime.now().timetuple()))
    params = {
        'a': 'BTC',
        's': tmau,
        'u': nu,
        'i': '24h',
        'f': 'json'
    }
    return call("https://api.glassnode.com/v1/metrics/entities/supply_distribution_relative", params)


def to_api_path(path_list):
    url_dict = {}
    for url, params in map(lambda item: [item['path'], item['params']], path_list):
        path_split = url.strip('/').split('/')
        current_dict = url_dict
        for i, element in enumerate(path_split):
            if i != len(path_split) - 1:
                # for non-terminal keys, simply create a nested dictionary as before
                current_dict = current_dict.setdefault(element, {})
            else:
                # for terminal key, set its value to params
                current_dict[element] = params
    return url_dict


st.title('GlassNode API exploration')

st.text("All metrics endpoints available in GlassNode API")
metric_paths_list = list(
    map(lambda item: {'path': item['path'],
                      'params': {k: v for k, v in item.items() if k not in ['path', 'tier', 'paramsDomain', 'formats']}},
        get_all_metrics()))
metric_paths_list = to_api_path(metric_paths_list)
for path in map(lambda item: item['path'], get_all_metrics()):
    st.text(path)
# st.json(json.dumps(metric_paths_list))

st.text("All metrics")
st.json(get_all_metrics())

st.text('Supply distribution relative')
st.json(json.dumps(supply_distribution_relative()))
