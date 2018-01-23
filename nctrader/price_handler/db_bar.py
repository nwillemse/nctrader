import pandas as pd

from ..price_parser import PriceParser
from .base import AbstractBarPriceHandler
from .db import db_session, init_engine
from .db.models import Asset, DataVendor
from ..event import BarEvent


class DbBarPriceHandler(AbstractBarPriceHandler):
    """
    SqliteBarPriceHandler is designed to read a sqlite3 database
    with daily Open-High-Low-Close-Volume (OHLCV) data for each
    requested financial instrument and stream those to the provided
    events queue as BarEvents.
    """
    def __init__(
        self, db_uri, events_queue, init_tickers=None,
        data_vendor='CSI', bar_size='D'
    ):
        """
        Takes path to sqlite database, the events queue and a possible
        list of initial ticker assets then creates an (optional)
        list of ticker subscriptions and associated prices.
        """
        self.db_uri = db_uri
        self.events_queue = events_queue
        self.bar_size = bar_size
        self.engine = init_engine(db_uri)
        self.data_vendor = db_session.query(DataVendor) \
                                     .filter(DataVendor.name == data_vendor) \
                                     .first()
        self.continue_backtest = True
        self.tickers = {}
        self.tickers_data = {}
        self.tickers_info = {}
        if init_tickers is not None:
            for ticker in init_tickers:
                self.subscribe_ticker(ticker)
        self.bar_stream = self._merge_sort_ticker_data()

    def _load_ticker_price(self, ticker):
        """
        Opens the database containing the ticker data from
        the specified database, converting them into
        them into a pandas DataFrame, stored in a dictionary.
        """
        qry = """SELECT d.timestamp AS date,
                        d.open_price AS open,
                        d.high_price AS high,
                        d.low_price AS low,
                        d.close_price AS close,
                        d.volume AS volume
                   FROM bar_data    d,
                        asset       s,
                        data_vendor dv
                  WHERE s.id = d.asset_id
                    AND dv.id = s.data_vendor_id
                    AND s.ticker = '%s'
                    AND d.bar_size = '%s'
                    AND dv.name = '%s'
        """
        sql_qry = qry % (ticker, self.bar_size, self.data_vendor.name)
        print(sql_qry)
        self.tickers_data[ticker] = pd.read_sql_query(
            sql_qry, self.engine, index_col='date', parse_dates=['date']
        )
        self.tickers_data[ticker]["Ticker"] = ticker

    def _load_ticker_info(self, ticker):
        """
        Opens up the sqlite database, loads the Asset table into a dictionary
        containing all the additional information including big_point_value,
        tick_size, margin
        """
        asset_info = db_session.query(Asset) \
                               .filter(Asset.ticker == ticker) \
                               .filter(Asset.data_vendor == self.data_vendor) \
                               .one()
        asset_info.margin = PriceParser.parse(asset_info.margin)
        return asset_info

    def _merge_sort_ticker_data(self):
        """
        Concatenates all of the separate equities DataFrames
        into a single DataFrame that is time ordered, allowing tick
        data events to be added to the queue in a chronological fashion.

        Note that this is an idealised situation, utilised solely for
        backtesting. In live trading ticks may arrive "out of order".
        """
        return pd.concat(
            self.tickers_data.values()
        ).sort_index().iterrows()

    def subscribe_ticker(self, ticker):
        """
        Subscribes the price handler to a new ticker symbol.
        """
        if ticker not in self.tickers:
            try:
                self._load_ticker_price(ticker)
                dft = self.tickers_data[ticker]
                row0 = dft.iloc[0]

                close = PriceParser.parse(row0["close"])

                ticker_prices = {
                    "close": close,
                    "timestamp": dft.index[0]
                }
                self.tickers[ticker] = ticker_prices
            except OSError:
                print(
                    "Could not subscribe ticker %s "
                    "as no data was found in database..." % ticker
                )
        else:
            print(
                "Could not subscribe ticker %s "
                "as is already subscribed." % ticker
            )

        if ticker not in self.tickers_info:
            try:
                ticker_info = self._load_ticker_info(ticker)
                self.tickers_info[ticker] = ticker_info
            except OSError:
                print(
                    "Could not load ticker info %s as no data"
                    "was found in database table Asset..." % ticker
                )

    def _create_event(self, index, period, ticker, row):
        """
        Obtain all elements of the bar from a row of dataframe
        and return a BarEvent
        """
        open_price = PriceParser.parse(row["open"])
        high_price = PriceParser.parse(row["high"])
        low_price = PriceParser.parse(row["low"])
        close_price = PriceParser.parse(row["close"])
        volume = int(row["volume"])
        bev = BarEvent(
            ticker, index, period, open_price, high_price,
            low_price, close_price, volume
        )
        return bev

    def stream_next(self):
        """
        Place the next BarEvent onto the event queue.
        """
        try:
            index, row = next(self.bar_stream)
        except StopIteration:
            self.continue_backtest = False
            return
        # Obtain all elements of the bar from the dataframe
        ticker = row["Ticker"]
        period = self._period_map[self.bar_size]
        # Create the tick event for the queue
        bev = self._create_event(index, period, ticker, row)
        # Store event
        self._store_event(bev)
        # Send event to queue
        self.events_queue.put(bev)
