from __future__ import division

import itertools
from numpy import sign
from collections import OrderedDict

from .price_parser import PriceParser


class Position(object):

    newid = itertools.count(start=1).next

    def __init__(
        self, action, ticker, init_quantity,
        init_price, init_commission,
        bid, ask, entry_date, bpv=1
    ):
        """
        Set up the initial "account" of the Position to be
        zero for most items, with the exception of the initial
        purchase/sale.

        Then calculate the initial values and finally update the
        market value of the transaction.
        """
        self.position_id = Position.newid()
        self.action = action
        self.ticker = ticker
        self.quantity = init_quantity
        self.init_price = init_price
        self.init_commission = init_commission
        self.bpv = bpv

        self.realised_pnl = 0
        self.unrealised_pnl = 0

        self.buys = 0
        self.sells = 0
        self.avg_bot = 0
        self.avg_sld = 0
        self.total_bot = 0
        self.total_sld = 0
        self.comm_bot = 0
        self.comm_sld = 0
        self.total_commission = 0
        
        self.entry_date = entry_date
        self.exit_date = None
        self.trade_pct = 0.0
        
        self._calculate_initial_value()
        self.update_market_value(bid, ask, entry_date)

    def _calculate_initial_value(self):
        """
        Depending upon whether the action was a buy or sell ("BOT"
        or "SLD") calculate the average bought cost, the total bought
        cost, the average price and the cost basis.

        Finally, calculate the net total with and without commission.
        """
        if self.action == "BOT":
            self.buys = self.quantity
            self.avg_bot = self.init_price
            self.total_bot = self.buys * self.avg_bot * self.bpv
            self.comm_bot = self.init_commission
            self.avg_price = (self.total_bot + self.comm_bot) // self.quantity // self.bpv
            self.cost_basis = self.quantity * self.avg_price * self.bpv
        else:  # action == "SLD"
            self.sells = self.quantity
            self.avg_sld = self.init_price
            self.total_sld = self.sells * self.avg_sld * self.bpv
            self.comm_sld = self.init_commission
            self.avg_price = (self.total_sld - self.comm_sld) // self.quantity // self.bpv
            self.cost_basis = -self.quantity * self.avg_price * self.bpv
        self.net = self.buys - self.sells
        self.net_total = (self.total_bot - self.total_sld) * sign(self.net)
        self.total_commission = self.comm_bot + self.comm_sld
        self.net_incl_comm = self.net_total - self.total_commission

    def update_market_value(self, bid, ask, timestamp):
        """
        The market value is tricky to calculate as we only have
        access to the top of the order book through Interactive
        Brokers, which means that the true redemption price is
        unknown until executed.

        However, it can be estimated via the mid-price of the
        bid-ask spread. Once the market value is calculated it
        allows calculation of the unrealised and realised profit
        and loss of any transactions.
        """
        midpoint = (bid + ask) // 2
        self.market_value = self.quantity * midpoint * sign(self.net) * self.bpv
        self.unrealised_pnl = (self.market_value - self.cost_basis)
        self.exit_date = timestamp

    def transact_shares(self, action, quantity, price, commission):
        """
        Calculates the adjustments to the Position that occur
        once new shares are bought and sold.

        Takes care to update the average bought/sold, total
        bought/sold, the cost basis and PnL calculations,
        as carried out through Interactive Brokers TWS.
        """
        #print action, quantity, price, commission
        # Adjust total bought and sold
        if action == "BOT":
            self.comm_bot += commission
            self.avg_bot = (self.avg_bot * self.buys + price * quantity) // (self.buys + quantity)
            self.buys += quantity
            self.total_bot = self.buys * self.avg_bot * self.bpv
            if self.action != "SLD":
                self.avg_price = (self.total_bot + self.comm_bot) // self.buys // self.bpv
            else:
                self.realised_pnl += ((price * quantity - self.avg_sld * quantity) * self.bpv * 
                    sign(self.net) - int(quantity / self.sells * self.comm_sld + commission)
                )
                self.trade_pct = -1 * (self.avg_bot / float(self.avg_sld) - 1)
                

        # action == "SLD"
        else:
            self.comm_sld += commission
            self.avg_sld = (self.avg_sld * self.sells + price * quantity) // (self.sells + quantity)
            self.sells += quantity
            self.total_sld = self.sells * self.avg_sld * self.bpv
            if self.action != "BOT":
                self.avg_price = (self.total_sld - self.comm_sld) // self.sells // self.bpv
            else:
                self.realised_pnl += ((price * quantity - self.avg_bot * quantity) * self.bpv *
                    sign(self.net) - int(quantity / self.buys * self.comm_bot + commission)
                )
                self.trade_pct = self.avg_sld / float(self.avg_bot) - 1

        # Adjust net values, including commissions
        self.net = self.buys - self.sells
        self.quantity = self.net * sign(self.net)
        self.net_total = self.total_sld - self.total_bot
        self.total_commission = self.comm_bot + self.comm_sld
        self.net_incl_comm = self.net_total - self.total_commission

        # Adjust average price and cost basis
        self.cost_basis = self.quantity * self.avg_price * self.bpv * sign(self.net)
        
        
    def __str__(self):
        return "Position[%s]: ticker=%s action=%s entry_date=%s exit_date=%s quantity=%s buys=%s sells=%s net=%s avg_bot=%0.4f avg_sld=%0.4f total_bot=%0.2f total_sld=%0.2f comm_bot=%0.2f comm_sld=%0.2f total_commission=%0.4f avg_price=%0.4f cost_basis=%0.4f market_value=%0.4f realised_pnl=%0.2f unrealised_pnl=%0.2f trade_pct=%0.2f" % \
            (self.position_id, self.ticker, self.action, self.entry_date,
             self.exit_date, self.quantity, self.buys, self.sells, self.net,
             PriceParser.display(self.avg_bot, 4), PriceParser.display(self.avg_sld, 4),
             PriceParser.display(self.total_bot), PriceParser.display(self.total_sld),
             PriceParser.display(self.comm_bot, 4), PriceParser.display(self.comm_sld, 4),
             PriceParser.display(self.total_commission, 4), PriceParser.display(self.avg_price, 4),
             PriceParser.display(self.cost_basis, 4), PriceParser.display(self.market_value, 4),
             PriceParser.display(self.realised_pnl), PriceParser.display(self.unrealised_pnl),
             self.trade_pct
            )

    def __dict__(self):
        od = OrderedDict()
        od['position_id'] = self.position_id
        od['ticker'] = self.ticker
        od['action'] = self.action
        od['quantity'] = self.quantity
        od['buys'] = self.buys
        od['sells'] = self.sells
        od['entry_date'] = self.entry_date
        od['exit_date'] = self.exit_date
        od['avg_price'] = PriceParser.display(self.avg_price, 5)
        od['net'] = PriceParser.display(self.net, 5)
        od['net_incl_comm'] = PriceParser.display(self.net_incl_comm, 5)
        od['net_total'] = PriceParser.display(self.net_total, 5)
        od['avg_bot'] = PriceParser.display(self.avg_bot, 5)
        od['avg_sld'] = PriceParser.display(self.avg_sld, 5)
        od['total_bot'] = PriceParser.display(self.total_bot)
        od['total_sld'] = PriceParser.display(self.total_sld)
        od['total_commission'] = PriceParser.display(self.total_commission, 5)
        od['cost_basis'] = self.cost_basis
        od['market_value'] = PriceParser.display(self.market_value)
        od['unrealised_pnl'] = PriceParser.display(self.unrealised_pnl)
        od['realised_pnl'] = PriceParser.display(self.realised_pnl)
        od['trade_pct'] = self.trade_pct
        return od
