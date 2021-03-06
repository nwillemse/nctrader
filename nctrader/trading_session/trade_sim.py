from __future__ import print_function

from ..compat import queue
from ..event import EventType

from datetime import datetime


class TradeSim(object):
    """
    Enscapsulates the settings and components for
    carrying out an event-driven trade simulator.
    """
    def __init__(
        self, price_handler, strategy, portfolio_handler, execution_handler,
        position_sizer, risk_manager, statistics, equity, end_date=None
    ):
        """
        Set up the variables according to
        what has been passed in.
        """
        self.price_handler = price_handler
        self.strategy = strategy
        self.portfolio_handler = portfolio_handler
        self.execution_handler = execution_handler
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.statistics = statistics
        self.equity = equity
        self.end_date = end_date
        self.events_queue = price_handler.events_queue
        self.cur_time = None

    def _run_backtest(self):
        """
        Carries out an infinite while loop that polls the
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop continue until the event queue has been
        emptied.
        """
        print("Running Backtest...")
        while self.price_handler.continue_backtest:
            try:
                event = self.events_queue.get(False)
            except queue.Empty:
                self.price_handler.stream_next()
            else:
                if (event.type == EventType.BAR and event.time > self.end_date):
                    continue
                if event.type == EventType.BAR:
                    self.cur_time = event.time
                    self.strategy.on_bar(event)
                    self.portfolio_handler.update_portfolio_value()
                    self.statistics.update(event)
                elif event.type == EventType.TRADE:
                    self.portfolio_handler.on_trade(event)
                elif event.type == EventType.ORDER:
                    self.execution_handler.execute_order(event)
                elif event.type == EventType.FILL:
                    self.portfolio_handler.on_fill(event)
                else:
                    raise NotImplemented("Unsupported event.type '%s'" % event.type)

    def simulate_trading(self, testing=False):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        self._run_backtest()
        print("---------------------------------")
        print("Backtest complete.")
        self.statistics.save()
