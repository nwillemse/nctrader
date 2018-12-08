from __future__ import print_function

from enum import Enum


EventType = Enum("EventType", "TICK BAR SIGNAL ORDER FILL TRADE")


class Event(object):
    """
    Event is base class providing an interface for all subsequent
    (inherited) events, that will trigger further events in the
    trading infrastructure.
    """
    @property
    def typename(self):
        return self.type.name


class TickEvent(Event):
    """
    Handles the event of receiving a new market update tick,
    which is defined as a ticker symbol and associated best
    bid and ask from the top of the order book.
    """
    def __init__(self, ticker, time, bid, ask):
        """
        Initialises the TickEvent.

        Parameters:
        ticker - The ticker symbol, e.g. 'GOOG'.
        time - The timestamp of the tick
        bid - The best bid price at the time of the tick.
        ask - The best ask price at the time of the tick.
        """
        self.type = EventType.TICK
        self.ticker = ticker
        self.time = time
        self.bid = bid
        self.ask = ask
        self.priority = 100

    def __str__(self):
        return "Type: %s, Ticker: %s, Time: %s, Bid: %s, Ask: %s" % (
            str(self.type), str(self.ticker),
            str(self.time), str(self.bid), str(self.ask)
        )

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        return (self.priority < other.priority)

    def __eq__(self, other):
        return (self.priority == other.priority)


class BarEvent(Event):
    """
    Handles the event of receiving a new market
    open-high-low-close-volume bar, as would be generated
    via common data providers such as Yahoo Finance.
    """
    def __init__(
        self, ticker, time, period,
        open_price, high_price, low_price,
        close_price, volume, adj_close_price=None
    ):
        """
        Initialises the BarEvent.

        Parameters:
        ticker - The ticker symbol, e.g. 'GOOG'.
        time - The timestamp of the bar
        period - The time period covered by the bar in seconds
        open_price - The unadjusted opening price of the bar
        high_price - The unadjusted high price of the bar
        low_price - The unadjusted low price of the bar
        close_price - The unadjusted close price of the bar
        volume - The volume of trading within the bar
        adj_close_price - The vendor adjusted closing price
            (e.g. back-adjustment) of the bar

        Note: It is not advised to use 'open', 'close' instead
        of 'open_price', 'close_price' as 'open' is a reserved
        word in Python.
        """
        self.type = EventType.BAR
        self.ticker = ticker
        self.time = time
        self.period = period
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.adj_close_price = adj_close_price
        self.period_readable = self._readable_period()
        self.priority = 100

    def _readable_period(self):
        """
        Creates a human-readable period from the number
        of seconds specified for 'period'.

        For instance, converts:
        * 1 -> '1sec'
        * 5 -> '5secs'
        * 60 -> '1min'
        * 300 -> '5min'

        If no period is found in the lookup table, the human
        readable period is simply passed through from period,
        in seconds.
        """
        lut = {
            1: "1sec",
            5: "5sec",
            10: "10sec",
            15: "15sec",
            30: "30sec",
            60: "1min",
            300: "5min",
            600: "10min",
            900: "15min",
            1800: "30min",
            3600: "1hr",
            86400: "1day",
            604800: "1wk"
        }
        if self.period in lut:
            return lut[self.period]
        else:
            return "%ssec" % str(self.period)

    def __str__(self):
        format_str = "Type: %s, Ticker: %s, Time: %s, Period: %s, " \
            "Open: %s, High: %s, Low: %s, Close: %s, " \
            "Adj Close: %s, Volume: %s" % (
                str(self.type), str(self.ticker), str(self.time),
                str(self.period_readable), str(self.open_price),
                str(self.high_price), str(self.low_price),
                str(self.close_price), str(self.adj_close_price),
                str(self.volume)
            )
        return format_str

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        return (self.priority < other.priority)

    def __eq__(self, other):
        return (self.priority == other.priority)


class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """
    def __init__(
            self, ticker, action, suggested_quantity=None,
            fraction=0.0, name=None, unit=1, price=None,
            commission=None, timestamp=None
    ):
        """
        Initialises the SignalEvent.

        Parameters:
        ticker - The ticker symbol, e.g. 'GOOG'.
        action - 'BOT'  go long
                 'SLD'  go short
                 'XIT' close the trade out completely
        suggested_quantity - Optional positively valued integer
            representing a suggested absolute quantity of units
            of an asset to transact in, which is used by the
            PositionSizer and RiskManager.
        fraction - % of equity to use for position sizing (optional)
        name - entry or exit name to tie the position to
        unit - the unit number when scaling into position, i.e 1, 2, or 3.
               This is used during position sizing.
        """
        self.type = EventType.SIGNAL
        self.ticker = ticker
        self.action = action
        self.suggested_quantity = suggested_quantity
        self.fraction = fraction
        self.name = name
        self.unit = unit
        self.price = price
        self.commission = commission
        self.timestamp = timestamp
        self.priority = 200

    def __str__(self):
        return "%s ticker:%s action:%s quantity:%s fraction:%.2f%% name:%s unit:%s" % (
            self.type, self.ticker, self.action, self.suggested_quantity,
            self.fraction, self.name, self.unit
        )

    def __lt__(self, other):
        return (self.priority < other.priority)

    def __eq__(self, other):
        return (self.priority == other.priority)


class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system.
    The order contains a ticker (e.g. GOOG), action (BOT or SLD)
    and quantity.
    """
    def __init__(
            self, ticker, action, quantity, name=None,
            price=None, commission=None, timestamp=None
    ):
        """
        Initialises the OrderEvent.

        Parameters:
        ticker - The ticker symbol, e.g. 'GOOG'.
        action - 'BOT' (for long) or 'SLD' (for short).
        quantity - The quantity of shares to transact.
        name - entry or exit name to tie to position
        """
        self.type = EventType.ORDER
        self.ticker = ticker
        self.action = action
        self.quantity = quantity
        self.name = name
        self.price = price
        self.commission = commission
        self.timestamp = timestamp
        self.priority = 300

    def print_order(self):
        """
        Outputs the values within the OrderEvent.
        """
        print(
            "Order: Ticker=%s, Action=%s, Quantity=%s Name=%s Price=%.2f Commission=%.2f" % (
                self.ticker, self.action, self.quantity, self.name, self.price, self.commission
            )
        )

    def __str__(self):
        return "%s ticker:%s action:%s quantity:%s name=%s price=%.2f commission=%.2f" % (
            self.type, self.ticker, self.action, self.quantity, self.name, self.price, self.commission
        )

    def __lt__(self, other):
        return (self.priority < other.priority)

    def __eq__(self, other):
        return (self.priority == other.priority)


class FillEvent(Event):
    """
    Encapsulates the notion of a filled order, as returned
    from a brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores
    the commission of the trade from the brokerage.

    TODO: Currently does not support filling positions at
    different prices. This will be simulated by averaging
    the cost.
    """

    def __init__(
        self, timestamp, ticker,
        action, quantity,
        exchange, price,
        commission, name
    ):
        """
        Initialises the FillEvent object.

        timestamp - The timestamp when the order was filled.
        ticker - The ticker symbol, e.g. 'GOOG'.
        action - 'BOT' (for long) or 'SLD' (for short).
        quantity - The filled quantity.
        exchange - The exchange where the order was filled.
        price - The price at which the trade was filled
        commission - The brokerage commission for carrying out the trade.
        name - entry or exit name for the position
        """
        self.type = EventType.FILL
        self.timestamp = timestamp
        self.ticker = ticker
        self.action = action
        self.quantity = quantity
        self.exchange = exchange
        self.price = price
        self.commission = commission
        self.name = name
        self.priority = 400

    def __str__(self):
        return "%s ticker:%s timestamp:%s action:%s quantity:%s exchange:%s price:%s commission:%s name:%s" % (
            str(self.type), str(self.ticker), str(self.timestamp),
            str(self.action), str(self.quantity), str(self.action),
            str(self.price), str(self.commission), self.name
        )

    def __lt__(self, other):
        return (self.priority < other.priority)

    def __eq__(self, other):
        return (self.priority == other.priority)
