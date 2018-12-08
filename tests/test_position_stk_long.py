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

    def test_calculate_round_trip(self):
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

        self.assertEqual(self.position.action, "BOT")
        self.assertEqual(self.position.ticker, "SPY")
        self.assertEqual(self.position.quantity, 100)
        self.assertEqual(self.position.open_quantity, 100)

        self.assertEqual(PriceParser.display(self.position.entry_price, 5), (239.08*100 + 1)/100)
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), 1.00)
        self.assertEqual(PriceParser.display(self.position.cost_basis), 239.08*100 + 1.00)
        self.assertEqual(PriceParser.display(self.position.market_value), 239.95*100 * 1, 2)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), (239.95*100 * 1) - (239.08*100 + 1.00), 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        print("Buy 300 shares to add to current position at 238.90 with 1.50 commission. Market at 238.96/238.97:")
        self.position.transact_shares(
            "BOT", 300, PriceParser.parse(238.90), PriceParser.parse(1.50)
        )
        self.position.update_market_value(
            PriceParser.parse(238.96), PriceParser.parse(238.97),
            datetime(2016, 1, 3)
        )
        print(self.position, '\n')

        self.assertEqual(self.position.quantity, 400)
        self.assertEqual(self.position.open_quantity, 400)
        self.assertEqual(PriceParser.display(self.position.entry_price, 5), (239.08*100+1 + 238.90*300+1.5)/400)
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), 2.50)
        self.assertEqual(PriceParser.display(self.position.cost_basis), (239.08*100+1 + 238.90*300+1.5))
        self.assertEqual(PriceParser.display(self.position.market_value), 238.96 * 400, 2)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), (238.96 * 400) - (239.08*100+1 + 238.90*300+1.5), 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)
  
        print("Sell 150 shares from current position at 239.05 with 1.80 commission. Market at 239.19/239.20:")
        self.position.transact_shares(
            "SLD", 150, PriceParser.parse(239.05), PriceParser.parse(1.80)
        )
        self.position.update_market_value(
            PriceParser.parse(239.19), PriceParser.parse(239.20),
            datetime(2016, 1, 4)
        )
        print(self.position, '\n')
        
        self.assertEqual(self.position.quantity, 400)
        self.assertEqual(self.position.open_quantity, 100+300-150)
        self.assertEqual(PriceParser.display(self.position.entry_price, 5), (239.08*100+1 + 238.90*300+1.5)/400)
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), (239.05*150+1.80)/150)
        self.assertEqual(PriceParser.display(self.position.total_commission), 4.30)
        self.assertEqual(PriceParser.display(self.position.cost_basis), (238.90*250)+(250/300*1.5))
        self.assertEqual(PriceParser.display(self.position.market_value), 239.19 * 250)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), (239.19 * 250) - ((238.90*250)+(250/300*1.5)), 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 1.45)
        
        print("Buy 250 shares adding to current position at 239.39 with 1.25 commission. Market at 245.24/245.25:")
        self.position.transact_shares(
            "BOT", 250, PriceParser.parse(239.39), PriceParser.parse(1.25)
        )
        self.position.update_market_value(
            PriceParser.parse(245.24), PriceParser.parse(245.25),
            datetime(2016, 1, 5)
        )
        print(self.position, '\n')

        self.assertEqual(self.position.quantity, 650)
        self.assertEqual(self.position.open_quantity, 100+300-150+250)
        self.assertEqual(PriceParser.display(self.position.entry_price, 5), round((239.08*100+1 + 238.90*300+1.5 + 239.39*250+1.25)/650, 5))
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), (239.05*150+1.80)/150)
        self.assertEqual(PriceParser.display(self.position.total_commission), 5.55)
        self.assertEqual(PriceParser.display(self.position.cost_basis), (238.90*250)+(250/300*1.5)+(239.39*250+1.25))
        self.assertEqual(PriceParser.display(self.position.market_value), 245.24 * 500)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), (245.24 * 500) - ((238.90*250)+(250/300*1.5)+(239.39*250+1.25)), 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 1.45)

        print("Sell 500 shares to close position at 244.09 with 5.22 commission. Market at 244.09/244.10:")
        self.position.transact_shares(
            "SLD", 500, PriceParser.parse(244.09), PriceParser.parse(5.22)
        )
        self.position.update_market_value(
            PriceParser.parse(244.09), PriceParser.parse(244.10),
            datetime(2016, 1, 6)
        )
        print(self.position, '\n')

        self.assertEqual(self.position.quantity, 650)
        self.assertEqual(self.position.open_quantity, 100+300-150+250-500)
        self.assertEqual(PriceParser.display(self.position.entry_price, 5), round((239.08*100+1 + 238.90*300+1.5 + 239.39*250+1.25)/650, 5))
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), round((239.05*150+1.80 + 244.09*500+5.22)/(150+500), 5))
        self.assertEqual(PriceParser.display(self.position.total_commission), 5.55+5.22)
        self.assertEqual(PriceParser.display(self.position.cost_basis), 0)
        self.assertEqual(PriceParser.display(self.position.market_value), 0)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), 0)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), round(1.45+(244.09-238.90)*250-250/300*1.5+(244.09-239.39)*250-1.25-5.22, 2))


if __name__ == "__main__":
    unittest.main()
