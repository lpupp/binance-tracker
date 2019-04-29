# binance-tracker

A tool to help (partially) automate trading on Binance. Interfaces with the
Binance API. Tracks list of cryptocurrencies and notifies you when self-defined
conditions are met. Additional tool to implement stop-loss.

__NOTE__: This implementation is untested. Use at your own risk. Make sure you
educate yourself on the risks of trading before trading with real money.

In its current state, this script is ideal for when you notice a trend
developing but do not continuously want to monitor it. Program the condition
and a notification will alert you and a window will open in your browser when
the condition is triggered.

## Dependencies
* [Python 3.5+](https://www.continuum.io/downloads)
* [python-binance](https://github.com/sammchardy/python-binance)
* [ta](https://github.com/bukosabino/ta)
* [pandas](https://pandas.pydata.org)

## Usage

### 1. Clone the repository
```bash
$ git clone https://github.com/lpupp/binance-tracker.git
$ cd binance-tracker/
```

### 2. Register and connect to Binance
    1. Register on [binance.com](https://www.binance.com/)
    2. Create an [API key](https://support.binance.com/hc/en-us/articles/360002502072-How-to-create-API)
    3. Put key in `assets>>client.txt` ([here](https://github.com/lpupp/binance-tracker/blob/master/assets/client.txt)). The key should be entered one 2 lines in txt file.

__Careful__: if you are going to be making changes to this script and tracking it
on GitHub, make sure not to upload the `client.txt` with your API key in it.

### 3. Select indicators

The current implementation imports all indicators from [ta](https://github.com/bukosabino/ta).

If you to wish use your own, implement them in the `Indicator` class ([here](https://github.com/lpupp/binance-tracker/blob/master/src/indicator.py)).

For example, calculate the width of bollinger bands
```python
def bb_width(self, df, full_df=False):
    """Calculate the width of bollinger bands."""
    df = df.copy()

    bb_u = [e for e in df.columns if 'bb_u' in e]
    bb_l = [e for e in df.columns if 'bb_l' in e]
    df['bb_width'] = df[bb_u[0]] - df[bb_l[0]]

    if full_df:
        return df
    else:
        return df.tail(1)
```
and update the call function accordingly:
```python
def __call__(self, df, full_df=False, d1=False, d2=False, smooth_periods=None):
    ...
    if smooth_periods is not None:
        df = self.get_smooth(df, smooth_periods, full_df)

    df = self.bb_width(df, full_df)
    if full_df:
        return df
    ...
```

### 4. Create buy or sell trigger conditions

Implement all buy or sell signals in the `signals.py` [script](https://github.com/lpupp/binance-tracker/blob/master/src/signals.py)
and import to the `TradingBot` class ([here](https://github.com/lpupp/binance-tracker/blob/master/src/tradingbot.py)).

Currently, only an example condition is implemented. Furthermore, the script
is only configured to notify you when condition is triggered--not to make orders.
```python
def __call__(self, crypto_klines, symbol, verbose):
...
    if eg_condition(df):
        self.notify(symbol, crypto_klines, notify_cond='eg_condition')
        notify('eg_condition', '{} {}'.format(symbol, freq), '')
...
```
That is, it will notify you and open a browser window with the exchange of the
crypto pair that triggered the condition. Note, however, that the candlestick
frequency loaded in the browser may be incorrect (as this can currently not be
set in the url). Reference the notification for the correct frequency.

### 5. Start tracking crypto pairs
```bash
python src/main.py --trading_currencies ETH XRP ADA \
                   --trading_freqs 1T 3T 5T --base_currency BTC \
                   --client_path assets/client.txt
```

`--trading_freqs` can be one of any [pandas frequencies](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases)

## Stop loss function
Additionally, if you are currently in a trade, Binance does not allow you to set
a stop-loss and a take-profit simultaneously. The [stop loss script](https://github.com/lpupp/binance-tracker/blob/master/src/stop_loss.py)
will monitor the price for you and issue a sell order when your stop-loss
condition is triggered.

### Steps:
1. Make trade.
2. Set take-profit order on binance.com.
3. Issue stop-loss with `src/stop_loss.py` script. The arguments correspond to
   those that would be input to create a stop-loss order online.
```bash
python src/stop_loss.py --client_path assets/client.txt --symbol ADA_BTC
                        --p_stop 0.00031 --p_limit 0.0003 --balance 100
```

## Additional documentation
- Official [binance API documentation](https://github.com/binance-exchange/binance-official-api-docs)
