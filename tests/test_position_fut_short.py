import unittest
from datetime import datetime

from nctrader.position2 import Position
from nctrader.price_parser import PriceParser


class TestShortRoundTripESPosition(unittest.TestCase):
    """
    Test a round-trip trade in S&P e-mini futures contract where the initial
    trade is a buy/long of 1 contract of ES, at a price of
    2155.25, with $2.00 commission.
    """
    def setUp(self):
        """
        Set up the Position object that will store the PnL.
        """
        print("Setup initial position SLD 1 ES at 2430.50 with $2.03 commission:")
        self.position = Position(
            "SLD", "ES", 1,
            PriceParser.parse(2430.50), PriceParser.parse(2.04),
            PriceParser.parse(2400.50), PriceParser.parse(2400.75),
            datetime(2016, 1, 1), mul=50
        )
        print(self.position, '\n')

    def test_transact_position(self):
        """
        Update market value of current position
        """
        print("Update market value with bid/ask of 2423.75.00/2424.00:")
        self.position.update_market_value(
            PriceParser.parse(2423.75), PriceParser.parse(2424.00),
            datetime(2016, 1, 2)
        )
        print(self.position, '\n')
                
        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "ES")
        self.assertEqual(self.position.quantity, 1)
        self.assertEqual(self.position.open_quantity, 1)

        self.assertEqual(PriceParser.display(self.position.entry_price, 5), round((2430.50 * 50 - 2.04) / 50, 5) )
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), 2.04)
        self.assertEqual(PriceParser.display(self.position.cost_basis), -50*2430.50 + 2.04)
        self.assertEqual(PriceParser.display(self.position.market_value), -50*2424.00, 2)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((50*2424.00*-1) - (50*2430.50*-1 + 2.04),2) , 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        print("Sell 3 ES @ 2422.75 with $6.12 commission. Update market value with bid/ask of 2420.75/2421.00:")
        self.position.transact_shares(
            "SLD", 3, PriceParser.parse(2422.75), PriceParser.parse(6.12)
        )
        self.position.update_market_value(
            PriceParser.parse(2420.75), PriceParser.parse(2421.00),
            datetime(2016, 1, 3)
        )
        print(self.position, '\n')
        print(self.position.bots, self.position.solds)

        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "ES")
        self.assertEqual(self.position.quantity, 4)
        self.assertEqual(self.position.open_quantity, 4)

        self.assertEqual(PriceParser.display(self.position.entry_price, 5), round((2430.50 * 50 - 2.04 + 3*2422.75*50 - 6.12) / 4 / 50, 5) )
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), 2.04+6.12)
        self.assertEqual(PriceParser.display(self.position.cost_basis), (-50*2430.50 + 2.04) + (-3*50*2422.75 + 6.12) )
        self.assertEqual(PriceParser.display(self.position.market_value), -4*50*2421.00, 2)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((-4*50*2421.00) - ((-50*2430.50 + 2.04) + (-3*50*2422.75 + 6.12)),2) , 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)


if __name__ == "__main__":
    unittest.main()
