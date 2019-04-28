"""TODO."""
import time
import webbrowser

from utils import notify, get_holding
from signals import eg_condition

from binance.client import Client


class TradingBot():
    """Trading bot.

    TODO(lpupp):
    [ ] Journal trades
    [ ] Sell conditions trigger
    [ ] Import conditions
    [ ] Implement take profit: can_trigger_sell = coin_holding > epsilon
    """
    def __init__(self, symbols, freqs, client, t_sleep=5, log_path=None):
        self.t_notify = dict((k, 0) for k in symbols)
        self.t_sleep = t_sleep
        self.can_trigger_buy = dict((k, True) for k in symbols)
        self.can_trigger_sell = dict((k, False) for k in symbols)
        self.client = client
        self.freqs = freqs

        if log_path is None:
            self.log = {}
        else:
            raise NotImplementedError('Read json.')

        self.buy_price = dict((k, []) for k in symbols)
        self.orders = dict((sym, client.get_open_orders(symbol=sym.replace('_', ''))) for sym in symbols)
        self.holdings = dict((sym.replace('_BTC', ''), get_holding(client, sym)) for sym in symbols)

    def __call__(self, crypto_klines, symbol, verbose):
        """Trading bot call."""
        self.can_trigger_buy[symbol] = time.time() - self.t_notify[symbol] > self.t_sleep * 60
        if self.can_trigger_buy[symbol]:
            print('Buy path: {}.'.format(symbol))
            for freq in self.freqs:
                df = getattr(crypto_klines, 'df_' + freq)

                if eg_condition(df):
                    self.notify(symbol, crypto_klines, notify_cond='eg_condition')
                    notify('eg_condition', '{} {}'.format(symbol, freq), '')

        elif self.can_trigger_sell[symbol]:  # Manually monitor stop loss
            print('Sell path: {}'.format(symbol))
            p = float(df['close'].values.item())
            if p <= self.buy_price[symbol][2]*1.005:
                order = self.sell(symbol, self.buy_price[symbol][2])
                self.update_log(order, freq, df.tail(100))

        self.update_orders(symbol)

    def update_orders(self, symbol):
        orders = self.client.get_open_orders(symbol=symbol.replace('_', ''))
        n_open_0 = len(self.orders[symbol])
        n_open_1 = len(orders)

        if n_open_1 > 1:
            raise ValueError("More than one order on single currency isn't allowed")

        # if n_open_1 > n_open_0:  # New order (add new order)
        #    self.orders[symbol] = orders
        elif n_open_1 < n_open_0:  # Order has been processed
            side = self.orders[symbol]['side']
            p = self.orders[symbol]['price']
            q = self.orders[symbol]['origQty']

            if side == 'BUY':
                order = self.set_take_profit(symbol, p)
                self.orders[symbol] = [order]
                self.can_trigger_sell[symbol] = True
            elif side == 'SELL':
                self.can_trigger_buy[symbol] = True
                self.orders[symbol] = []
                notify('Sell order processed', 'sym:{}; p:{}; q:{}'.format(symbol, p, q), '')
                self.buy_price[symbol] = []
        else:
            pass

    def notify(self, symbol, crypto_klines, notify_cond=''):
        # TODO(lpupp) can i see if the window is still opened?
        # If window is open, don't trigger open_new
        # If window is open, trigger utils.notify
        print('-'*50, '{} condition passed'.format(notify_cond))
        if self.can_trigger_buy[symbol]:
            binance = 'https://www.binance.com/en/trade/pro/' + symbol
            webbrowser.open_new(binance)
        self.can_trigger_buy[symbol] = False
        self.t_notify[symbol] = time.time()

    def update_log(self, order, freq, crypto_klines):
        # TODO(lpupp) log trades
        # (symbol, crypto_klines.df_1T.tail(1).index.values)
        order.update({'freq': freq, 'df': crypto_klines})
        self.log.update(order)

    def buy(self, symbol, freq, price, type='limit', portion=0.5):
        BTC_balance = float(get_holding(self.client, 'BTC'))
        # TODO(lpupp) buy, set stop loss
        # Get upper BB at cross and set buy limits

        q = int(max(float(price) / (BTC_balance * portion), float(price) / 0.2))
        if type == 'limit':
            order = self.client.order_limit_buy(
                symbol=symbol.replace('_', ''),
                quantity=str(q),
                price=price)
            notify('Limit buy order placed', 'sym:{}_{}; q:{}; p{}, '.format(symbol, freq, q, price), '')
        elif type == 'market':
            order = self.client.order_market_buy(
                symbol=symbol.replace('_', ''),
                quantity=str(q))
            notify('Market buy order placed', 'sym:{}_{}; q:{}'.format(symbol, freq, q), '')

        self.orders[symbol].append(order)
        self.can_trigger_buy[symbol] = False
        return order

    def set_take_profit(self, symbol, price):
        # TODO(lpupp) when order filled:
        # TODO(lpupp) call this in KLineTracker in "track order" with "if order_filled:"
        # and with order = client.get_order(symbol='BNBBTC', orderId='orderId')
        q = get_holding(self.client, symbol)
        order = self.client.order_limit_sell(
            symbol=symbol.replace('_', ''),
            quantity=q,
            price=str(float(price)*1.031))
        notify('Take profit order placed', 'sym:{}; q:{}; p{}, '.format(symbol, freq, q, price), '')

        self.update_log(order, None, None)
        return order

    def sell(self, symbol, price):
        # client.get_all_orders(symbol='BNBBTC', limit=10)

        # TODO(lpupp) if all are sold
        orders = self.client.get_open_orders(symbol=symbol)
        result = self.client.cancel_order(
            symbol=symbol,
            orderId=orders[-1]['orderId'])
        self.update_log(result, None, None)

        balance = get_holding(self.client, symbol)
        order = self.client.order_limit_sell(
            symbol=symbol.replace('_', ''),
            quantity=balance,
            price=str(price))
        return order
