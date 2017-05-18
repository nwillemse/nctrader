from .base import AbstractPositionSizer


class FractionalPositionSizer(AbstractPositionSizer):
    def __init__(
            self, fraction=1.0, use_dvar=False,
            dollar_per_contract=0.0, units_per_position=1
    ):
        self.fraction = fraction
        self.use_dvar = use_dvar
        self.dollar_per_contract = dollar_per_contract
        self.units_per_position = units_per_position

    def _unit_shares(self, tot_shares, unit):
        """
        Calculates the number of shares for the next unit.  Based on
        the total shares for the position and the number of units
        taken per position.
        """
        result = []
        for i in range(self.units_per_position):
            result.append(tot_shares / self.units_per_position)
        remaining = tot_shares % self.units_per_position
        for i in range(remaining):
            result[i] += 1
        return result[unit-1]

    def size_order(self, portfolio, initial_order):
        """
        This FractionalPositionSizer object modifies the quantity base on
        available equity times fraction.
        """
        if initial_order is None:
            return
        
        ticker_info = portfolio.price_handler.tickers_info[initial_order.ticker]
        last_price = portfolio.price_handler.get_last_close(initial_order.ticker)
        tot_shares = 0

        # only size the order if quantity is zero - entry order
        if initial_order.quantity == 0:
            dvar = initial_order.fraction if self.use_dvar else self.fraction
            if ticker_info.type == 'STK':
                tot_shares = int(portfolio.equity * dvar / last_price)
            elif ticker_info.type == 'FUT':
                tot_shares = int(portfolio.equity * dvar / self.dollar_per_contract)
            else:
                print("Ticker type not handled for", ticker_info)
        
            initial_order.quantity = self._unit_shares(
                    tot_shares, initial_order.unit
            )

        return initial_order
