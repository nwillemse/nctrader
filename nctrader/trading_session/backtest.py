from __future__ import print_function

from ..compat import queue
from ..event import EventType

from datetime import datetime


class Backtest(object):
    """
    Enscapsulates the settings and components for
    carrying out an event-driven backtest.
    """
    def __init__(
        self, price_handler, strategy, portfolio_handler,
        execution_handler, position_sizer, risk_manager,
        statistics, equity, start_date=None, end_date=None
    ):
        """
        Set up the backtest variables according to
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
        self.start_date, self.end_date = self._default_dates(
            start_date, end_date
        )
        self.events_queue = price_handler.events_queue
        self.cur_time = None

    def _default_dates(self, start_date, end_date):
        """
        """
        if start_date is None:
            start_date = datetime(1900, 1, 1)
        if end_date is None:
            end_date = datetime(2099, 1, 1)
        return start_date, end_date

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
                if (event is not None and self.cur_time is None
                    or (self.cur_time >= self.start_date and self.cur_time <= self.end_date)
                ):
                    if event.type == EventType.TICK or event.type == EventType.BAR:
                        self.cur_time = event.time
                        self.strategy.calculate_signals(event)
                        self.portfolio_handler.update_portfolio_value()
                        self.statistics.update(event.time, self.portfolio_handler)
                    elif event.type == EventType.SIGNAL:
                        self.portfolio_handler.on_signal(event)
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
        results = self.statistics.get_results()
        print("---------------------------------")
        print("Backtest complete.")
        if not testing:
            self.statistics.plot_results()
        return results
