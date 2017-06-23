from __future__ import division

from collections import OrderedDict

from .price_parser import PriceParser


class Position(object):
    pos_id = 0

    def __init__(
            self, action, ticker, init_quantity,
            init_price, init_commission, bid, ask, entry_date,
            mul=1, entry_name=None
    ):
        """
        Set up the initial "account" of the Position to be
        zero for most items, with the exception of the initial
        purchase/sale.

        Then calculate the initial values and finally update the
        market value of the transaction.
        """
        Position.pos_id += 1
        self.id = Position.pos_id
        self.action = action
        self.ticker = ticker
        self.quantity = init_quantity
        self.open_quantity = init_quantity
        self.mul = mul
        self.entry_name = entry_name
        self.exit_name = None

        self.bots = []
        self.solds = []

        self.realised_pnl = 0
        self.unrealised_pnl = 0

        self.entry_date = entry_date
        self.exit_date = None
        self.exit_price = 0
        self.cur_timestamp = entry_date
        self.trade_ret = 0
        self.time_in_pos = 0

        self._calculate_initial_value(init_price, init_commission)
        #self.update_market_value(bid, ask, entry_date)
        self.market_value = 0

    def _calculate_initial_value(self, init_price, init_commission):
        """
        Depending upon whether the action was a buy or sell ("BOT"
        or "SLD") calculate the average bought cost, the total bought
        cost, the average price and the cost basis.
        """
        trade = {'quantity': self.quantity,
                 'remaining_qty': self.quantity,
                 'price': init_price,
                 'comm': init_commission
                }
        if self.action == "BOT":
            self.cost_basis = self.quantity * init_price * self.mul + init_commission
            trade['init_cost'] = abs(self.cost_basis)
            self.bots.append(trade)
        else:  # action == "SLD"
            self.cost_basis = -self.quantity * init_price * self.mul + init_commission
            trade['init_cost'] = abs(self.cost_basis)
            self.solds.append(trade)

        self.entry_price = abs(self.cost_basis) / self.quantity / self.mul
        self.total_commission = init_commission

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
        mv = 0
        if self.action == 'BOT':
            for p in self.bots: mv += p['remaining_qty'] * bid
        else:
            for p in self.solds: mv -= p['remaining_qty'] * ask

        self.market_value = mv * self.mul
        self.unrealised_pnl = (self.market_value - self.cost_basis)
        self.exit_date = timestamp
        if self.cur_timestamp != timestamp:
            self.time_in_pos += 1
            self.cur_timestamp = timestamp

    def _update_position(self):
        """
        Update various attributes of the position after changes
        to position was transacted
        """
        bot, sld = 0, 0
        b_qty, s_qty = 0, 0
        b_oqty, s_oqty = 0, 0
        b_cb, s_cb = 0, 0

        for p in self.bots:
            b_cb += p['remaining_qty'] * p['price'] * self.mul \
                + p['remaining_qty'] / p['quantity'] * p['comm']
            bot += p['init_cost']
            b_qty += p['quantity']
            b_oqty += p['remaining_qty']

        for p in self.solds:
            s_cb -= p['remaining_qty'] * p['price'] * self.mul \
                - p['remaining_qty'] / p['quantity'] * p['comm']
            sld += p['init_cost']
            s_qty += p['quantity']
            s_oqty += p['remaining_qty']

        if self.action == 'BOT':
            self.quantity = b_qty
            self.entry_price = bot / b_qty / self.mul
            self.exit_price = 0 if s_qty == 0 else (sld / s_qty / self.mul)
            self.cost_basis = int(b_cb)
            self.open_quantity= b_oqty
        else:
            self.quantity = s_qty
            self.entry_price = sld / s_qty / self.mul
            self.exit_price = 0 if b_qty == 0 else (bot / b_qty / self.mul)
            self.cost_basis = int(s_cb)
            self.open_quantity= s_oqty

        self.trade_ret = 0 if self.exit_price == 0 else self.exit_price / self.entry_price - 1

    def transact_shares(self, action, quantity, price, commission, name=None):
        """
        Calculates the adjustments to the Position that occur
        once new shares are bought and sold.

        Takes care to update the average bought/sold, total
        bought/sold, the cost basis and PnL calculations,
        as carried out through Interactive Brokers TWS.
        """
        trade = {'quantity': quantity,
                 'remaining_qty': quantity,
                 'price': price,
                 'comm': commission
                }
        if action == "BOT":
            trade['init_cost'] = abs(quantity * price * self.mul + commission)
            self.bots.append(trade)
        else: # action == "SLD"
            trade['init_cost'] = abs(-1 * quantity * price * self.mul + commission)
            self.solds.append(trade)

        remaining_qty = quantity
        rpnl = 0
        finished = False
        if self.action == "BOT" and action == "SLD":
            # sell some of long position
            for i in range(len(self.bots)):
                q = self.bots[i]['quantity']
                qty = self.bots[i]['remaining_qty']
                e_price = self.bots[i]['price']
                e_comm = self.bots[i]['comm']
                if qty < remaining_qty:
                    rpnl += (price - e_price) * qty * self.mul \
                        - (qty / q * e_comm)
                    remaining_qty -= qty
                    qty = 0
                elif qty == remaining_qty:
                    rpnl += (price - e_price) * qty * self.mul \
                        - (qty / q * e_comm) - commission
                    remaining_qty -= qty
                    qty = 0
                    finished = True
                else:
                    rpnl += (price - e_price) * remaining_qty * self.mul \
                        - (remaining_qty / q * e_comm) - commission
                    qty -= remaining_qty
                    remaining_qty = 0
                    finished = True

                self.bots[i]['remaining_qty'] = qty
                if finished: break

        elif self.action == "SLD" and action == "BOT":
            # buy back some of short position
            for i in range(len(self.solds)):
                q = self.solds[i]['quantity']
                qty = self.solds[i]['remaining_qty']
                e_price = self.solds[i]['price']
                e_comm = self.solds[i]['comm']
                if qty < remaining_qty:
                    rpnl += (e_price - price) * qty * self.mul \
                        - (qty / q * e_comm)
                    remaining_qty -= qty
                    qty = 0
                elif qty == remaining_qty:
                    rpnl += (e_price - price) * qty * self.mul \
                        - (qty / q * e_comm) - commission
                    remaining_qty -= qty
                    qty = 0
                    finished = True
                else:
                    rpnl += (e_price - price) * remaining_qty * self.mul \
                        - (remaining_qty / q * e_comm) - commission
                    qty -= remaining_qty
                    remaining_qty = 0
                    finished = True

                self.solds[i]['remaining_qty'] = qty
                if finished: break

        self.realised_pnl += int(rpnl)

        self._update_position()
        self.total_commission += commission

    def __str__(self):
        out = "position[{}] ticker[{}] action[{}] quantity[{}] open_quantity[{}] " \
            + "entry_date[{}] entry_price[{}] entry_name[{}] exit_date[{}] " \
            + "exit_price[{}] exit_name[{}] total_comm[{}] unrealised_pnl[{}] " \
            + "realised_pnl[{}] trade_ret[{}] time_in_pos[{}] " \
            + "cost_basis[{}] market_value[{}]"
        return out.format(
            self.id, self.ticker, self.action, self.quantity, self.open_quantity,
            self.entry_date, PriceParser.display(self.entry_price, 5), self.entry_name, self.exit_date,
            PriceParser.display(self.exit_price, 5), self.exit_name, PriceParser.display(self.total_commission, 5), PriceParser.display(self.unrealised_pnl, 2),
            PriceParser.display(self.realised_pnl, 2), self.trade_ret, self.time_in_pos,
            PriceParser.display(self.cost_basis, 5), PriceParser.display(self.market_value, 5)
        )

    def __dict__(self):
        od = OrderedDict()
        od['id'] = self.id
        od['ticker'] = self.ticker
        od['action'] = self.action
        od['quantity'] = self.quantity
        od['entry_date'] = self.entry_date
        od['entry_price'] = PriceParser.display(self.entry_price, 5)
        od['entry_name'] = self.entry_name
        od['exit_date'] = self.exit_date
        od['exit_price'] = PriceParser.display(self.exit_price, 5)
        od['exit_name'] = self.exit_name
        od['total_commission'] = PriceParser.display(self.total_commission, 5)
        od['unrealised_pnl'] = PriceParser.display(self.unrealised_pnl)
        od['realised_pnl'] = PriceParser.display(self.realised_pnl)
        od['trade_ret'] = self.trade_ret
        od['time_in_pos'] = self.time_in_pos
        return od
