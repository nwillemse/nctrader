class SuggestedOrder(object):
    """
    A SuggestedOrder object is generated by the PortfolioHandler
    to be sent to the PositionSizer object and subsequently the
    RiskManager object. Creating a separate object type for
    suggested orders and final orders (OrderEvent objects) ensures
    that a suggested order is never transacted unless it has been
    scrutinised by the position sizing and risk management layers.
    """
    def __init__(
        self, ticker, action, quantity=0, fraction=0.0, name=None, unit=1,
        price=None, commission=None, timestamp=None
    ):
        """
        Initialises the SuggestedOrder. The quantity defaults
        to zero as the PortfolioHandler creates these objects
        prior to any position sizing.

        The PositionSizer object will "fill in" the correct
        value prior to sending the SuggestedOrder to the
        RiskManager.

        Parameters:
        ticker - The ticker symbol, e.g. 'GOOG'.
        action - 'BOT' (for long) or 'SLD' (for short).
        quantity - The quantity of shares to transact.
        name - entry or exit name for the position
        unit - number of unit this signal is for.  Used during scaling in.
        """
        self.ticker = ticker
        self.action = action
        self.quantity = quantity
        self.fraction = fraction
        self.name = name
        self.unit = unit
        self.price = price
        self.commission = commission
        self.timestamp = timestamp

    def __str__(self):
        return "SuggestedOrder: ticker=%s action=%s quantity=%s fraction=%.2f%% name=%s unit=%s price=%.2f comm=%.2f" % \
            (self.ticker, self.action, self.quantity, self.fraction, self.name, self.unit, self.price, self.commission)
