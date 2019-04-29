"""Main.

TODO LR:
[ ] Docstrings
[ ] Remove main.py from github history
[ ] First all data should be loaded and saved

cmd:
cd binance-tracker/
python src/main.py --client_path assets/client.txt
"""
import sys
sys.path.append('./src')

import argparse

from binance.client import Client

from utils import get_config
from klinetracker import KLineTracker
from cryptoklines import CryptoKlines
from indicator import Indicator
from tradingbot import TradingBot

parser = argparse.ArgumentParser(description='Binance Tracker')

parser.add_argument('--trading_currencies', nargs='+', default=['ETH', 'XRP'], help='List of currencies. Need to be traded with base_currency.')
parser.add_argument('--trading_freqs', nargs='+', default=['1T', '3T', '5T', '15T', '30T', '1H', '2H', '4H'], help='List of frequencies to track.')
parser.add_argument('--base_currency', type=str, default='BTC', help='BTC|USDT.')
parser.add_argument('--load_path', type=str, default=None, help='Path to csv data file(s).')
parser.add_argument('--client_path', type=str, default=None, help='Path to client key txt.')

parser.add_argument('--config', type=str, default='configs/indicators.yaml', help='Path to the config file.')

def main(args, client):
    """Track cryptocurrency pairs."""
    all_symbols = [e['symbol'] for e in client.get_all_tickers()]
    [e for e in all_symbols if e[-3:] == 'BTC']

    symbols = [e.upper() for e in args.trading_currencies]
    symbols = ['{}_{}'.format(sym, args.base_currency) for sym in symbols]
    symbols = [sym for sym in symbols if sym.replace('_', '') in all_symbols]
    print('Tracking {}'.format(symbols))

    freqs = args.trading_freqs
    print('Initializing trading bot')
    bot = TradingBot(symbols, freqs, client, t_sleep=15)

    print('Initializing indicator')
    config = get_config(args.config)
    indicator = Indicator(config)

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
