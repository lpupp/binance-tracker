"""TODO.

TODO LR:
[ ] Docstrings
[ ] Get more indicators. E.g.:
    [ ] First and second derivatives
    [ ] Smooth indicators
    [ ] Dummies and interactions (maybe this should be done by trading bot...)
"""
import numpy as np

from utils import create_fn_ohlc, create_fn_c,  smooth, get_first_derivative, \
    get_second_derivative

from ta import rsi, ema_indicator, stoch, stoch_signal, bollinger_lband, \
    bollinger_hband

indicator_functions = {'rsi': create_fn_c(rsi),
                       'ema': create_fn_c(ema_indicator),
                       'percent_k': create_fn_ohlc(stoch),
                       'percent_d': create_fn_ohlc(stoch_signal),
                       'l_bb': create_fn_c(bollinger_lband),
                       'u_bb': create_fn_c(bollinger_hband)}


def kwargs_error_handling(kwargs):
    """Error handlings for Indicator init kwargs."""
    if not isinstance(kwargs, dict):
        raise ValueError("`kwargs` should be dict: {'new_indicator': periods_list, ...}")
    for k, v in kwargs.items():
        if not isinstance(v, list):
            raise ValueError('All kwargs arguments must be lists')
        for vi in v:
            if not isinstance(vi, int):
                raise ValueError('All elements of kwargs arguments must be ints')


class Indicator():
    def __init__(self, **kwargs):
        """Initialize indicators object.

        kwargs: new_indicator=periods_list
                e.g. rsi=[14], ema = [7, 25, 99], percent_k=[14],
                     percent_d=[14], ...
        """
        self.indicators = {}
        self.update_indicators(kwargs)
        if len(self.indicators) == 0:
            raise ValueError('no kwargs provided')

    def update_indicators(self, kwargs):
        """kwargs must be a dict."""
        kwargs_error_handling(kwargs)
        for k, v in kwargs.items():
            for vi in v:
                if k in indicator_functions.keys():
                    self.indicators.update({k + '_' + str(vi): indicator_functions[k](vi)})
                else:
                    raise NotImplementedError('{} not in indicator_functions.'.format(k))

    def names(self):
        """Return names of indicators (format: nm_period)."""
        return list(self.indicators.keys())

    def __call__(self, df, full_df=False, d1=False, d2=False, smooth_periods=None):
        """Calculate indicators on df.

        args:
            smooth_periods: list of smooth periods.
        """
        df = df.copy()
        n = len(df.index)
        for k, v in self.indicators.items():
            periods = int(k.split('_')[-1])
            df[k] = v(df.high, df.low, df.close) if n >= periods else np.full((n, ), np.nan)

        if d1:
            df = self.get_derivatives(df, d2, full_df)

        if smooth_periods is not None:
            df = self.get_smooth(df, smooth_periods, full_df)

        if full_df:
            return df
        else:
            return df.tail(1)

    def get_derivatives(self, df, d2=False, full_df=False):
        """Calculate (first and second) derivatives of df indicators."""
        df = df.copy()
        if d2:
            df = get_second_derivative(df, self.names())
        else:
            df = get_first_derivative(df, self.names())

        if full_df:
            return df
        else:
            return df.tail(1)

    def get_smooth(self, df, periods, full_df=False):
        """Smooth indicators."""
        df = df.copy()
        if isinstance(periods, int):
            periods = [periods]
        for i in periods:
            df = smooth(df, self.names(), period=i)

        if full_df:
            return df
        else:
            return df.tail(1)

    def custom(self, df, full_df=False):
        """Add custom indicators here as new method (below).

        For example, calculate the width of bollinger bands. Update call
        function accordingly.
        """
        df = df.copy()

        bb_u = [e for e in df.columns if 'bb_u' in e]
        bb_l = [e for e in df.columns if 'bb_l' in e]
        df['bb_width'] = df[bb_u[0]] - df[bb_l[0]]

        if full_df:
            return df
        else:
            return df.tail(1)
