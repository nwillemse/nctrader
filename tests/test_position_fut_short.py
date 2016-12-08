import unittest
from datetime import datetime

from nctrader.position import Position
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
        print "Setup initial position SLD 2 ES_0_I0B at 2200.25 with $4.06 commission:"
        self.position = Position(
            "SLD", "ES_0_I0B", 2,
            PriceParser.parse(2200.25), PriceParser.parse(4.06),
            PriceParser.parse(2201.50), PriceParser.parse(2201.75),
            datetime(2016, 1, 1)
        )
        print self.position, '\n'

    def test_transact_position(self):
        """
        Update market value of current position
        """
        print "Update market value with bid/ask of 2190.00/2190.25:"
        self.position.update_market_value(
            PriceParser.parse(2190.00), PriceParser.parse(2190.25),
            datetime(2016, 1, 2)
        )
        print self.position, '\n'
        
        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "ES_0_I0B")
        self.assertEqual(self.position.quantity, 2)

        self.assertEqual(self.position.buys, 0)
        self.assertEqual(self.position.sells, 2)
        self.assertEqual(self.position.net, -2)
        self.assertEqual(
            PriceParser.display(self.position.avg_bot, 5), 0
        )
        self.assertEqual(
            PriceParser.display(self.position.avg_sld, 5), 2200.25
        )
        self.assertEqual(PriceParser.display(self.position.total_bot), 0.00)
        self.assertEqual(PriceParser.display(self.position.total_sld), 2200.25*2*50)
        self.assertEqual(PriceParser.display(self.position.net_total), 2200.25*2*50)
        self.assertEqual(PriceParser.display(self.position.total_commission), 4.06)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), 2200.25*2*50 - 4.06)

        self.assertEqual(
            PriceParser.display(self.position.avg_price, 5), (2200.25*2*50 - 4.06) / 2 / 50
        )
        self.assertEqual(PriceParser.display(self.position.cost_basis), 2200.25*-2*50 + 4.06)
        self.assertEqual(PriceParser.display(self.position.market_value), (2190.00+2190.25)/2 * -2 * 50)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((((2190+2190.25)/2 * -2 * 50) - (2200.25*-2*50 + 4.06)), 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        print "Cover 1 contract of current position at 2198.50 with 2.03 commission. Market at 2199.00/2199.25:"
        self.position.transact_shares(
            "BOT", 1, PriceParser.parse(2198.50), PriceParser.parse(2.03)
        )
        self.position.update_market_value(
            PriceParser.parse(2199.00), PriceParser.parse(2199.25),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'

        self.assertEqual(self.position.quantity, 1)

        self.assertEqual(self.position.buys, 1)
        self.assertEqual(self.position.sells, 2)
        self.assertEqual(self.position.net, -1)
        self.assertEqual(
            PriceParser.display(self.position.avg_bot, 5), (2198.5 * 1) / 1
        )
        self.assertEqual(
            PriceParser.display(self.position.avg_sld, 5), (2200.25 * 2) / 2
        )
        self.assertEqual(PriceParser.display(self.position.total_bot), 2198.50*1*50)
        self.assertEqual(PriceParser.display(self.position.total_sld), 2200.25*2*50)
        self.assertEqual(PriceParser.display(self.position.net_total), 2200.25*2*50 - 2198.50*1*50)
        self.assertEqual(PriceParser.display(self.position.total_commission), 4.06+2.03)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), 2200.25*2*50 - 2198.50*1*50 - 6.09)

        self.assertEqual(
            PriceParser.display(self.position.avg_price, 5), (2200.25*2*50 - 4.06) / 2 / 50
        )
        self.assertEqual(PriceParser.display(self.position.cost_basis), 2200.25*-1*50 + 2.03)
        self.assertEqual(PriceParser.display(self.position.market_value), (2199.00+2199.25)/2 * -1 * 50)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((((2199+2199.25)/2 * -1 * 50) - (2200.25*-1*50 + 2.03)), 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), (2198.50 - 2200.25) * -1 * 50 - 4.06)

        print "Cover 1 contract TO CLOSE position at 2190.00 with 2.03 commission. Market at 2190.50/2190.75:"
        self.position.transact_shares(
            "BOT", 1, PriceParser.parse(2190.00), PriceParser.parse(2.03)
        )
        self.position.update_market_value(
            PriceParser.parse(2190.50), PriceParser.parse(2190.75),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'

if __name__ == "__main__":
    unittest.main()
