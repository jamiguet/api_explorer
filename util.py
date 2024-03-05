import streamlit as st
import requests
import pandas as pd
import time
import numpy as np
from io import StringIO
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def call(method, params=None, as_text=False):
    response = requests.get(method, headers={"X-Api-Key": st.secrets.GLASSNODE_API_KEY}, params=params, verify=False)

    # check the HTTP status code of the response
    assert response.status_code == 200, (
        f"An error occurred while calling {method}. Status code: {response.status_code}."
        f" Reason: {response.reason}. Content: {response.text}")

    if not as_text:
        return response.json()
    else:
        return response.text


def get_field_list(name, collection):
    return list(map(lambda item: item[name], collection))


def get_field_filtered_list(name, tag, collection):
    return sorted(list(map(lambda item: item[name], filter(lambda item: tag in item['tags'], collection))))


def get_field_set(name, collection):
    return sorted(list(map(lambda item: item[name], collection)))


@st.cache_data
def load_pump_data(_conn):
    sql_str = 'select "Coin" from pumps.pumps;'

    pump_events = pd.read_sql(sql_str, _conn.connect())

    return pump_events.Coin.unique().tolist()


def to_unix(time_point):
    return int(time.mktime(time_point.timetuple()))


def pseudolog(val):
    return np.sign(val) * np.log1p(np.abs(val))


def update_y_ticks(y):
    return '{:.0f}'.format(np.sign(y) * ((np.exp(np.abs(y))) - 1))


def plot_transfer_count(result_in, result_out, title, ylabel, pseudo_log=False):
    data = StringIO(result_out)
    data_in = StringIO(result_in)
    result_df = pd.read_csv(data)
    result_df = result_df.join(pd.read_csv(data_in), lsuffix='_in', rsuffix='_out', how='inner')
    result_df = result_df.rename(columns={'value_in': 'receiving', 'value_out': 'sending'})
    result_df.sending = -1 * result_df.sending
    result_df['disparity'] = result_df.sending + result_df.receiving
    if pseudo_log:
        result_df['disparity'] = result_df['disparity'].apply(pseudolog)
        result_df['sending'] = result_df.sending.apply(pseudolog)
        result_df['receiving'] = result_df['receiving'].apply(pseudolog)
    fig = go.Figure()
    for series in ['sending', 'receiving', 'disparity']:
        fig.add_trace(go.Scatter(x=result_df['timestamp_in'], y=result_df[series], mode='lines', name=series))
    fig.update_layout(
        title=go.layout.Title(text=f'{title} count {"pseudoLog" if pseudo_log else ""}'),
        yaxis=dict(
            title=ylabel
        )
    )
    st.plotly_chart(fig)


def plot_candles(raw_candles, exchange):
    data_pd = pd.DataFrame(raw_candles, columns=['unix', 'open', 'high', 'low', 'close', 'volume'])

    data_pd['date'] = pd.to_datetime(data_pd['unix'].apply(lambda it: it / 1000),
                                     unit='s')

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, subplot_titles=(f"OHLC {exchange} (n={len(data_pd)})", 'Volume'),
                        row_width=[0.2, 0.7])
    # Plot OHLC on 1st row
    fig.add_trace(go.Candlestick(go.Candlestick(x=data_pd['date'],
                                                open=data_pd['open'],
                                                high=data_pd['high'],
                                                low=data_pd['low'],
                                                close=data_pd['close']),
                                 name=f"OHLC"), row=1, col=1)
    # Bar trace for volumes on 2nd row without legend
    fig.add_trace(go.Bar(x=data_pd['date'], y=data_pd['volume'], showlegend=False), row=2, col=1)
    # Do not show OHLC's rangeslider plot
    fig.update(layout_xaxis_rangeslider_visible=False)
    st.plotly_chart(fig)


def plot_series(data, title, logy):
    fig = px.line(data, x='timestamp', y='value', title=title, log_y=logy)
    st.plotly_chart(fig)


def annotate_symbol(symbol, pump, ku_symbols, bi_symbols, okx_symbols):
    return (f'{symbol} {" ⛽" if symbol in pump else ""} '
            f'({"B" if symbol in bi_symbols else ""}'
            f'{"K" if symbol in ku_symbols else ""}'
            f'{"O" if symbol in okx_symbols else ""})')


@st.cache_data
def get_all_metrics():
    return call("https://api.glassnode.com/v2/metrics/endpoints")
