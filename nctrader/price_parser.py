from __future__ import division
from multipledispatch import dispatch
import numpy as np


class PriceParser(object):
    """
    PriceParser is designed to abstract away the underlying number used as a price
    within qstrader. Due to efficiency and floating point precision limitations,
    QSTrader uses an integer to represent all prices. This means that $0.10 is,
    internally, 10,000,000. Because such large numbers are rather unwieldy
    for humans, the PriceParser will take "normal" 2dp numbers as input, and show
    "normal" 2dp numbers as output when requested to `display()`

    For consistency's sake, PriceParser should be used for ALL prices that enter
    the qstrader system. Numbers should also always be parsed correctly to view.

    """

    # 10,000,000
    PRICE_MULTIPLIER = 10000000
    DEFAULT_PREC = 6

    """Parse Methods. Multiplies a float out into an int if needed."""

    @staticmethod
    @dispatch(int)
    def parse(x):  # flake8: noqa
        return x

    @staticmethod
    @dispatch(np.int64)
    def parse(x):  # flake8: noqa
        return x

    @staticmethod
    @dispatch(str)
    def parse(x):  # flake8: noqa
        return int(float(x) * PriceParser.PRICE_MULTIPLIER)

    @staticmethod
    @dispatch(float)
    def parse(x):  # flake8: noqa
        return int(x * PriceParser.PRICE_MULTIPLIER)

    """Display Methods. Multiplies a float out into an int if needed."""

    @staticmethod
    @dispatch(int)
    def display(x):  # flake8: noqa
        return round(x / PriceParser.PRICE_MULTIPLIER, PriceParser.DEFAULT_PREC)

    @staticmethod
    @dispatch(np.int64)
    def display(x):  # flake8: noqa
        return round(x / PriceParser.PRICE_MULTIPLIER, PriceParser.DEFAULT_PREC)

    @staticmethod
    @dispatch(np.float64)
    def display(x):  # flake8: noqa
        return round(x / PriceParser.PRICE_MULTIPLIER, PriceParser.DEFAULT_PREC)

    @staticmethod
    @dispatch(float)
    def display(x):  # flake8: noqa
        return round(x, PriceParser.DEFAULT_PREC)

    @staticmethod
    @dispatch(int, int)
    def display(x, dp):  # flake8: noqa
        return round(x / PriceParser.PRICE_MULTIPLIER, dp)

    @staticmethod
    @dispatch(np.int64, int)
    def display(x, dp):  # flake8: noqa
        return round(x / PriceParser.PRICE_MULTIPLIER, dp)

    @staticmethod
    @dispatch(float, int)
    def display(x, dp):  # flake8: noqa
        return round(x / PriceParser.PRICE_MULTIPLIER, dp)
