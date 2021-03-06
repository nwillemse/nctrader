from .position import Position


class Portfolio(object):
    def __init__(self, price_handler, cash):
        """
        On creation, the Portfolio object contains no
        positions and all values are "reset" to the initial
        cash, with no PnL - realised or unrealised.

        Note that realised_pnl is the running tally pnl from closed
        positions (closed_pnl), as well as realised_pnl
        from currently open positions.
        """
        self.price_handler = price_handler
        self.init_cash = cash
        self.equity = cash
        self.cur_cash = cash
        self.positions = {}
        self.closed_positions = []
        self.realised_pnl = 0
        self.open_quantity = 0
        self.tickers_info = price_handler.tickers_info

    def _update_portfolio(self):
        """
        Updates the value of all positions that are currently open.
        Value of closed positions is tallied as self.realised_pnl.
        """
        self.unrealised_pnl = 0
        self.equity = self.realised_pnl
        self.equity += self.init_cash
        for ticker in self.positions:
            pt = self.positions[ticker]
            if self.price_handler.istick():
                bid, ask = self.price_handler.get_best_bid_ask(ticker)
            else:
                close_price = self.price_handler.get_last_close(ticker)
                bid = close_price
                ask = close_price
            timestamp = self.price_handler.get_last_timestamp(ticker)
            pt.update_market_value(bid, ask, timestamp)
            self.unrealised_pnl += pt.unrealised_pnl
            self.equity += pt.market_value - pt.cost_basis

    def _add_position(
        self, action, ticker, quantity,
        price, commission, entry_date, entry_name
    ):
        """
        Adds a new Position object to the Portfolio. This
        requires getting the best bid/ask price from the
        price handler in order to calculate a reasonable
        "market value".

        Once the Position is added, the Portfolio values
        are updated.
        """
        if ticker not in self.positions:
            if self.price_handler.istick():
                bid, ask = self.price_handler.get_best_bid_ask(ticker)
            else:
                close_price = self.price_handler.get_last_close(ticker)
                bid = close_price
                ask = close_price

            bpv = self.tickers_info[ticker].big_point_value
            ticker_type = self.tickers_info[ticker].type
            margin = self.tickers_info[ticker].margin
            position = Position(
                action, ticker, ticker_type, margin, quantity, price,
                commission, bid, ask, entry_date, bpv, entry_name
            )
            self.positions[ticker] = position
            self.open_quantity = quantity
            self._update_portfolio()
        else:
            print(
                "Ticker %s is already in the positions list. "
                "Could not add a new position." % ticker
            )

    def _modify_position(
        self, action, ticker,
        quantity, price, commission, name
    ):
        """
        Modifies a current Position object to the Portfolio.
        This requires getting the best bid/ask price from the
        price handler in order to calculate a reasonable
        "market value".

        Once the Position is modified, the Portfolio values
        are updated.
        """
        self.open_quantity = 0
        if ticker in self.positions:
            self.positions[ticker].transact_shares(
                action, quantity, price, commission, name
            )
            if self.price_handler.istick():
                bid, ask = self.price_handler.get_best_bid_ask(ticker)
            else:
                close_price = self.price_handler.get_last_close(ticker)
                bid = close_price
                ask = close_price

            timestamp = self.price_handler.get_last_timestamp(ticker)
            self.positions[ticker].update_market_value(bid, ask, timestamp)

            self.open_quantity += self.positions[ticker].open_quantity
            if self.positions[ticker].open_quantity == 0:
                closed = self.positions.pop(ticker)
                self.realised_pnl += closed.realised_pnl
                self.cur_cash += closed.realised_pnl
                self.closed_positions.append(closed)

            self._update_portfolio()
        else:
            print(
                "Ticker %s not in the current position list. "
                "Could not modify a current position." % ticker
            )

    def transact_position(
        self, action, ticker, quantity, price,
        commission, timestamp, name
    ):
        """
        Handles any new position or modification to
        a current position, by calling the respective
        _add_position and _modify_position methods.

        Hence, this single method will be called by the
        PortfolioHandler to update the Portfolio itself.
        """
        ticker_type = self.tickers_info[ticker].type
        margin = self.tickers_info[ticker].margin
        if ticker_type == 'FUT':
            factor = margin
        else:
            factor = price

        if action == "BOT":
            self.cur_cash -= (quantity * factor)
        elif action == "SLD":
            self.cur_cash += (quantity * factor)

        if ticker not in self.positions:
            self._add_position(
                action, ticker, quantity, price, commission, timestamp, name
            )
        else:
            self._modify_position(
                action, ticker, quantity, price, commission, name
            )

    def get_position(self, ticker):
        """
        Returns the current position for the ticker specified or None
        """
        if ticker in self.positions:
            pt = self.positions[ticker]
            return pt
        else:
            return None

    def get_open_positions(self):
        """
        Returns a list with all the open positions
        """
        open_pos = []
        for ticker, pos in self.positions.items():
            open_pos.append(pos)
        return open_pos
