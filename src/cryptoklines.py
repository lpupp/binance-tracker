"""Object to track and record klines of crypto trading pair."""
import os
import sys
sys.path.append('./src')

import pandas as pd
import numpy as np

from utils import printv, klines_2_df

names = ['start_t', 'end_t', 'open', 'high', 'low', 'close', 'volume', 'n_trades']
all_freqs = ['1T', '3T', '5T', '15T', '30T', '1H', '2H', '4H', '6H', '12H', '24H']


class CryptoKlines():
    def __init__(self,
                 symbol,
                 indicator,
                 client,
                 start_time='1 Jan, 2017',
                 load_path=None,
                 verbose=1):
        self.symbol = symbol.upper().replace('_', '')
        self.indicator = indicator
        self.verbose = verbose
        self.client = client

        if load_path:
            self.load(load_path)
            self.fill_2_present()
        else:
            # Get klines
            self.df_1T = klines_2_df(self.symbol, start_time, self.client)
            self.save(load_path or './output/data/')
            self.fill_2_present()

        # Get indicators
        self.df_1T = self.indicator(self.df_1T, full_df=True, d1=False, d2=False, smooth_periods=[5])
        self.df_freqs = ['1T']
        self.resample_all()

    def fill_2_present(self):
        """Fill klines from most recent recorded date to present."""
        t_last = self.df_1T['end_t'].values[-1].item()
        klines = klines_2_df(self.symbol, t_last)

        self.update(klines, '1T', drop_dups=True)

    def reindex_all(self, n=100):
        """Reindex the frequencies of all dataframes to 1T."""
        out = {'1T': self.df_1T.tail(n)}
        for freq in all_freqs[1:]:
            printv('Interpolating {}'.format(freq), self.verbose)
            df = getattr(self, 'df_' + freq)
            df = df.copy()
            df = df.asfreq(freq='1T')
            df = df.interpolate(method='index')
            out.update({freq: df.tail(n)})

    def resample(self, freq):
        """Resample 1T klines to freq by binning."""
        if freq not in all_freqs:
            raise ValueError('inappropriate provided')

        df = self.df_1T.loc[:, names].copy()

        printv('Resampling', self.verbose)
        df = pd.concat([df['start_t'].resample(freq).first(),
                        df['end_t'].resample(freq).last(),
                        df['open'].resample(freq).first(),
                        df['high'].resample(freq).max(),
                        df['low'].resample(freq).min(),
                        df['close'].resample(freq).last(),
                        df['volume'].resample(freq).sum(),
                        df['n_trades'].resample(freq).sum()], axis=1)

        printv('Calculating indicators', self.verbose)
        df = self.indicator(df, full_df=True, d1=False, d2=False, smooth_periods=[5])

        setattr(self, 'df_' + freq, df)
        self.df_freqs.append(freq)

    def resample_all(self):
        """Resample 1T klines to all frequencies by binning."""
        for freq in all_freqs[1:]:
            printv('Resample freq: {}'.format(freq), self.verbose)
            self.resample(freq)
        printv('Done resampling!', self.verbose)

    def update(self, x, df_attr, drop_dups=False):
        """Update kline dataframe."""
        printv('Update datatable', self.verbose)
        df = getattr(self, 'df_' + df_attr)

        df = df.append(x)
        if drop_dups:
            df.drop_duplicates(inplace=True)

        setattr(self, 'df_' + df_attr, df)

    def get_recent(self, n):
        """Get last n 1T klines."""
        return self.df_1T.tail(n).copy()

    def save(self, path):
        """Save 1T klines."""
        if os.path.splitext(path)[1] == '':
            path = os.path.join(path, self.symbol + '.csv')

        print('Saving to {}'.format(path))
        self.df_1T.loc[:, names].to_csv(path)

    def load(self, path):
        """Load 1T klines from path."""
        if os.path.splitext(path)[1] == '':
            path = os.path.join(path, self.symbol + '.csv')
        if not os.path.isfile(path):
            raise ValueError('load_path={} does not exist.'.format(path))

        dtypes = {'start_t': np.int64,
                  'end_t': np.int64,
                  'open': np.float32,
                  'high': np.float32,
                  'low': np.float32,
                  'close': np.float32,
                  'volume': np.float32,
                  'n_trades': np.int64}

        self.df_1T = pd.read_csv(path, index_col=0, dtype=dtypes)
        print('Data loaded from {}'.format(path))
        self.df_1T.index = pd.to_datetime(self.df_1T.index)
