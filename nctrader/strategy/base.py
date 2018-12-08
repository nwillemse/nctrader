from abc import ABCMeta, abstractmethod


class AbstractStrategy(object):
    """
    AbstractStrategy is an abstract base class providing an interface for
    all subsequent (inherited) strategy handling objects.

    The goal of a (derived) Strategy object is to generate Signal
    objects for particular symbols based on the inputs of ticks
    generated from a PriceHandler (derived) object.

    This is designed to work both with historic and live data as
    the Strategy object is agnostic to data location.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def on_bar(self, event):
        """
        Gets called whenever a bar event received.
        """
        raise NotImplementedError("Should implement on_bar()")

    @abstractmethod
    def on_tick(self, event):
        """
        Gets called whenever a tick event received.
        """
        raise NotImplementedError("Should implement on_tick()")

class Strategies(AbstractStrategy):
    """
    Strategies is a collection of strategy
    """
    def __init__(self, *strategies):
        self._lst_strategies = strategies

    def on_bar(self, event):
        for strategy in self._lst_strategies:
            strategy.on_bar(event)

    def on_tick(self, event):
        for strategy in self._lst_strategies:
            strategy.on_tick(event)
