import copy
import datetime
import pandas as pd

import streamlit as st
from util import call, plot_transfer_count, load_pump_data, get_field_set, get_field_filtered_list, to_unix, \
    plot_candles, plot_series
from io import StringIO
import ccxt
from ccxt.kucoin import BadSymbol

db = st.connection("postgresql", type="sql")

kucoin = ccxt.kucoin({
    'adjustForTimeDifference': True,
    "apiKey": st.secrets.KUCOIN_API_KEY,
    "secret": st.secrets.KUCOIN_API_SECRET,
    'password': st.secrets.PASSWORD,
})

binance = ccxt.binance({
    'apiKey': st.secrets.BINANCE_API_KEY,
    'secret': st.secrets.BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',
    },
})

kucoin.load_markets()
binance.load_markets()

ku_markets = list(
    set(map(lambda symbol: symbol.split('/')[0],
            filter(lambda symbol: 'USDT' in symbol, kucoin.symbols))))

binance_markets = list(
    set(map(lambda symbol: symbol.split('/')[0],
            filter(lambda symbol: 'USDT' in symbol, binance.symbols))))

st.text(f"Kucoin: {ku_markets}")
st.text(f"Binanace: {binance_markets}")

st.title("Assets Per Exchange")

pumped_coins = load_pump_data(db)

assets = call("https://api.glassnode.com/v1/metrics/assets")
field_set = list(set([item for sublist in get_field_set('tags', assets) for item in sublist]))
tag = st.sidebar.selectbox("Asset tags", field_set)


def annotate_symbol(symbol, pump, ku_symbols, bi_symbols):
    return (f'{symbol} {" ⛽" if symbol in pump else ""} '
            f'({"B" if symbol in bi_symbols else ""}{"K" if symbol in ku_symbols else ""})')


filtered_assets = get_field_filtered_list('symbol', tag, assets)
filtered_assets = list(filter(lambda symbol: symbol in ku_markets or symbol in binance_markets, filtered_assets))
filtered_assets = list(
    map(lambda symbol: annotate_symbol(symbol, pumped_coins, ku_markets, binance_markets), filtered_assets))
current_asset = st.sidebar.selectbox(f"Assets ({len(filtered_assets)})", filtered_assets).split(' ')[0]

start = st.sidebar.date_input('Start Date', datetime.date.today() - datetime.timedelta(days=60))
end = st.sidebar.date_input('End Date', datetime.date.today())

kucoin_res = {
    '1h': '1h',
    '24h': '1d'
}
resolution = st.sidebar.selectbox("Time resolution:", list(kucoin_res.keys()))

params = {
    'a': current_asset,
    's': to_unix(start),
    'u': to_unix(end),
    'i': resolution,
    'f': 'csv',
    'timestamp_format': 'humanized'
}

transfer_out = call("https://api.glassnode.com/v1/metrics/addresses/sending_count",
                    params=params,
                    as_text=True)

transfer_in = call("https://api.glassnode.com/v1/metrics/addresses/receiving_count",
                   params=params,
                   as_text=True)

plot_transfer_count(transfer_in, transfer_out, 'Address transfer', 'Address count')

exchange_out = call("https://api.glassnode.com/v1/metrics/addresses/sending_to_exchanges_count",
                    params=params,
                    as_text=True)

exchange_in = call("https://api.glassnode.com/v1/metrics/addresses/receiving_from_exchanges_count",
                   params=params,
                   as_text=True)

plot_transfer_count(exchange_in, exchange_out, 'Exchange address transfer', 'Exchange address count')

tvol_params = copy.copy(params)
tvol_params['c'] = 'USD'
tvol_params['f'] = 'CSV'
transfer_volume = call("https://api.glassnode.com/v1/metrics/transactions/transfers_volume_sum", tvol_params,
                       as_text=True)

tvol_df = pd.read_csv(StringIO(transfer_volume))

plot_series(tvol_df, 'Transfer volume (USD)')


num_candles = int((end - start).total_seconds() / 3600 / (24 if resolution == '24h' else 1))

try:
    kucoin_candles = kucoin.fetch_ohlcv(f"{current_asset}-USDT", timeframe=kucoin_res[resolution],
                                        since=to_unix(start) * 1000,
                                        limit=num_candles)

    plot_candles(kucoin_candles, 'Kucoin')
except BadSymbol as bs:
    st.error(f"Bad symbol: {bs}")

try:
    binance_candles = binance.fetch_ohlcv(f"{current_asset}/USDT", timeframe=kucoin_res[resolution],
                                          since=to_unix(start) * 1000,
                                          limit=num_candles)

    plot_candles(binance_candles, 'Binanace')
except BadSymbol as bs:
    st.error(f"Bad symbol: {bs}")
