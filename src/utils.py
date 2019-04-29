"""Utils for binance-tracker tools.

Assume that the utils are untested. Some tests have been done, but are not
published.

TODO LR:
[ ] Docstrings
[ ] Test
"""
import os
import time
import yaml

import pandas as pd
import numpy as np

from binance.client import Client


def get_config(config):
    with open(config, 'r') as stream:
        return yaml.load(stream)


def get_holding(client, symbol):
    """Get (free) Binance holding for certain crypto symbol."""
    return client.get_asset_balance(asset=symbol.replace('_BTC', ''))['free']


def resample(df, freq):
    """Resample klines dataframe to specified frequency."""
    df = pd.concat([df['start_t'].resample(freq).first(),
                    df['end_t'].resample(freq).last(),
                    df['open'].resample(freq).first(),
                    df['high'].resample(freq).max(),
                    df['low'].resample(freq).min(),
                    df['close'].resample(freq).last(),
                    df['volume'].resample(freq).sum(),
                    df['n_trades'].resample(freq).sum()],
                   axis=1)
    return df


def format_current_stream(cs, nm):
    """Format current stream value to dict."""
    return dict((k, [float(cs[v])]) for k, v in nm)


def smooth(df, indicator_names, period=5, verbose=0):
    """Smooth indicator values."""
    df = df.copy()
    for nm in df.columns.values:
        if nm in indicator_names:
            printv(nm, verbose)
            df[nm+'_smooth'] = df[nm].rolling(window=period,center=False).mean()
    return df


def get_first_derivative(df, indicator_names, verbose=0):
    """Get indicator's first derivative."""
    df = df.copy()
    for nm in df.columns.values:
        if nm in indicator_names:
            printv(nm, verbose)
            df['d_'+nm] = df[nm].diff()
    return df


def get_second_derivative(df, indicator_names, verbose=0):
    """Get indicator's second derivative."""
    df = get_first_derivative(df)
    for nm in df.columns.values:
        if nm in ['d_'+nm for nm in indicator_names]:
            printv(nm, verbose)
            df['d2_'+nm] = df[nm].diff()
    return df


def dict_2_df(dt_dict):
    """Convert dict to pd.DataFrame with time index."""
    df = pd.DataFrame(dt_dict, columns=dt_dict.keys())
    if 'start_t' in dt_dict.keys():
        df['time'] = pd.to_datetime(df['start_t'], unit='ms')
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)
    return df


def get_klines(symbol, time, client=None, freq=Client.KLINE_INTERVAL_1MINUTE):
    """Get historical klines."""
    if isinstance(time, str):
        return client.get_historical_klines(symbol, freq, time)
    elif isinstance(time, int):
        return get_historical_klines(symbol, freq, time)
    else:
        raise NotImplementedError('`time` is of type:', type(time))


def process_klines(klines):
    """Process klines."""
    klines_dict = {'start_t': np.array([e[0] for e in klines]),
                   'end_t': np.array([e[6] for e in klines]),
                   'open': np.array([float(e[1]) for e in klines]),
                   'high': np.array([float(e[2]) for e in klines]),
                   'low': np.array([float(e[3]) for e in klines]),
                   'close': np.array([float(e[4]) for e in klines]),
                   'volume': np.array([float(e[5]) for e in klines]),
                   'n_trades': np.array([e[8] for e in klines])}
    return klines_dict


def klines_2_df(symbol, time, client=None, freq=Client.KLINE_INTERVAL_1MINUTE):
    """Wrapper for get_klines, process_klines, and dict_2_df."""
    klines = get_klines(symbol, time, client, freq)
    klines = process_klines(klines)
    klines = dict_2_df(klines)
    return klines


def printv(string, verbose):
    """Print function with verbose option."""
    if verbose in [1, 'debug']:
        print(string)


def create_fn_hl(fn):
    """Repackage indicator functions to only take hl as args."""
    def f1(period):
        def f2(high, low, close):
            return fn(high, low, period)
        return f2
    return f1


def create_fn_hlc(fn):
    """Repackage indicator functions to only take ohl as args."""
    def f1(period):
        def f2(high, low, close):
            return fn(high, low, close, period)
        return f2
    return f1


def create_fn_c(fn):
    """Repackage indicator functions to only take closing price as arg."""
    def f1(period):
        def f2(high, low, close):
            return fn(close, period)
        return f2
    return f1


def notify(title, subtitle, message):
    """Notify (through notifaction window) of event."""
    t = '-title {!r}'.format(title)
    s = '-subtitle {!r}'.format(subtitle)
    m = '-message {!r}'.format(message)
    os.system('terminal-notifier {}'.format(' '.join([m, t, s])))


def _interval_to_milliseconds(interval):
    """Convert a Binance interval string to milliseconds.

    :param interval: Binance interval string 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
    :type interval: str
    :return:
         None if unit not one of m, h, d or w
         None if string not in correct format
         int value of interval in milliseconds

    source: https://sammchardy.github.io/binance/2018/01/08/historical-data-download-binance.html
    """
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60
    }

    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms


def get_historical_klines(symbol, interval, start_ts, end_str=None):
    """Get Historical Klines from Binance.

    See dateparse docs for valid start and end string formats http://dateparser.readthedocs.io/en/latest/
    If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Biannce Kline interval
    :type interval: str
    :param start_str: Start date string in UTC format
    :type start_str: str
    :param end_str: optional - end date string in UTC format
    :type end_str: str
    :return: list of OHLCV values

    source: https://sammchardy.github.io/binance/2018/01/08/historical-data-download-binance.html
    """
    # create the Binance client, no need for api key
    client = Client("", "")

    # init our list
    output_data = []

    # setup the max limit
    limit = 500

    # convert interval to useful value in seconds
    timeframe = _interval_to_milliseconds(interval)

    # if an end time was passed convert it
    end_ts = None

    idx = 0
    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 500 entries or the end_ts if set
        temp_data = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            startTime=start_ts,
            endTime=end_ts
        )

        # handle the case where our start date is before the symbol pair listed on Binance
        if not symbol_existed and len(temp_data):
            symbol_existed = True

        if symbol_existed:
            # append this loops data to our output data
            output_data += temp_data

            # update our start timestamp using the last value in the array and add the interval timeframe
            start_ts = temp_data[len(temp_data) - 1][0] + timeframe
        else:
            # it wasn't listed yet, increment our start date
            start_ts += timeframe

        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break

        # sleep after every 3rd call to be kind to the API
        if idx % 3 == 0:
            time.sleep(1)

    return output_data
