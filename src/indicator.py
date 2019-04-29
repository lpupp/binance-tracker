"""TODO.

TODO LR:
[ ] Docstrings
[ ] Get more indicators. E.g.:
    [ ] First and second derivatives
    [ ] Smooth indicators
    [ ] Dummies and interactions (maybe this should be done by trading bot...)
"""
import numpy as np

from utils import create_fn_hlc, create_fn_c,  create_fn_hl, smooth, \
    get_first_derivative, get_second_derivative


def config_error_handling(config):
    """Error handlings for indicator config."""
    if not isinstance(config, dict):
        raise ValueError("`kwargs` should be dict: {'new_indicator': periods_list, ...}")
    for k, v in config.items():
        if not isinstance(v, list):
            config[k] = list(v)
        for vi in v:
            if not isinstance(vi, int):
                raise ValueError('All elements of kwargs arguments must be ints')


def import_and_init(config):
    """Import and repackage indicator function from ta.

    Repackage indicator:
    - If the indicators expects (close, ...), repackage with create_fn_c
    - If the indicators expects (high, low, ...), repackage with create_fn_hl
    - If the indicators expects (high, low, close, ...), repackage with create_fn_hlc

    Note that some of the functions require extra arguments that cannot be passed in.

    TODO: this is quite an ugly hack. could use ta.TAFeaturesTransform
    (https://github.com/bukosabino/ta/blob/master/ta/pipeline_wrapper.py)
    """
    ifns = {}
    for k in config:
        if k == 'rsi':
            from ta import rsi
            ifns.update({'rsi': create_fn_c(rsi)})
        elif k == 'money_flow_index':
            from ta import money_flow_index
            ifns.update({'money_flow_index': create_fn_hlc(money_flow_index)})
        elif k == 'tsi':
            from ta import tsi
            ifns.update({'tsi': create_fn_c(tsi)})
        elif k == 'uo':
            from ta import uo
            ifns.update({'uo': create_fn_hlc(uo)})
        elif k == 'stoch':
            from ta import stoch
            ifns.update({'stoch': create_fn_hlc(stoch)})
        elif k == 'stoch_signal':
            from ta import stoch_signal
            ifns.update({'stoch_signal': create_fn_hlc(stoch_signal)})
        elif k == 'wr':
            from ta import wr
            ifns.update({'wr': create_fn_hlc(wr)})
        elif k == 'ao':
            from ta import ao
            ifns.update({'ao': create_fn_hl(ao)})
        elif k == 'daily_return':
            from ta import daily_return
            ifns.update({'daily_return': create_fn_c(daily_return)})
        elif k == 'daily_log_return':
            from ta import daily_log_return
            ifns.update({'daily_log_return': create_fn_c(daily_log_return)})
        elif k == 'cumulative_return':
            from ta import cumulative_return
            ifns.update({'cumulative_return': create_fn_c(cumulative_return)})
        elif k == 'macd':
            from ta import macd
            ifns.update({'macd': create_fn_c(macd)})
        elif k == 'macd_signal':
            from ta import macd_signal
            ifns.update({'macd_signal': create_fn_c(macd_signal)})
        elif k == 'macd_diff':
            from ta import macd_diff
            ifns.update({'macd_diff': create_fn_c(macd_diff)})
        elif k == 'ema_indicator':
            from ta import ema_indicator
            ifns.update({'ema_indicator': create_fn_c(ema_indicator)})
        elif k == 'adx':
            from ta import adx
            ifns.update({'adx': create_fn_hlc(adx)})
        elif k == 'adx_pos':
            from ta import adx_pos
            ifns.update({'adx_pos': create_fn_hlc(adx_pos)})
        elif k == 'adx_neg':
            from ta import adx_neg
            ifns.update({'adx_neg': create_fn_hlc(adx_neg)})
        elif k == 'vortex_indicator_pos':
            from ta import vortex_indicator_pos
            ifns.update({'vortex_indicator_pos': create_fn_hlc(vortex_indicator_pos)})
        elif k == 'vortex_indicator_neg':
            from ta import vortex_indicator_neg
            ifns.update({'vortex_indicator_neg': create_fn_hlc(vortex_indicator_neg)})
        elif k == 'trix':
            from ta import trix
            ifns.update({'trix': create_fn_c(trix)})
        elif k == 'mass_index':
            from ta import mass_index
            ifns.update({'mass_index': create_fn_hl(mass_index)})
        elif k == 'ci':
            from ta import ci
            ifns.update({'ci': create_fn_hlc(ci)})
        elif k == 'dpo':
            from ta import dpo
            ifns.update({'dpo': create_fn_c(dpo)})
        elif k == 'kst':
            from ta import kst
            ifns.update({'kst': create_fn_c(kst)})
        elif k == 'kst_sig':
            from ta import kst_sig
            ifns.update({'kst_sig': create_fn_c(kst_sig)})
        elif k == 'ichimoku_a':
            from ta import ichimoku_a
            ifns.update({'ichimoku_a': create_fn_hlc(ichimoku_a)})
        elif k == 'ichimoku_b':
            from ta import ichimoku_b
            ifns.update({'ichimoku_b': create_fn_hlc(ichimoku_b)})
        elif k == 'aroon_up':
            from ta import aroon_up
            ifns.update({'aroon_up': create_fn_c(aroon_up)})
        elif k == 'aroon_down':
            from ta import aroon_down
            ifns.update({'aroon_down': create_fn_c(aroon_down)})
        elif k == 'average_true_range':
            from ta import average_true_range
            ifns.update({'average_true_range': create_fn_hlc(average_true_range)})
        elif k == 'bollinger_mavg':
            from ta import bollinger_mavg
            ifns.update({'bollinger_mavg': create_fn_c(bollinger_mavg)})
        elif k == 'bollinger_hband':
            from ta import bollinger_hband
            ifns.update({'bollinger_hband': create_fn_c(bollinger_hband)})
        elif k == 'bollinger_lband':
            from ta import bollinger_lband
            ifns.update({'bollinger_lband': create_fn_c(bollinger_lband)})
        elif k == 'bollinger_hband_indicator':
            from ta import bollinger_hband_indicator
            ifns.update({'bollinger_hband_indicator': create_fn_c(bollinger_hband_indicator)})
        elif k == 'bollinger_lband_indicator':
            from ta import bollinger_lband_indicator
            ifns.update({'bollinger_lband_indicator': create_fn_c(bollinger_lband_indicator)})
        elif k == 'keltner_channel_central':
            from ta import keltner_channel_central
            ifns.update({'keltner_channel_central': create_fn_hlc(keltner_channel_central)})
        elif k == 'keltner_channel_hband':
            from ta import keltner_channel_hband
            ifns.update({'keltner_channel_hband': create_fn_hlc(keltner_channel_hband)})
        elif k == 'keltner_channel_lband':
            from ta import keltner_channel_lband
            ifns.update({'keltner_channel_lband': create_fn_hlc(keltner_channel_lband)})
        elif k == 'keltner_channel_hband_indicator':
            from ta import keltner_channel_hband_indicator
            ifns.update({'keltner_channel_hband_indicator': create_fn_hlc(keltner_channel_hband_indicator)})
        elif k == 'keltner_channel_lband_indicator':
            from ta import keltner_channel_lband_indicator
            ifns.update({'keltner_channel_lband_indicator': create_fn_hlc(keltner_channel_lband_indicator)})
        elif k == 'donchian_channel_hband':
            from ta import donchian_channel_hband
            ifns.update({'donchian_channel_hband': create_fn_c(donchian_channel_hband)})
        elif k == 'donchian_channel_lband':
            from ta import donchian_channel_lband
            ifns.update({'donchian_channel_lband': create_fn_c(donchian_channel_lband)})
        elif k == 'donchian_channel_hband_indicator':
            from ta import donchian_channel_hband_indicator
            ifns.update({'donchian_channel_hband_indicator': create_fn_c(donchian_channel_hband_indicator)})
        elif k == 'donchian_channel_lband_indicator':
            from ta import donchian_channel_lband_indicator
            ifns.update({'donchian_channel_lband_indicator': create_fn_c(donchian_channel_lband_indicator)})
    return ifns


class Indicator():
    def __init__(self, config):
        """Initialize indicators object."""
        self.ifns = import_and_init(config)
        self.indicators = {}
        self.update_indicators(config)
        if len(self.indicators) == 0:
            raise ValueError('no kwargs provided')

    def update_indicators(self, config):
        """Config file must be read as dict."""
        config_error_handling(config)
        for k, v in config.items():
            for vi in v:
                if k in self.ifns.keys():
                    self.indicators.update({k + '_' + str(vi): self.ifns[k](vi)})
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
