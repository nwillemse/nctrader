from .base import AbstractPositionSizer


class RotationalPositionSizer(AbstractPositionSizer):
    def __init__(
            self, fraction=1.0, dollar_per_contract=0.0, units_per_position=1
    ):
        self.fraction = fraction
        self.dollar_per_contract = dollar_per_contract
        self.units_per_position = units_per_position

    def size_order(self, portfolio, initial_order):
        """
        This RotationalPositionSizer object modifies the quantity base on
        the fraction specified in the order.  Value of 0 implies exit position if
        in a position, values < 0 implies short positions and values > 0 implies
        long positions
        """
        if initial_order is None:
            return
        
        n_shares = 0
        action = None

        ticker_info = portfolio.price_handler.tickers_info[initial_order.ticker]
        last_price = portfolio.price_handler.get_last_close(initial_order.ticker)
        pos = portfolio.get_position(initial_order.ticker)
        order_fraction = initial_order.fraction


        # only size the order if quantity is zero - entry order
        if initial_order.quantity != 0:
            raise Exception("The order quantity should be zero for rotational position sizer:", initial_order)

        if pos is None:
            action = 'BOT' if order_fraction > 0 else 'SLD'
            if ticker_info.type == 'STK':
                n_shares = int(portfolio.equity * self.fraction * order_fraction / last_price)
            else:
                raise Exception("Ticker type not handled for", ticker_info)

        else:
            # exit current pos if fraction is zero
            if order_fraction == 0:
                action = 'SLD' if pos.action == 'BOT' else 'BOT'
                n_shares = abs(pos.net)

            else:
                target_pos = int(portfolio.equity * self.fraction * order_fraction / last_price)
                n_shares = target_pos - pos.net
                if n_shares > 0:
                    action = 'BOT'
                elif n_shares < 0:
                    action = 'SLD'
                else:
                    print("The order's new net position is zero:", n_shares)
                    return None

        initial_order.action = action
        initial_order.quantity = abs(n_shares)

        return initial_order
