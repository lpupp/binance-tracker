"""Connect to binance API: get, process, and store ticker stream.

TODO LR:
[ ] Docstrings
[ ] Test

Ticker stream output:
{
  "e": "kline",     // Event type
  "E": 123456789,   // Event time
  "s": "BNBBTC",    // Symbol
  "k": {
    "t": 123400000, // Kline start time
    "T": 123460000, // Kline close time
    "s": "BNBBTC",  // Symbol
    "i": "1m",      // Interval
    "f": 100,       // First trade ID
    "L": 200,       // Last trade ID
    "o": "0.0010",  // Open price
    "c": "0.0020",  // Close price
    "h": "0.0025",  // High price
    "l": "0.0015",  // Low price
    "v": "1000",    // Base asset volume
    "n": 100,       // Number of trades
    "x": false,     // Is this kline closed?
    "q": "1.0000",  // Quote asset volume
    "V": "500",     // Taker buy base asset volume
    "Q": "0.500",   // Taker buy quote asset volume
    "B": "123456"   // Ignore
  }
}

"""
import time

import pandas as pd

from utils import printv, format_current_stream, dict_2_df, resample

from binance.websockets import BinanceSocketManager
from binance.enums import *

msg_dict = {'start_t': 't', 'end_t': 'T', 'open': 'o', 'high': 'h',
            'low': 'l', 'close': 'c', 'volume': 'v', 'n_trades': 'n'}


class KLineTracker():
    def __init__(self, symbol, indicator, df_klines, bot, client=None, verbose=1):
        self.counter = 0
        self.symbol_nm = symbol.upper()
        self.symbol = symbol.upper().replace('_', '')
        self.indicator = indicator
        self.bot = bot
        self.verbose = verbose
        self.df_klines = df_klines
        self.ws_hist = self.df_klines.df_1T.copy()

    def process_message(self, msg):
        """Recieve ticker message (see intro docstrings) from Binance."""
        printv('Stream: {}; keys: {}'.format(msg, msg.keys()), self.verbose)
        printv('----------------------------------------------', self.verbose)
        printv(self.counter, self.verbose)

        current_stream, e_t = msg['k'], int(msg['E'])
        self.process_inputs(current_stream, e_t, 100)

    def process_inputs(self, current_stream, event_time, save_iter=100):
        """Process and evaluate incoming ticker message."""
        self.counter += 1

        self.process_klines(current_stream, save_iter)

        print('current_volume', current_stream['v'])
        self.bot(self.df_klines, self.symbol_nm, self.verbose)

        if current_stream['x']:
            print('{} candle closed at {}'.format(self.symbol, pd.to_datetime(event_time, unit='ms')))

        if self.counter == save_iter:
            printv('Save data', self.verbose)
            self.df_klines.save('./output/data')
            self.counter = 0

    def get_current_values(self, current_stream, n_tail=500):
        """Format current values from ticker stream and compute indicators."""
        klines = format_current_stream(current_stream, msg_dict.items())
        klines = dict_2_df(klines)
        df = self.df_klines.get_recent(n_tail).loc[:, msg_dict.keys()]
        df = self.indicator(df.append(klines), full_df=False, d1=False, d2=False, smooth_periods=[5])
        return df

    def process_klines(self, current_stream, save_iter=100):
        """Update kline while candle is open.

        The ticker message streams price updates while a candle of a given
        frequency is open. This price updates need to be recorded in the open
        candle's entry (not by multiple candles). Once the candle is closed,
        the final price (i.e. close price) needs to be correct, and a new candle
        is opened. Multiple candles for a single freq window cannot be open.
        """
        df = format_current_stream(current_stream, msg_dict.items())

        if self.ws_hist.loc[self.ws_hist['start_t'] == df['start_t']].empty:
            printv('Append ws_hist', self.verbose)
            df = dict_2_df(df)
            self.ws_hist = self.ws_hist.append(df)
        else:
            printv('Update ws_hist', self.verbose)
            start = time.time()
            self.ws_hist.loc[self.ws_hist['start_t'] == df['start_t'], 'end_t'] = df['end_t']
            self.ws_hist.loc[self.ws_hist['start_t'] == df['start_t'], 'open'] = df['open']
            self.ws_hist.loc[self.ws_hist['start_t'] == df['start_t'], 'high'] = df['high']
            self.ws_hist.loc[self.ws_hist['start_t'] == df['start_t'], 'low'] = df['low']
            self.ws_hist.loc[self.ws_hist['start_t'] == df['start_t'], 'close'] = df['close']
            self.ws_hist.loc[self.ws_hist['start_t'] == df['start_t'], 'volume'] = df['volume']
            self.ws_hist.loc[self.ws_hist['start_t'] == df['start_t'], 'n_trades'] = df['n_trades']

            printv('Updating ws_hist time: {}'.format(time.time()-start), self.verbose)

        # TODO(lpupp) this doesn't work yet...
        start = time.time()
        self.resample_for_update()
        printv('Resample time: {}'.format(time.time()-start), self.verbose)

        if self.counter == save_iter:
            printv('Save websocket history', self.verbose)
            # TODO

    def resample_for_update(self):
        """Resample updates for the various frequencies of interest.

        This script only streams 1T candles. If we are also interested in
        frequencies larger than a 1T, we need to aggregate the 1T candles
        correctly.
        """
        for freq in self.df_klines.df_freqs:
            start = time.time()
            df_freq = getattr(self.df_klines, 'df_' + freq)
            df_freq = df_freq.drop(df_freq.tail(1).index)
            t_latest = df_freq.tail(1)['end_t'].values.item()
            df_new = self.ws_hist.loc[self.ws_hist['start_t'] > t_latest]
            if freq in self.df_klines.df_freqs[1:]:
                df_new = resample(df_new, freq)

            df_new = self.indicator(df_freq.loc[:, msg_dict.keys()].tail(110).append(df_new), full_df=False, d1=False, d2=False, smooth_periods=[5])
            df_freq = df_freq.append(df_new)
            setattr(self.df_klines, 'df_' + freq, df_freq)
            printv('Resample freq {} time: {}'.format(freq, time.time()-start), self.verbose)

    def start_ticker(self, client, freq='1m'):
        """Start connection to ticker."""
        self.bm = BinanceSocketManager(client)
        if freq in ['1m', '1T']:
            conn_key = self.bm.start_kline_socket(self.symbol,
                                                  self.process_message,
                                                  interval=KLINE_INTERVAL_1MINUTE)
        else:
            raise NotImplementedError

        self.bm.start()

    def end_ticker(self):
        """Close connection to ticker."""
        self.bm.close()
