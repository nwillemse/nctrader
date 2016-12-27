from .base import AbstractRiskManager
from ..event import OrderEvent


class ExampleRiskManager(AbstractRiskManager):
    def refine_orders(self, portfolio, sized_order):
        """
        This ExampleRiskManager object simply lets the
        sized order through, creates the corresponding
        OrderEvent object and adds it to a list.
        """
        if sized_order is None or sized_order.quantity == 0:
            return []

        elif sized_order.quantity > 0:
            order_event = OrderEvent(
                sized_order.ticker,
                sized_order.action,
                sized_order.quantity
            )
            return [order_event]
