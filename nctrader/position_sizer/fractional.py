import numpy as np
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
        """
        spu = []
        ttl = 0
        for i in range(1, self.units_per_position):
            spu_tmp = int(np.ceil((tot_shares - ttl) / float(self.units_per_position)))
            spu.append(spu_tmp)
            ttl += spu_tmp
        # now append the last share unit
        spu.append(int(max(tot_shares - ttl,0)))
        spu.sort(reverse=True)
        return spu[unit-1]


    def size_order(self, portfolio, initial_order):
        """
        This FranctionalPositionSizer object modifies the quantity base on
        available equity times fraction.
        """
        if initial_order is None:
            return
        
        ticker_info = portfolio.price_handler.tickers_info[initial_order.ticker]
        last_price = portfolio.price_handler.get_last_close(initial_order.ticker)

        # only size the order if quantity is zero - entry order
        if initial_order.quantity == 0:
            dvar = initial_order.fraction if self.use_dvar else self.fraction
            if ticker_info.type == 'STK':
                tot_shares = int(portfolio.equity * dvar / last_price)
            elif ticker_info.type == 'FUT':
                tot_shares = int(portfolio.equity * dvar / self.dollar_per_contract)
            else:
                print "Ticker type not handled for", ticker_info
        
            initial_order.quantity = self._unit_shares(
                    tot_shares, initial_order.unit
            )

        return initial_order
