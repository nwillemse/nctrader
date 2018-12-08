import unittest

from datetime import datetime
from nctrader.position2 import Position
from nctrader.price_parser import PriceParser


class TestShortRoundTripSPYPosition(unittest.TestCase):
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
            "SLD", "SPY", 400,
            PriceParser.parse(244.15), PriceParser.parse(4.18),
            PriceParser.parse(244.05), PriceParser.parse(244.06),
            datetime(2016, 1, 1)
        )
        print(self.position, '\n')

    def test_calculate_round_trip(self):
        """
        After the subsequent purchase, carry out two more buys/longs
        and then close the position out with two additional sells/shorts.
        """
        print("Sell 400 SPY at 244.15 with $4.18 commission. Update market value with bid/ask of 244.05/244.06:")
        self.position.update_market_value(
            PriceParser.parse(244.05), PriceParser.parse(244.06),
            datetime(2016, 1, 2)
        )
        print(self.position, '\n')

        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "SPY")
        self.assertEqual(self.position.quantity, 400)
        self.assertEqual(self.position.open_quantity, 400)

        self.assertEqual(PriceParser.display(self.position.entry_price, 5), (244.15*400 - 4.18) / 400)
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), 4.18)
        self.assertEqual(PriceParser.display(self.position.cost_basis), -1*244.15*400 + 4.18)
        self.assertEqual(PriceParser.display(self.position.market_value), -1*244.06*400, 2)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((-1*244.06*400) - (-1*244.15*400 + 4.18),2) , 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        print("Sell 250 SPY at 243.88 with $2.61 commission. Update market value with bid/ask of 243.47/243.48:")
        self.position.transact_shares(
            "SLD", 250, PriceParser.parse(243.88), PriceParser.parse(2.61)
        )
        self.position.update_market_value(
            PriceParser.parse(243.47), PriceParser.parse(243.48),
            datetime(2016, 1, 3)
        )
        print(self.position, '\n')

        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "SPY")
        self.assertEqual(self.position.quantity, 400+250)
        self.assertEqual(self.position.open_quantity, 400+250)

        self.assertEqual(PriceParser.display(self.position.entry_price, 5), round((244.15*400+4.18 + 243.88*250+2.61) / 650, 5))
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), round(4.18+2.61, 2))
        self.assertEqual(PriceParser.display(self.position.cost_basis), round(-1*244.15*400 + 4.18 -1*243.88*250 + 2.61, 2))
        self.assertEqual(PriceParser.display(self.position.market_value), -1*243.48*650, 2)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((-1*243.48*650) - (-1*244.15*400 + 4.18 -1*243.88*250 + 2.61),2) , 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        print("Sell 150 SPY at 243.50 with $1.81 commission. Update market value with bid/ask of 243.50/243.51:")
        self.position.transact_shares(
            "SLD", 150, PriceParser.parse(243.50), PriceParser.parse(1.81)
        )
        self.position.update_market_value(
            PriceParser.parse(243.50), PriceParser.parse(243.51),
            datetime(2016, 1, 4)
        )
        print(self.position, '\n')
        print("bots:", self.position.bots)
        print("solds:", self.position.solds)

        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "SPY")
        self.assertEqual(self.position.quantity, 400+250+150)
        self.assertEqual(self.position.open_quantity, 400+250+150)

        self.assertEqual(PriceParser.display(self.position.entry_price, 5), round((244.15*400+4.18 + 243.88*250+2.61 + 243.50*150+1.81) / 800, 5))
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), 0)
        self.assertEqual(PriceParser.display(self.position.total_commission), round(4.18+2.61+1.81, 2))
        self.assertEqual(PriceParser.display(self.position.cost_basis), round(-1*244.15*400 + 4.18 -1*243.88*250 + 2.61 -1*243.50*150 + 1.81, 2))
        self.assertEqual(PriceParser.display(self.position.market_value), -1*243.51*800, 2)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((-1*243.51*800) - (-1*244.15*400 + 4.18 -1*243.88*250 + 2.61 -1*243.50*150 + 1.81),2) , 2)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        print("Buy 50 SPY at 243.77 with $1.00 commission. Update market value with bid/ask of 243.84/243.86:")
        self.position.transact_shares(
            "BOT", 50, PriceParser.parse(243.77), PriceParser.parse(1.00)
        )
        self.position.update_market_value(
            PriceParser.parse(243.84), PriceParser.parse(243.86),
            datetime(2016, 1, 5)
        )
        print(self.position, '\n')

        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "SPY")
        self.assertEqual(self.position.quantity, 400+250+150)
        self.assertEqual(self.position.open_quantity, 400+250+150-50)

        self.assertEqual(PriceParser.display(self.position.entry_price, 5), round((244.15*400+4.18 + 243.88*250+2.61 + 243.50*150+1.81) / 800, 5))
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), (243.77*50+1)/50)
        self.assertEqual(PriceParser.display(self.position.total_commission), round(4.18+2.61+1.81+1, 2))
        self.assertEqual(PriceParser.display(self.position.cost_basis), round(-1*244.15*350 + 350/400*4.18 -1*243.88*250 + 2.61 -1*243.50*150 + 1.81, 4))
        self.assertEqual(PriceParser.display(self.position.market_value), -1*243.86*750, 2)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), round((-1*243.86*750) - (-1*244.15*350 + 350/400*4.18 -1*243.88*250 + 2.61 -1*243.50*150 + 1.81), 4))
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 17.4775)

        print("Buy 750 SPY at 244.29 with $3.75 commission. Update market value with bid/ask of 243.84/243.86:")
        self.position.transact_shares(
            "BOT", 750, PriceParser.parse(244.29), PriceParser.parse(3.75)
        )
        self.position.update_market_value(
            PriceParser.parse(243.29), PriceParser.parse(243.29),
            datetime(2016, 1, 6)
        )
        print(self.position, '\n')
        print("bots:", self.position.bots)
        print("solds:", self.position.solds)

        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "SPY")
        self.assertEqual(self.position.quantity, 400+250+150)
        self.assertEqual(self.position.open_quantity, 400+250+150-50-750)

        self.assertEqual(PriceParser.display(self.position.entry_price, 5), round((244.15*400+4.18 + 243.88*250+2.61 + 243.50*150+1.81) / 800, 5))
        self.assertEqual(PriceParser.display(self.position.exit_price, 5), round((243.77*50+1 + 244.29*750+3.75)/800, 5))
        self.assertEqual(PriceParser.display(self.position.total_commission), round(4.18+2.61+1.81+1+3.75, 2))
        self.assertEqual(PriceParser.display(self.position.cost_basis), 0)
        self.assertEqual(PriceParser.display(self.position.market_value), 0)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), 0)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), -264.35)

if __name__ == "__main__":
    unittest.main()
