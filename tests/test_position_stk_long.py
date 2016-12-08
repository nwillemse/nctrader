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
            PriceParser.parse(220.45), PriceParser.parse(1.00),
            PriceParser.parse(220.45), PriceParser.parse(20.45),
            datetime(2016, 1, 1)
        )

    def test_calculate_round_trip(self):
        """
        After the subsequent purchase, carry out two more buys/longs
        and then close the position out with two additional sells/shorts.
        """
        print "Buy 100 SPY at 220.45 with $1.00 commission. Update market value with bid/ask of 220.70/220.71:"
        self.position.update_market_value(
            PriceParser.parse(220.70), PriceParser.parse(220.71),
            datetime(2016, 1, 2)
        )
        print self.position, '\n'
        
        self.assertEqual(self.position.action, "BOT")
        self.assertEqual(self.position.ticker, "SPY")
        self.assertEqual(self.position.quantity, 100)

        self.assertEqual(self.position.buys, 100)
        self.assertEqual(self.position.sells, 0)
        self.assertEqual(self.position.net, 100)
        self.assertEqual(PriceParser.display(self.position.avg_bot, 5), 220.45)
        self.assertEqual(PriceParser.display(self.position.avg_sld, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_bot), 220.45*100)
        self.assertEqual(PriceParser.display(self.position.total_sld), 0)
        self.assertEqual(PriceParser.display(self.position.net_total), 220.45*100)
        self.assertEqual(PriceParser.display(self.position.total_commission), 1.00)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), 220.45*100 - 1.00)

        self.assertEqual(PriceParser.display(self.position.avg_price, 5), (220.45*100 + 1.00) / 100 / 1)
        self.assertEqual(PriceParser.display(self.position.cost_basis), 220.45*100 + 1.00)
        self.assertEqual(PriceParser.display(self.position.market_value), round(((220.70+220.71)/2 * 100 * 1), 2))
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round(((220.70+220.71)/2 * 100 * 1) - (220.45*100 + 1.00), 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        
        print "Buy 50 shares to add to current position at 220.35 with 1.00 commission. Market at 220.41/220.42:"
        self.position.transact_shares(
            "BOT", 50, PriceParser.parse(220.35), PriceParser.parse(1.00)
        )
        self.position.update_market_value(
            PriceParser.parse(220.41), PriceParser.parse(220.42),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'

        self.assertEqual(self.position.buys, 150)
        self.assertEqual(self.position.sells, 0)
        self.assertEqual(self.position.net, 150)
        self.assertEqual(PriceParser.display(self.position.avg_bot, 5), round((220.45*100 + 220.35*50) / 150, 5))
        self.assertEqual(PriceParser.display(self.position.avg_sld, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_bot), 220.45*100 + 220.35*50)
        self.assertEqual(PriceParser.display(self.position.total_sld), 0)
        self.assertEqual(PriceParser.display(self.position.net_total), 0 - (220.45*100 + 220.35*50))
        self.assertEqual(PriceParser.display(self.position.total_commission), 2.00)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), (0 - (220.45*100 + 220.35*50)) - 2.00)

        self.assertEqual(PriceParser.display(self.position.avg_price, 5), (220.45*100 + 220.35*50 + 2.00) / 150 / 1)
        self.assertEqual(PriceParser.display(self.position.cost_basis), 220.45*100 + 220.35*50 + 2.00)
        self.assertEqual(PriceParser.display(self.position.market_value), round(((220.41+220.42)/2 * 150 * 1), 2))
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round(((220.41+220.42)/2 * 150 * 1) - (220.45*100 + 220.35*50 + 2.00), 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)
        
        print "Sell 75 shares from current position at 220.85 with 1.37 commission. Market at 220.85/220.86:"
        self.position.transact_shares(
            "SLD", 75, PriceParser.parse(220.85), PriceParser.parse(1.37)
        )
        self.position.update_market_value(
            PriceParser.parse(220.85), PriceParser.parse(220.86),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'

        self.assertEqual(self.position.buys, 150)
        self.assertEqual(self.position.sells, 75)
        self.assertEqual(self.position.net, 75)
        self.assertEqual(PriceParser.display(self.position.avg_bot, 5), round((220.45*100 + 220.35*50) / 150, 5))
        self.assertEqual(PriceParser.display(self.position.avg_sld, 5), 220.85 * 75 / 75)
        self.assertEqual(PriceParser.display(self.position.total_bot), 220.45*100 + 220.35*50)
        self.assertEqual(PriceParser.display(self.position.total_sld), 220.85 * 75)
        self.assertEqual(PriceParser.display(self.position.net_total), (220.85 * 75) - (220.45*100 + 220.35*50))
        self.assertEqual(PriceParser.display(self.position.total_commission), 3.37)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), ((220.85 * 75) - (220.45*100 + 220.35*50)) - 3.37)

        self.assertEqual(PriceParser.display(self.position.avg_price, 5), (220.45*100 + 220.35*50 + 2.00) / 150 / 1)
        self.assertEqual(PriceParser.display(self.position.cost_basis), ((220.45*100 + 220.35*50 + 2.00) / 150) * 75)
        self.assertEqual(PriceParser.display(self.position.market_value), round(((220.85+220.86)/2 * 75 * 1), 2))
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round(((220.85+220.86)/2 * 75 * 1) - ((220.45*100 + 220.35*50 + 2.00) / 150)*75, 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), (220.85 * 75) - ((220.45*100 + 220.35*50 + 2.00) / 150)*75 - 1.37)

        print "Sell 75 shares from current position at 221.24 with 1.37 commission. Market at 221.24/221.25:"
        self.position.transact_shares(
            "SLD", 75, PriceParser.parse(221.24), PriceParser.parse(1.37)
        )
        self.position.update_market_value(
            PriceParser.parse(221.24), PriceParser.parse(221.25),
            datetime(2016, 1, 3)
        )
        print self.position, '\n'

        self.assertEqual(self.position.buys, 150)
        self.assertEqual(self.position.sells, 150)
        self.assertEqual(self.position.net, 0)
        self.assertEqual(PriceParser.display(self.position.avg_bot, 5), round((220.45*100 + 220.35*50) / 150, 5))
        self.assertEqual(PriceParser.display(self.position.avg_sld, 5), (220.85*75 + 221.24*75) / 150)
        self.assertEqual(PriceParser.display(self.position.total_bot), 220.45*100 + 220.35*50)
        self.assertEqual(PriceParser.display(self.position.total_sld), 220.85*75 + 221.24*75)
        self.assertEqual(PriceParser.display(self.position.net_total), (220.85*75 + 221.24*75) - (220.45*100 + 220.35*50))
        self.assertEqual(PriceParser.display(self.position.total_commission), 3.37+1.37)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), round(((220.85*75 + 221.24*75) - (220.45*100 + 220.35*50)) - 3.37 - 1.37, 2))

        self.assertEqual(PriceParser.display(self.position.avg_price, 5), (220.45*100 + 220.35*50 + 2.00) / 150 / 1)
        self.assertEqual(PriceParser.display(self.position.cost_basis), 0)
        self.assertEqual(PriceParser.display(self.position.market_value), 0)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), 0)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), round(
                         (220.85*75) - ((220.45*100 + 220.35*50 + 2.00) / 150)*75 - 1.37 +
                         (221.24*75) - ((220.45*100 + 220.35*50 + 2.00) / 150)*75 - 1.37,
                         2)
        )
        

if __name__ == "__main__":
    unittest.main()
