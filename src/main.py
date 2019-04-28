"""TODO.

TODO MASTER (lpupp):
[ ] How to calculate indicators dynamically with freq != 1T
[ ] How to update df for freq != 1T
[ ] How to notify when signal is triggered
[ ] How to trigger signal
[ ] How to handel data?
[ ] More currency pairs (easy)

TODO LR:
[ ] Docstrings
[ ] Remove main.py from github history
[ ] First all data should be loaded and saved

cmd:
cd Documents/GitHub/crypyto
python src/main.py --client_path assets/client.txt
"""
import sys
sys.path.append('./src')

import argparse

from binance.client import Client

from klinetracker import KLineTracker
from cryptoklines import CryptoKlines
from indicator import Indicator
from tradingbot import TradingBot

parser = argparse.ArgumentParser(description='Binance Tracker')

parser.add_argument('--base_currency', type=str, default=None, help='BTC|USDT.')
parser.add_argument('--load_path', type=str, default=None, help='Path to csv data file(s).')
parser.add_argument('--client_path', type=str, default=None, help='Path to client key txt.')


def main(args, client):
    """TODO."""
    all_symbols = [e['symbol'] for e in client.get_all_tickers()]
    [e for e in all_symbols if e[-3:] == 'BTC']

    symbols = ['ADA', 'BAT', 'BCHABC']
    symbols = ['{}_{}'.format(sym, args.base_currency) for sym in symbols]
    symbols = [sym for sym in symbols if sym.replace('_', '') in all_symbols]
    print('Tracking {}'.format(symbols))

    freqs = ['1T', '3T', '5T', '15T', '30T', '1H', '2H', '4H']
    print('Initializing trading bot')
    bot = TradingBot(symbols, freqs, client, t_sleep=15)

    print('Initializing indicator')
    indicator = Indicator(ema=[7, 25, 99],
                          l_bb=[25], u_bb=[25],
                          percent_k=[14], percent_d=[14])

    CK, KT = {}, {}
    for sym in symbols:
        print(sym)
        CK[sym] = CryptoKlines(sym, indicator, client,
                               start_time='10 days ago UTC',
                               load_path=args.load_path, verbose=0)
        KT[sym] = KLineTracker(symbol=sym,
                               indicator=indicator,
                               df_klines=CK[sym],
                               bot=bot,
                               client=client, verbose=0)
    for sym in symbols:
        KT[sym].start_ticker(client)


if __name__ == "__main__":
    global args
    args = parser.parse_args()
    print('-------------------------------------------------------------')
    print('* - * - * - * - * - * - * - * - * - * - * - * - * - * - * - *')
    print('-------------------------------------------------------------')

    if args.client_path is None:
        raise ValueError('`client_path` not provided.')

    client_keys = []
    with open(args.client_path, 'r') as f:
        for line in f:
            client_keys.append(line.rstrip('\n'))

    client = Client(client_keys[0], client_keys[1])

    main(args, client)
