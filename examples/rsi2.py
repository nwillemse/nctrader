#!/usr/bin/env python
"""
RSI2.py

Standard trading system trading the 2-period RSI on SPY

Created on Mon Aug 15 19:20:57 2016

@author: nwillemse
"""
import click
import csv
import pandas as pd
import numpy as np

from datetime import datetime
from os import path, remove
from collections import OrderedDict

from nctrader import settings
from nctrader.compat import queue
from nctrader.price_parser import PriceParser
from nctrader.price_handler.sqlite_bar import SqliteBarPriceHandler
from nctrader.strategy.base import AbstractStrategy
from nctrader.position_sizer.fixed import FixedPositionSizer
from nctrader.risk_manager.example import ExampleRiskManager
from nctrader.portfolio_handler import PortfolioHandler
from nctrader.compliance.example import ExampleCompliance
from nctrader.execution_handler.ib_simulated import IBSimulatedExecutionHandler
from nctrader.statistics.basic import BasicStatistics
from nctrader.statistics.tearsheet import TearsheetStatistics
from nctrader.trading_session.backtest import Backtest
from nctrader.event import (SignalEvent, EventType)


def RSI(series, period=2):
    delta = series.diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    u[u.index[period-1]] = np.mean( u[:period] ) #first value is sum of avg gains
    u = u.drop(u.index[:(period-1)])
    d[d.index[period-1]] = np.mean( d[:period] ) #first value is sum of avg losses
    d = d.drop(d.index[:(period-1)])
    rs = u.ewm(com=period-1, adjust=False).mean() / \
         d.ewm(com=period-1, adjust=False).mean()
    rsi = 100 - 100 / (1 + rs)
    return rsi[-1]


class RSI2Strategy(AbstractStrategy):
    """
    Requires:
     tickers - The list of ticker symbols
     events_queue - A handle to the system events queue
     start_dt - Trading start datetime
     end_dt - Trading end datetime
    """
    def __init__(
        self, config, tickers, events_queue
    ):
        self.config = config
        self.tickers = tickers
        self.events_queue = events_queue
        self.bars = pd.DataFrame(columns=['open', 'high', 'low', 'close'])
        self.sma_length = 200
        self.position = 'OUT'
        self.explore_fname = self._get_explore_filename()
        self.explore_header = True


    def _get_explore_filename(self):
        """
        """
        today = datetime.utcnow().date()
        csv_filename = "explore_" + today.strftime("%Y-%m-%d") + ".csv"
        fname = path.expanduser(path.join(self.config.OUTPUT_DIR, csv_filename))
        try:
            remove(fname)
        except (IOError, OSError):
            print("No exlore files to clean.")
        return fname


    def record_explore(self, info):
        """
        """
        # Write row
        with open(self.explore_fname, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=info.keys())
            if self.explore_header:
                writer.writeheader()
                self.explore_header = False
            writer.writerow(info)


    def calc_trend(self, prices):
        """
        """
        sma0 = np.mean(prices[-self.sma_length:]['close'])
        sma1 = np.mean(prices[-(self.sma_length+1):-1]['close'])
        sma2 = np.mean(prices[-(self.sma_length+2):-2]['close'])
        sma3 = np.mean(prices[-(self.sma_length+3):-3]['close'])

        if sma0 > sma1 and sma1 > sma2 and sma2 > sma3:
            return 1
        else:
            return -1


    def calculate_signals(self, event):

        ticker = self.tickers[0]
        if event.type == EventType.BAR and event.ticker == ticker:

            d = OrderedDict()
            d['timestamp'] = event.time
            d['sig_ticker'] = ticker
            d['sig_close'] = PriceParser.display(event.close_price)
            d['trend'] = None
            d['rsi'] = None
            self.bars.loc[event.time] = (event.open_price, event.high_price,
                event.low_price, event.close_price)

            # Enough bars are present for trading
            if len(self.bars) > 3:

                trend = self.calc_trend(self.bars)
                rsi = RSI(self.bars['close'])
                d['trend'] = trend
                d['rsi'] = rsi

#                print ("Date: %s Ticker: %s Trend: %s RSI: %0.4f" % (
#                    event.time, ticker, trend, rsi)
#                )

                # Process Exit Signals
                if self.position == 'LE' and rsi > 50:
                    signal = SignalEvent(ticker, "SLD")
                    self.events_queue.put(signal)
                    self.position = 'OUT'
                    print "%s Signal:LX %s trend:%s rsi:%0.4f" % (
                        event.time, ticker, trend, rsi)

                if self.position == 'SE' and rsi < 50:
                    signal = SignalEvent(ticker, "BOT")
                    self.events_queue.put(signal)
                    self.position = 'OUT'
                    print "%s Signal:SX %s trend:%s rsi:%0.4f" % (
                        event.time, ticker, trend, rsi)

                # Entry Signals
                if self.position == 'OUT':
                    # LE
                    if rsi < 50:
                        signal = SignalEvent(ticker, "BOT")
                        self.events_queue.put(signal)
                        self.position = 'LE'
                        print "%s Signal:LE %s trend:%s rsi:%0.4f" % (
                            event.time, ticker, trend, rsi)

                    # SE
                    if rsi > 50:
                        signal = SignalEvent(ticker, "SLD")
                        self.events_queue.put(signal)
                        self.position = 'SE'
                        print "%s Signal:SE %s trend:%s rsi:%0.4f" % (
                            event.time, ticker, trend, rsi)
            # Write explore
            d['position'] = self.position
            self.record_explore(d)


def run(config, testing, tickers):

    # Benchmark ticker
    benchmark = None
    bt_start_dt = datetime(2000, 4, 1)
    trd_start_dt = datetime(2000, 4, 1)
    end_dt = datetime(2000, 12, 31)
    #start_dt = datetime(2016, 1, 1)
    #end_dt = datetime(2016, 8, 1)

    # Set up variables needed for backtest
    title = [
        'RSI2',
        path.basename(__file__),
        ','.join(tickers)
    ]
    events_queue = queue.Queue()
    sqlite_db = config.SQLITE_DB
    initial_equity = PriceParser.parse(100000.00)

    # Use Sqlite Daily Price Handler
    price_handler = SqliteBarPriceHandler(
        sqlite_db, events_queue, tickers
    )

    # Use the RSI Strategy
    strategy = RSI2Strategy(config, tickers, events_queue)

    # Use fixed Position Sizer,
    position_sizer = FixedPositionSizer()

    # Use an example Risk Manager,
    risk_manager = ExampleRiskManager()

    # Use the default Portfolio Handler
    portfolio_handler = PortfolioHandler(
        initial_equity, events_queue, price_handler,
        position_sizer, risk_manager
    )

    # Use the ExampleCompliance component
    compliance = ExampleCompliance(config)

    # Use a simulated IB Execution Handler
    execution_handler = IBSimulatedExecutionHandler(
        events_queue, price_handler, compliance
    )

    # Use the default Statistics
#    statistics = BasicStatistics(
#        config, portfolio_handler
#    )
    statistics = TearsheetStatistics(
        config, portfolio_handler, title, benchmark, trd_start_dt, end_dt
    )

    # Set up the backtest
    backtest = Backtest(
        price_handler, strategy, portfolio_handler, execution_handler,
        position_sizer, risk_manager, statistics, initial_equity,
        bt_start_dt, end_dt
    )
    results = backtest.simulate_trading(testing=testing)

    return results


@click.command()
@click.option('--config', '-c', default=settings.DEFAULT_CONFIG_FILENAME, help='Config filename')
@click.option('--tickers', '-t', default='SPY', help='Tickers (use comma)')
@click.option('--testing/--no-testing', default=False, help='Enable testing mode')
def main(config, tickers, testing):
    tickers = tickers.split(",")
    config = settings.from_file(config, testing)
    run(config, testing, tickers)

if __name__ == "__main__":
    main()
