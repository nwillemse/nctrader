from .base import AbstractPositionSizer


class FixedDollarPositionSizer(AbstractPositionSizer):
    def __init__(
            self, dollar_amount
    ):
        self.dollar_amount = dollar_amount


    def size_order(self, portfolio, initial_order):
        """
        This FixedDollarPositionSizer object modifies the quantity base on
        how many shares or contracts can be purchased for dollar_amount.
        """
        if initial_order is None:
            return
        
        ticker_info = portfolio.price_handler.tickers_info[initial_order.ticker]
        last_price = portfolio.price_handler.get_last_close(initial_order.ticker)

        # only size the order if quantity is zero - entry order
        if initial_order.quantity == 0:
            if ticker_info.type == 'STK':
                quantity = int(self.dollar_amount / last_price)
            elif ticker_info.type == 'FUT':
                quantity = int(self.dollar_amount / ticker_info.margin)
            else:
                print("Ticker type not handled for", ticker_info)
        
            initial_order.quantity = quantity

        return initial_order
