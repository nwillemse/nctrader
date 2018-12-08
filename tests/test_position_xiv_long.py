import unittest

from datetime import datetime
from nctrader.position import Position
from nctrader.price_parser import PriceParser


class TestLongRoundTripXIVPosition(unittest.TestCase):
    """
    Tests a long position with multiple entries and exits during the trade
    """
    def setUp(self):
        """
        Set up the Position object that will store the PnL.
        """
        self.position = Position(
            "BOT", "XIV", 4352,
            PriceParser.parse(15.01), PriceParser.parse(1.00),
            PriceParser.parse(15.01), PriceParser.parse(15.01),
            datetime(2011, 2, 4)
        )

    def test_enter_long_position(self):
        """
        Initial entry
        """
        print("Buy 4352 XIV at 15.01 with $1.00 commission. Update market value with bid/ask of 15.01/15.01:")
        self.position.update_market_value(
            PriceParser.parse(15.01), PriceParser.parse(15.01),
            datetime(2011, 2, 4)
        )
        print(self.position, '\n')

        self.assertEqual(self.position.action, "BOT")
        self.assertEqual(self.position.ticker, "XIV")
        self.assertEqual(self.position.quantity, 4352)

        self.assertEqual(self.position.buys, 4352)
        self.assertEqual(self.position.sells, 0)
        self.assertEqual(self.position.net, 4352)
        self.assertEqual(PriceParser.display(self.position.avg_bot, 5), 15.01)
        self.assertEqual(PriceParser.display(self.position.avg_sld, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_bot), 15.01*4352)
        self.assertEqual(PriceParser.display(self.position.total_sld), 0)
        self.assertEqual(PriceParser.display(self.position.net_total), 15.01*4352)
        self.assertEqual(PriceParser.display(self.position.total_commission), 1.00)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), 15.01*4352 - 1.00)

        self.assertEqual(PriceParser.display(self.position.avg_price, 5), round((15.01*4352 + 1.00) / 4352 / 1, 5))
        self.assertEqual(PriceParser.display(self.position.cost_basis, 2), 15.01*4352 + 1.00)
        self.assertEqual(PriceParser.display(self.position.market_value), round(((15.01+15.01)/2 * 4352 * 1), 2))
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl, 2), round(((15.01+15.01)/2 * 4352 * 1) - (15.01*4352 + 1.00), 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl, 2), 0.00)

        print("Sell 2188 shares of current position at 15.24 with 1.00 commission. Market at 15.24/15.24:")
        self.position.transact_shares(
            "SLD", 2188, PriceParser.parse(15.24), PriceParser.parse(1.00)
        )
        self.position.update_market_value(
            PriceParser.parse(15.24), PriceParser.parse(15.24),
            datetime(2011, 2, 7)
        )
        print(self.position, '\n')

        self.assertEqual(self.position.buys, 4352)
        self.assertEqual(self.position.sells, 2188)
        self.assertEqual(self.position.net, 4352-2188)
        self.assertEqual(PriceParser.display(self.position.avg_bot, 5), round((15.01*4352) / 4352, 5))
        self.assertEqual(PriceParser.display(self.position.avg_sld, 5), round((15.24*2188) / 2188, 5))
        self.assertEqual(PriceParser.display(self.position.total_bot), 15.01*4352)
        self.assertEqual(PriceParser.display(self.position.total_sld), 15.24*2188)
        self.assertEqual(PriceParser.display(self.position.net_total), round(15.24*2188 - (15.01*4352), 2))
        self.assertEqual(PriceParser.display(self.position.total_commission), 2.00)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), round(((15.24*2188) - (15.01*4352)) - 2.00, 2))

        self.assertEqual(PriceParser.display(self.position.avg_price, 5), round((15.01*4352 + 1) / 4352, 5))
        self.assertEqual(PriceParser.display(self.position.cost_basis, 2), 32482.14) #15.01*(4352-2188) + 1)
        self.assertEqual(PriceParser.display(self.position.market_value), round((15.24 * (4352-2188) * 1), 2))
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl, 2), round((15.24 * (4352-2188) * 1) - (32482.14), 2))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), (15.24-15.01)*2188 - 2)
        
        print("Sell 75 shares from current position at 220.85 with 1.37 commission. Market at 220.85/220.86:")
        self.position.transact_shares(
            "SLD", 75, PriceParser.parse(220.85), PriceParser.parse(1.37)
        )
        self.position.update_market_value(
            PriceParser.parse(220.85), PriceParser.parse(220.86),
            datetime(2016, 1, 3)
        )
        print(self.position, '\n')

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

        print("Sell 75 shares from current position at 221.24 with 1.37 commission. Market at 221.24/221.25:")
        self.position.transact_shares(
            "SLD", 75, PriceParser.parse(221.24), PriceParser.parse(1.37)
        )
        self.position.update_market_value(
            PriceParser.parse(221.24), PriceParser.parse(221.25),
            datetime(2016, 1, 3)
        )
        print(self.position, '\n')

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
