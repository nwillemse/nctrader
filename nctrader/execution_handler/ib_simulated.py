from .base import AbstractExecutionHandler
from ..event import (FillEvent, EventType, StopType, StopMode)
from ..price_parser import PriceParser


class IBSimulatedExecutionHandler(AbstractExecutionHandler):
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

    def calculate_ib_commission(self):
        """
        Calculate the Interactive Brokers commission for
        a transaction. At this stage, simply add in $1.00
        for transaction costs, irrespective of lot size.
        """
        return PriceParser.parse(1.00)

    def calculate_stop_price(self, action, fill_price, stoploss):
        """
        """
        stop_price = 0
        if stoploss is None:
            return stop_price

        stop_type = stoploss['StopType']
        stop_mode = stoploss['StopMode']
        stop_amount = stoploss['StopAmount']
        
        if stop_type == StopType.LOSS:
            mul = -1 if action == "BOT" else 1
        else:
            print "StopType not implemented:", stop_type
            return 0
        
        if stop_mode == StopMode.POINTS:
            stop_price = fill_price + (stop_amount * mul)
        elif stop_mode == StopMode.PERCENT:
            stop_price = fill_price * ((1*mul) + stop_amount)

        return stop_price
        
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

            # Obtain the fill price
            if self.price_handler.istick():
                bid, ask = self.price_handler.get_best_bid_ask(ticker)
                if event.action == "BOT":
                    fill_price = ask
                else:
                    fill_price = bid
            else:
                close_price = self.price_handler.get_last_close(ticker)
                fill_price = close_price

            # Set a dummy exchange and calculate trade commission
            exchange = "ARCA"
            commission = self.calculate_ib_commission()

            # Calculate stop loss price
            stop_price = self.calculate_stop_price(
                event.action, fill_price, event.stoploss
            )

            # Create the FillEvent and place on the events queue
            fill_event = FillEvent(
                timestamp, ticker,
                action, quantity,
                exchange, fill_price,
                commission, stop_price
            )
            self.events_queue.put(fill_event)

            if self.compliance is not None:
                self.compliance.record_trade(fill_event)
