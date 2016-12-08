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
            "SLD", "SPY", 100,
            PriceParser.parse(220.78), PriceParser.parse(1.49),
            PriceParser.parse(220.45), PriceParser.parse(220.45),
            datetime(2016, 1, 1)
        )

    def test_calculate_round_trip(self):
        """
        After the subsequent purchase, carry out two more buys/longs
        and then close the position out with two additional sells/shorts.
        """
        print "Sell 100 SPY at 220.78 with $1.49 commission. Update market value with bid/ask of 220.85/220.86:"
        self.position.update_market_value(
            PriceParser.parse(220.85), PriceParser.parse(220.86),
            datetime(2016, 1, 2)
        )
        print self.position, '\n'

        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "SPY")
        self.assertEqual(self.position.quantity, 100)

        self.assertEqual(self.position.buys, 0)
        self.assertEqual(self.position.sells, 100)
        self.assertEqual(self.position.net, -100)
        self.assertEqual(PriceParser.display(self.position.avg_bot, 5), 0)
        self.assertEqual(PriceParser.display(self.position.avg_sld, 5), (220.78*100) / 100)
        self.assertEqual(PriceParser.display(self.position.total_bot), 0)
        self.assertEqual(PriceParser.display(self.position.total_sld), 220.78*100)
        self.assertEqual(PriceParser.display(self.position.net_total), 220.78*100 - 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), 1.49)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), 220.78*100 - 0 - 1.49)

        self.assertEqual(PriceParser.display(self.position.avg_price, 5), (220.78*100 - 1.49) / 100 / 1)
        self.assertEqual(PriceParser.display(self.position.cost_basis), -1 * (220.78*100 - 1.49))
        self.assertEqual(PriceParser.display(self.position.market_value), -1 * round(((220.85+220.86)/2 * 100 * 1), 2))
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round(-1 * ((220.85+220.86)/2 * 100 * 1) - (-1 * (220.78*100 - 1.49)), 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)
        
        print "Sell 200 shares to add to current position at 220.85 with 1.99 commission. Market at 220.91/220.92:"
        self.position.transact_shares(
            "SLD", 200, PriceParser.parse(220.85), PriceParser.parse(1.99)
        )
        self.position.update_market_value(
            PriceParser.parse(220.91), PriceParser.parse(220.92),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'

        self.assertEqual(self.position.buys, 0)
        self.assertEqual(self.position.sells, 300)
        self.assertEqual(self.position.net, -300)
        self.assertEqual(PriceParser.display(self.position.avg_bot, 5), 0)
        self.assertEqual(PriceParser.display(self.position.avg_sld, 5), round((220.78*100 + 220.85*200) / 300, 5))
        self.assertEqual(PriceParser.display(self.position.total_bot), 0)
        self.assertEqual(PriceParser.display(self.position.total_sld), 220.78*100 + 220.85*200)
        self.assertEqual(PriceParser.display(self.position.net_total), 220.78*100 + 220.85*200 - 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), 1.49+1.99)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), round((220.78*100 + 220.85*200) - 0 - 1.49 - 1.99, 2))

        self.assertEqual(PriceParser.display(self.position.avg_price, 5), round((220.78*100 + 220.85*200 + (1.49 + 1.99)*-1) / 300 / 1, 5))
        self.assertEqual(PriceParser.display(self.position.cost_basis), round(-1 * (220.78*100 + 220.85*200 + (1.49 + 1.99)*-1), 2))
        self.assertEqual(PriceParser.display(self.position.market_value), -1 * round(((220.91+220.92)/2 * 300 * 1), 2))
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round(-1 * ((220.91+220.92)/2 * 300 * 1) - (-1 * (220.78*100 + 220.85*200 + (1.49 + 1.99)*-1)), 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        print "Buy 125 shares at 220.66 with ??? commission. Market at 220.66/220.67:"
        self.position.transact_shares(
            "BOT", 125, PriceParser.parse(220.66), PriceParser.parse(0.00)
        )
        self.position.update_market_value(
            PriceParser.parse(220.66), PriceParser.parse(220.67),
            datetime(2016, 1, 4)
        )
        print self.position, '\n'

        """
        print "Sell 75 shares from current position at 221.24 with 1.37 commission. Market at 221.24/221.25:"
        self.position.transact_shares(
            "SLD", 75, PriceParser.parse(221.24), PriceParser.parse(1.37)
        )
        self.position.update_market_value(
            PriceParser.parse(221.24), PriceParser.parse(221.25),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'
        """

if __name__ == "__main__":
    unittest.main()
