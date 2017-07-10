import unittest

from datetime import datetime
from nctrader.position import Position
from nctrader.price_parser import PriceParser


class TestLongRoundTripSPYPosition(unittest.TestCase):
    """
    Test a round-trip trade in SPY ETF where the initial
    trade is a buy/long of 100 shares of SPY, at a price of
    $220.45, with $1.00 commission.
    """
    def setUp(self):
        """
        Set up the Position object that will store the PnL.
        """
        self.position = Position(
            "BOT", "SPY", 100,
            PriceParser.parse(239.08), PriceParser.parse(1.00),
            PriceParser.parse(220.45), PriceParser.parse(220.45),
            datetime(2016, 1, 1)
        )

    def test_initial_bot(self):
        """
        After the subsequent purchase, carry out two more buys/longs
        and then close the position out with two additional sells/shorts.
        """
        print("Buy 100 SPY at 239.08 with $1.00 commission. Update market value with bid/ask of 239.95/239.96:")
        self.position.update_market_value(
            PriceParser.parse(239.95), PriceParser.parse(239.96),
            datetime(2016, 1, 2)
        )
        print(self.position, '\n')

        self.assertIs(type(self.position.quantity), int)
        self.assertIs(type(self.position.open_quantity), int)
        self.assertIs(type(self.position.mul), int)
        self.assertIs(type(self.position.realised_pnl), int)
        self.assertIs(type(self.position.unrealised_pnl), int)
        self.assertIs(type(self.position.entry_price), int)
        self.assertIs(type(self.position.exit_price), int)
        self.assertIs(type(self.position.total_commission), int)
        self.assertIs(type(self.position.market_value), int)
        self.assertIs(type(self.position.cost_basis), int)

        print("Buy 300 shares to add to current position at 238.90 with 1.50 commission. Market at 238.96/238.97:")
        self.position.transact_shares(
            "BOT", 300, PriceParser.parse(238.90), PriceParser.parse(1.50)
        )
        self.position.update_market_value(
            PriceParser.parse(238.96), PriceParser.parse(238.97),
            datetime(2016, 1, 3)
        )
        print(self.position, '\n')
        
        self.assertIs(type(self.position.quantity), int)
        self.assertIs(type(self.position.open_quantity), int)
        self.assertIs(type(self.position.mul), int)
        self.assertIs(type(self.position.realised_pnl), int)
        self.assertIs(type(self.position.unrealised_pnl), int)
        self.assertIs(type(self.position.entry_price), int)
        self.assertIs(type(self.position.exit_price), int)
        self.assertIs(type(self.position.total_commission), int)
        self.assertIs(type(self.position.market_value), int)
        self.assertIs(type(self.position.cost_basis), int)

        print("Sell 150 shares from current position at 239.05 with 1.80 commission. Market at 239.19/239.20:")
        self.position.transact_shares(
            "SLD", 150, PriceParser.parse(239.05), PriceParser.parse(1.80)
        )
        self.position.update_market_value(
            PriceParser.parse(239.19), PriceParser.parse(239.20),
            datetime(2016, 1, 4)
        )
        print(self.position, '\n')

        self.assertIs(type(self.position.quantity), int)
        self.assertIs(type(self.position.open_quantity), int)
        self.assertIs(type(self.position.mul), int)
        self.assertIs(type(self.position.realised_pnl), int)
        self.assertIs(type(self.position.unrealised_pnl), int)
        self.assertIs(type(self.position.entry_price), int)
        self.assertIs(type(self.position.exit_price), int)
        self.assertIs(type(self.position.total_commission), int)
        self.assertIs(type(self.position.market_value), int)
        self.assertIs(type(self.position.cost_basis), int)

        print("Sell 250 shares to close position at 244.09 with 5.22 commission. Market at 244.09/244.10:")
        self.position.transact_shares(
            "SLD", 250, PriceParser.parse(244.09), PriceParser.parse(5.22)
        )
        self.position.update_market_value(
            PriceParser.parse(244.09), PriceParser.parse(244.10),
            datetime(2016, 1, 6)
        )
        print(self.position, '\n')

        self.assertIs(type(self.position.quantity), int)
        self.assertIs(type(self.position.open_quantity), int)
        self.assertIs(type(self.position.mul), int)
        self.assertIs(type(self.position.realised_pnl), int)
        self.assertIs(type(self.position.unrealised_pnl), int)
        self.assertIs(type(self.position.entry_price), int)
        self.assertIs(type(self.position.exit_price), int)
        self.assertIs(type(self.position.total_commission), int)
        self.assertIs(type(self.position.market_value), int)
        self.assertIs(type(self.position.cost_basis), int)


if __name__ == "__main__":
    unittest.main()
