import unittest
from datetime import datetime

from nctrader.position import Position
from nctrader.price_parser import PriceParser


class TestLongRoundTripESPosition(unittest.TestCase):
    """
    Test a round-trip trade in S&P e-mini futures contract where the initial
    trade is a buy/long of 1 contract of ES, at a price of
    2155.25, with $2.00 commission.
    """
    def setUp(self):
        """
        Set up the Position object that will store the PnL.
        """
        print "Setup initial position BOT 2 ES_0_I0B at 2180.50 with $4.06 commission:"
        self.position = Position(
            "BOT", "ES_0_I0B", 2,
            PriceParser.parse(2180.50), PriceParser.parse(4.06),
            PriceParser.parse(2181.50), PriceParser.parse(2181.75),
            datetime(2016, 1, 1)
        )
        print self.position, '\n'

    def test_transact_position(self):
        """
        Update market value of current position
        """
        print "Update market value with bid/ask of 2178.50/2178.75:"
        self.position.update_market_value(
            PriceParser.parse(2190.00), PriceParser.parse(2190.25),
            datetime(2016, 1, 2)
        )
        print self.position, '\n'

        self.assertEqual(self.position.action, "BOT")
        self.assertEqual(self.position.ticker, "ES_0_I0B")
        self.assertEqual(self.position.quantity, 2)

        self.assertEqual(self.position.buys, 2)
        self.assertEqual(self.position.sells, 0)
        self.assertEqual(self.position.net, 2)
        self.assertEqual(
            PriceParser.display(self.position.avg_bot, 5), 2180.50
        )
        self.assertEqual(
            PriceParser.display(self.position.avg_sld, 5), 0
        )
        self.assertEqual(PriceParser.display(self.position.total_bot), 218050.00)
        self.assertEqual(PriceParser.display(self.position.total_sld), 0.0)
        self.assertEqual(PriceParser.display(self.position.net_total), 218050.00)
        self.assertEqual(PriceParser.display(self.position.total_commission), 4.06)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), 218050.00 - 4.06)

        self.assertEqual(
            PriceParser.display(self.position.avg_price, 5), (218050.00 - 4.06) / 2 / 50
        )
        self.assertEqual(PriceParser.display(self.position.cost_basis), 218050 - 4.06)
        self.assertEqual(PriceParser.display(self.position.market_value), (2190+2190.25)/2 * 2 * 50)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((((2190+2190.25)/2 * 2 * 50) - (218050-4.06)), 2) * 1)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        
        print "Sell 1 contract of current position at 2187.50 with 2.03 commission. Market at 2193.50/2193.50:"
        self.position.transact_shares(
            "SLD", 1, PriceParser.parse(2187.50), PriceParser.parse(2.03)
        )
        self.position.update_market_value(
            PriceParser.parse(2193.50), PriceParser.parse(2193.50),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'

        self.assertEqual(self.position.quantity, 1)

        self.assertEqual(self.position.buys, 2)
        self.assertEqual(self.position.sells, 1)
        self.assertEqual(self.position.net, 1)
        self.assertEqual(
            PriceParser.display(self.position.avg_bot, 5), 2180.50
        )
        self.assertEqual(
            PriceParser.display(self.position.avg_sld, 5), 2187.50
        )
        self.assertEqual(PriceParser.display(self.position.total_bot), 218050.00)
        self.assertEqual(PriceParser.display(self.position.total_sld), 2187.5 * 50)
        self.assertEqual(PriceParser.display(self.position.net_total), (2187.5 * 50) - 218050.00)
        self.assertEqual(PriceParser.display(self.position.total_commission), 6.09)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), (2187.5 * 50) - 218050.00 - 6.09)

        self.assertEqual(
            PriceParser.display(self.position.avg_price, 5), (218050.00 - 4.06) / 2 / 50
        )
        self.assertEqual(PriceParser.display(self.position.cost_basis), round(1 * (218050.00 - 4.06) / 2 / 50 * 50, 2))
        self.assertEqual(PriceParser.display(self.position.market_value), (2193.50+2193.50)/2 * 1 * 50)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), 652.03)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 347.97)
        
        
        print "Sell 1 contract TO CLOSE position at 2199.00 with 2.03 commission. Market at 2199.50/2199.75:"
        self.position.transact_shares(
            "SLD", 1, PriceParser.parse(2199.00), PriceParser.parse(2.03)
        )
        self.position.update_market_value(
            PriceParser.parse(2199.50), PriceParser.parse(2199.75),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'
        
if __name__ == "__main__":
    unittest.main()
