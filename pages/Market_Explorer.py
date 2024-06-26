import datetime
import pandas as pd
import streamlit as st
from util import call, load_pump_data, get_field_set, get_field_filtered_list, to_unix, \
    plot_candles, plot_series, annotate_symbol, get_all_metrics
from io import StringIO
from ccxt.kucoin import BadSymbol
from functools import reduce
import plotly.express as px

pumped_coins = load_pump_data(st.session_state.db)

assets = call("https://api.glassnode.com/v1/metrics/assets")
field_set = list(set([item for sublist in get_field_set('tags', assets) for item in sublist]))

tag = st.sidebar.selectbox("Asset tags", field_set)

metrics_list = list(filter(lambda item: 'market' in item['path'], get_all_metrics()))
metrics_list.sort(key=lambda item: item['path'])

supported_coins = [asset['symbol'] for asset in reduce(lambda acc, val: acc + val['assets'], metrics_list, [])]

filtered_assets = get_field_filtered_list('symbol', tag, assets)
filtered_assets = list(filter(lambda symbol: (symbol in st.session_state.ku_markets or symbol in st.session_state.binance_markets) and symbol in st.session_state.supported_coins,
                              filtered_assets))
filtered_assets = list(
    map(lambda symbol: annotate_symbol(symbol, pumped_coins, st.session_state.ku_markets,
                                       st.session_state.binance_markets, st.session_state.okx_markets),
        filtered_assets))
current_asset = st.sidebar.selectbox(f"Assets ({len(filtered_assets)})", filtered_assets).split(' ')[0]

start = st.sidebar.date_input('Start Date', datetime.date.today() - datetime.timedelta(days=60))
end = st.sidebar.date_input('End Date', datetime.date.today())

kucoin_res = {
    '1h': '1h',
    '24h': '1d'
}
resolution = st.sidebar.selectbox("Time resolution:", list(kucoin_res.keys()))

st.title('Market Explorer')

current_metric = st.sidebar.multiselect('Select metric:', metrics_list,
                                        format_func=lambda item: item['path'].split('/')[-1])

for metric in current_metric:
    path = metric['path']
    metric_name = path.split('/')[-1]
    st.text(f'{metric_name}')
    st.json(metric)

    params = {
        'a': current_asset,
        's': to_unix(start),
        'u': to_unix(end),
        'i': resolution,
        'f': 'csv',
        'e': 'kucoin',
        'timestamp_format': 'humanized'
    }

    try:
        data = call(f'https://api.glassnode.com{path}', params=params, as_text=True)
        metric_df = pd.read_csv(StringIO(data))

        columns = [val for val in metric_df.columns]
        columns = list(filter(lambda col: col != 'timestamp', columns))
        fig = px.line(metric_df, x='timestamp', y=columns)
        st.plotly_chart(fig)
    except AssertionError as ae:
        st.error(f"{ae} \nAllowed Assets: {', '.join(list(map(lambda item: item['symbol'], metric['assets'])))}")

    num_candles = int((end - start).total_seconds() / 3600 / (24 if resolution == '24h' else 1))

    try:
        kucoin_candles = st.session_state.kucoin.fetch_ohlcv(f"{current_asset}-USDT", timeframe=kucoin_res[resolution],
                                                             since=to_unix(start) * 1000,
                                                             limit=num_candles)

        plot_candles(kucoin_candles, f'{current_asset} Kucoin')
    except BadSymbol as bs:
        st.error(f"Bad symbol: {bs}")

    try:
        binance_candles = st.session_state.binance.fetch_ohlcv(f"{current_asset}/USDT",
                                                               timeframe=kucoin_res[resolution],
                                                               since=to_unix(start) * 1000,
                                                               limit=num_candles)

        plot_candles(binance_candles, f'{current_asset} Binanace')
    except BadSymbol as bs:
        st.error(f"Bad symbol: {bs}")

    try:
        okx_candles = st.session_state.okx.fetch_ohlcv(f"{current_asset}/USDT", timeframe=kucoin_res[resolution],
                                      since=to_unix(start) * 1000,
                                      limit=num_candles)

        plot_candles(okx_candles, f'{current_asset} OKX')
    except BadSymbol as bs:
        st.error(f"Bad symbol: {bs}")
