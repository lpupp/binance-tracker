"""Implement stop loss manually.

Since Binance does not allow take-profit and stop-loss to be implemented
simultaneously, I created a function to monitor price, cancel take-profit,
and implement stop-loss if stop-loss is triggered. The arguments are the same
as those that would be input in the Binance stop-loss fields. This script
monitors the prices in the background and terminates when take-profit or
stop-loss is fulfilled.

cmd:
cd Documents/GitHub/crypyto
python src/stop_loss.py --client_path assets/client.txt --symbol ADA_BTC --p_stop 0.00031 --p_limit 0.0003 --balance 100
"""

import argparse
import datetime as dt

from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *

from utils import notify

parser = argparse.ArgumentParser(description='Implement stop-loss.')

parser.add_argument('--client_path', type=str, default='./assets/client.txt', help='Path to client key txt.')
parser.add_argument('--symbol', type=str, default=None, help='Symbol to stop loss.')
parser.add_argument('--p_stop', type=float, default=None, help='Price to trigger order.')
parser.add_argument('--p_limit', type=float, default=None, help='Price to sell.')
parser.add_argument('--balance', type=str, default=None, help='Balance of coin.')


class StopLoss():
    def __init__(self, args, client):
        self.counter = 0
        self.symbol = args.symbol.upper()
        self.symbol_nm = self.symbol.replace('_', '')
        self.balance = args.balance
        self.p_stop = args.p_stop

        p = '{:.20f}'.format(args.p_limit)
        while p[-1] == '0':
            p = p[:-1]
        self.p_limit = p

        self.client = client

        self.order = client.get_open_orders(symbol=self.symbol_nm)
        assert len(self.order) == 1, 'More than one order on {} \n {}'.format(self.symbol, self.order)

        self.can_sell = True

        self.t0 = None

    def process_message(self, msg):
        """Cancel take-profit and implement stop-loss if stop-loss is triggered."""
        p_current = float(msg['k']['c'])
        if self.counter % 60 == 0:
            print('Current price: {}'.format(p_current))

        # If ticker value fall to or below args.p_stop
        if p_current <= self.p_stop and self.can_sell:
            notify('Stop loss triggered', self.symbol, '')
            self.t0 = dt.datetime.now()
            # Cancel existing sell order
            self.client.cancel_order(symbol=self.symbol_nm,
                                     orderId=self.order[0]['orderId'])
            print('Canceled profit sell order.')

            # Create new sell order at p_limit
            self.client.order_limit_sell(symbol=self.symbol_nm,
                                         quantity=self.balance,
                                         price=self.p_limit)
            print('Made stop loss order.')

            self.order = self.client.get_open_orders(symbol=self.symbol_nm)
            assert len(self.order) <= 1, 'Something failed with stop loss. \n {}'.format(self.order)
            self.can_sell = False

        self.order = self.client.get_open_orders(symbol=self.symbol_nm)
        if len(self.order) == 0:
            if self.t0 is None:
                notify('Order fulfilled otherwise', self.symbol, '')
            else:
                notify('Stop loss processed', self.symbol, '')
                print('Sell order active for {}.'.format(dt.datetime.now() - self.t0))
            self.end_ticker()

        self.counter += 1

    def start_ticker(self):
        """Start connection to ticker."""
        self.bm = BinanceSocketManager(self.client)
        conn_key = self.bm.start_kline_socket(self.symbol_nm,
                                              self.process_message,
                                              interval=KLINE_INTERVAL_1MINUTE)

        self.bm.start()

    def end_ticker(self):
        """Close connection to ticker."""
        self.bm.close()


if __name__ == "__main__":
    global args
    args = parser.parse_args()

    if args.client_path is None:
        raise ValueError('`client_path` not provided.')

    if args.symbol is None or args.p_stop is None or args.p_limit is None:
        raise ValueError('Provide all arguments.')

    client_keys = []
    with open(args.client_path, 'r') as f:
        for line in f:
            client_keys.append(line.rstrip('\n'))

    client = Client(client_keys[0], client_keys[1])

    sl = StopLoss(args, client)
    sl.start_ticker()
