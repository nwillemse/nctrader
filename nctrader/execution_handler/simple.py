from .base import AbstractExecutionHandler
from ..event import (FillEvent, EventType)
from ..price_parser import PriceParser


class SimpleExecutionHandler(AbstractExecutionHandler):
    """
    The simulated execution handler for Interactive Brokers
    converts all order objects into their equivalent fill
    objects automatically without latency, slippage or
    fill-ratio issues.

    This allows a straightforward "first go" test of any strategy,
    before implementation with a more sophisticated execution
    handler.
    """

    def __init__(self, events_queue, price_handler, compliance=None):
        """
        Initialises the handler, setting the event queue
        as well as access to local pricing.

        Parameters:
        events_queue - The Queue of Event objects.
        """
        self.events_queue = events_queue
        self.price_handler = price_handler
        self.compliance = compliance

    def execute_order(self, event):
        """
        Converts OrderEvents into FillEvents "naively",
        i.e. without any latency, slippage or fill ratio problems.

        Parameters:
        event - An Event object with order information.
        """
        if event.type == EventType.ORDER:
            # Obtain values from the OrderEvent
            timestamp = self.price_handler.get_last_timestamp(event.ticker)
            ticker = event.ticker
            action = event.action
            quantity = event.quantity
            name = event.name
            price = event.price
            commission = event.commission

            # Set a dummy exchange and calculate trade commission
            exchange = "ARCA"

            # Create the FillEvent and place on the events queue
            fill_event = FillEvent(
                timestamp, ticker,
                action, quantity,
                exchange, price,
                commission, name
            )
            self.events_queue.put(fill_event)

            if self.compliance is not None:
                self.compliance.record_trade(fill_event)
