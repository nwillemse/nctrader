import click

from nctrader import settings
from nctrader.compat import queue
from nctrader.price_parser import PriceParser
from nctrader.price_handler.historic_csv_tick import HistoricCSVTickPriceHandler
from nctrader.strategy.example import ExampleStrategy
from nctrader.position_sizer.fixed import FixedPositionSizer
from nctrader.risk_manager.example import ExampleRiskManager
from nctrader.portfolio_handler import PortfolioHandler
from nctrader.compliance.example import ExampleCompliance
from nctrader.execution_handler.ib_simulated import IBSimulatedExecutionHandler
from nctrader.statistics.simple import SimpleStatistics
from nctrader.trading_session.backtest import Backtest


def run(config, testing, tickers, filename):

    # Set up variables needed for backtest
    events_queue = queue.Queue()
    csv_dir = config.CSV_DATA_DIR
    initial_equity = PriceParser.parse(500000.00)

    # Use Historic CSV Price Handler
    price_handler = HistoricCSVTickPriceHandler(
        csv_dir, events_queue, tickers
    )

    # Use the Example Strategy
    strategy = ExampleStrategy(tickers, events_queue)

    # Use an example Position Sizer
    position_sizer = FixedPositionSizer()

    # Use an example Risk Manager
    risk_manager = ExampleRiskManager()

    # Use the default Portfolio Handler
    portfolio_handler = PortfolioHandler(
        initial_equity, events_queue, price_handler,
        position_sizer, risk_manager
    )

    # Use the ExampleCompliance component
    compliance = ExampleCompliance(config)

    # Use a simulated IB Execution Handler
    execution_handler = IBSimulatedExecutionHandler(
        events_queue, price_handler, compliance
    )
    # Use the default Statistics
    statistics = SimpleStatistics(config, portfolio_handler)

    # Set up the backtest
    backtest = Backtest(
        price_handler, strategy,
        portfolio_handler, execution_handler,
        position_sizer, risk_manager,
        statistics, initial_equity
    )
    results = backtest.simulate_trading(testing=testing)
    statistics.save(filename)
    return results


@click.command()
@click.option('--config', default=settings.DEFAULT_CONFIG_FILENAME, help='Config filename')
@click.option('--testing/--no-testing', default=False, help='Enable testing mode')
@click.option('--tickers', default='GOOG', help='Tickers (use comma)')
@click.option('--filename', default='', help='Pickle (.pkl) statistics filename')
def main(config, testing, tickers, filename):
    tickers = tickers.split(",")
    config = settings.from_file(config, testing)
    run(config, testing, tickers, filename)


if __name__ == "__main__":
    main()
