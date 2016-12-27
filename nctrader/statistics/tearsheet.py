from .base import AbstractStatistics
from ..price_parser import PriceParser

from matplotlib.ticker import FuncFormatter
from matplotlib import cm
from datetime import datetime
from collections import OrderedDict

import nctrader.statistics.performance as perf

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import seaborn as sns
import os
import csv


class TearsheetStatistics(AbstractStatistics):
    """
    """
    def __init__(self, config, portfolio_handler, title=None,
                 benchmark=None, start_date=None, end_date=None
    ):
        """
        Takes in the config, a portfolio handler, optional title
        and benchmark.
        """
        self.config = config
        self.portfolio_handler = portfolio_handler
        self.price_handler = portfolio_handler.price_handler
        self.title = '\n'.join(title)
        self.benchmark = benchmark
        self.start_date = start_date
        self.end_date = end_date
        self.equity = {}
        self.equity_benchmark = {}
        self.log_scale = False
        self.equity_file = []
        self.current_timestamp = None
        self.current_line = OrderedDict()


    def update(self, event):
        """
        Update equity curve and benchmark equity curve that must be tracked
        over time.
        """
        if self.current_timestamp == None or event.time < self.start_date:
            self.current_timestamp = event.time
            return

        if event.time <> self.current_timestamp and len(self.current_line) > 0:
            self.equity_file.append(self.current_line.copy())
            self.current_line.clear()
        else:
            self.current_line['timestamp'] = event.time
            self.equity[event.time] = PriceParser.display(
                self.portfolio_handler.portfolio.equity
            )
            self.current_line['equity'] = PriceParser.display(
                self.portfolio_handler.portfolio.equity
            )
            self.current_line['contracts'] = (
                self.portfolio_handler.portfolio.open_quantity
            )

        self.current_timestamp = event.time


    def get_results(self):
        """
        Return a dict with all important results & stats.
        """
        # Equity
        equity_s = pd.Series(self.equity).sort_index()

        # Returns
        returns_s = equity_s.pct_change().fillna(0.0)

        # Cummulative Returns
        cum_returns_s = np.exp(np.log(1 + returns_s).cumsum())

        # Drawdown, max drawdown, max drawdown duration
        dd_s, max_dd, dd_dur = perf.create_drawdowns(cum_returns_s)

        statistics = {}

        # Equity statistics
        statistics["sharpe"] = perf.create_sharpe_ratio(returns_s)
        statistics["drawdowns"] = dd_s
        # TODO: need to have max_drawdown so it can be printed at end of test
        statistics["max_drawdown"] = max_dd
        statistics["max_drawdown_pct"] = max_dd
        statistics["max_drawdown_duration"] = dd_dur
        statistics["equity"] = equity_s
        statistics["returns"] = returns_s
        statistics["cum_returns"] = cum_returns_s
        statistics["positions"] = pd.DataFrame(self._get_positions())

        # Benchmark statistics if benchmark ticker specified
        if self.benchmark is not None:
            equity_b = pd.Series(self.equity_benchmark).sort_index()
            returns_b = equity_b.pct_change().fillna(0.0)
            cum_returns_b = np.exp(np.log(1 + returns_b).cumsum())
            dd_b, max_dd_b, dd_dur_b = perf.create_drawdowns(cum_returns_b)
            statistics["sharpe_b"] = perf.create_sharpe_ratio(returns_b)
            statistics["drawdowns_b"] = dd_b
            statistics["max_drawdown_pct_b"] = max_dd_b
            statistics["max_drawdown_duration_b"] = dd_dur_b
            statistics["equity_b"] = equity_b
            statistics["returns_b"] = returns_b
            statistics["cum_returns_b"] = cum_returns_b

        return statistics


    def _get_positions(self):
        """
        Retrieve the list of closed Positions objects from the portfolio
        and reformat into a pandas dataframe to be returned
        """
        pos = self.portfolio_handler.portfolio.closed_positions
        a = []
        for p in pos:
            d = p.__dict__()
            a.append(d)

        return a


    def _plot_equity(self, stats, ax=None, **kwargs):
        """
        Plots cumulative rolling returns versus some benchmark.
        """
        def format_two_dec(x, pos):
            return '%.2f' % x

        equity = stats['cum_returns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_two_dec)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.yaxis.grid(linestyle=':')
        ax.xaxis.set_tick_params(reset=True)
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.grid(linestyle=':')


        if self.benchmark is not None:
            benchmark = stats['cum_returns_b']
            benchmark.plot(
                lw=2, color='gray', label=self.benchmark, alpha=0.60,
                ax=ax, **kwargs
            )

        equity.plot(lw=2, color='green', alpha=0.6, x_compat=False,
                    label='Backtest', ax=ax, **kwargs)

        ax.axhline(1.0, linestyle='--', color='black', lw=1)
        ax.set_ylabel('Cumulative returns')
        ax.legend(loc='best')
        ax.set_xlabel('')
        plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')

        if self.log_scale:
            ax.set_yscale('log')

        return ax


    def _plot_drawdown(self, stats, ax=None, **kwargs):
        """
        Plots the underwater curve
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        drawdown = stats['drawdowns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.yaxis.grid(linestyle=':')
        ax.xaxis.set_tick_params(reset=True)
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.grid(linestyle=':')


        underwater = -100 * drawdown
        underwater.plot(ax=ax, lw=2, kind='area', color='red', alpha=0.3, **kwargs)
        ax.set_ylabel('')
        ax.set_xlabel('')
        plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')
        ax.set_title('Drawdown (%)', fontweight='bold')
        return ax


    def _plot_monthly_returns(self, stats, ax=None, **kwargs):
        """
        Plots a heatmap of the monthly returns.
        """
        returns = stats['returns']
        if ax is None:
            ax = plt.gca()

        monthly_ret = perf.aggregate_returns(returns, 'monthly')
        monthly_ret = monthly_ret.unstack()
        monthly_ret = np.round(monthly_ret, 3)
        monthly_ret.rename(
            columns={1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
                     5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
                     9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'},
            inplace=True
        )

        sns.heatmap(
            monthly_ret.fillna(0) * 100.0,
            annot=True,
            fmt="0.1f",
            annot_kws={"size": 8},
            alpha=1.0,
            center=0.0,
            cbar=False,
            cmap=cm.RdYlGn,
            ax=ax, **kwargs)
        ax.set_title('Monthly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        ax.set_xlabel('')

        return ax


    def _plot_yearly_returns(self, stats, ax=None, **kwargs):
        """
        Plots a barplot of returns by year.
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        returns = stats['returns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.yaxis.grid(linestyle=':')

        yly_ret = perf.aggregate_returns(returns, 'yearly') * 100.0
        yly_ret.plot(ax=ax, kind="bar")
        ax.set_title('Yearly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        ax.xaxis.grid(False)

        return ax


    def _plot_txt_curve(self, stats, ax=None, **kwargs):
        """
        Outputs the statistics for the equity curve.
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        returns = stats["returns"]
        cum_returns = stats['cum_returns']
        positions = stats['positions']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

        tot_ret = cum_returns[-1] - 1.0
        cagr = perf.create_cagr(cum_returns)
        sharpe = perf.create_sharpe_ratio(returns)
        sortino = perf.create_sortino_ratio(returns)
        rsq = perf.rsquared(range(cum_returns.shape[0]), cum_returns)
        dd, dd_max, dd_dur = perf.create_drawdowns(cum_returns)
        trd_yr = positions.shape[0] / (((returns.index[-1] - returns.index[0]).days + 1) / 365.0)

        ax.text(0.25, 8.9, 'Total Return', fontsize=8)
        ax.text(7.50, 8.9, '{:.0%}'.format(tot_ret), fontweight='bold', horizontalalignment='right', fontsize=8)

        ax.text(0.25, 7.9, 'CAGR', fontsize=8)
        ax.text(7.50, 7.9, '{:.2%}'.format(cagr), fontweight='bold', horizontalalignment='right', fontsize=8)

        ax.text(0.25, 6.9, 'Sharpe Ratio', fontsize=8)
        ax.text(7.50, 6.9, '{:.2f}'.format(sharpe), fontweight='bold', horizontalalignment='right', fontsize=8)

        ax.text(0.25, 5.9, 'Sortino Ratio', fontsize=8)
        ax.text(7.50, 5.9, '{:.2f}'.format(sortino), fontweight='bold', horizontalalignment='right', fontsize=8)

        ax.text(0.25, 4.9, 'Annual Volatility', fontsize=8)
        ax.text(7.50, 4.9, '{:.2%}'.format(returns.std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=8)

        ax.text(0.25, 3.9, 'R-Squared', fontsize=8)
        ax.text(7.50, 3.9, '{:.2f}'.format(rsq), fontweight='bold', horizontalalignment='right', fontsize=8)

        ax.text(0.25, 2.9, 'Max Daily Drawdown', fontsize=8)
        ax.text(7.50, 2.9, '{:.2%}'.format(dd_max), color='red', fontweight='bold', horizontalalignment='right', fontsize=8)

        ax.text(0.25, 1.9, 'Max Drawdown Duration', fontsize=8)
        ax.text(7.50, 1.9, '{:.0f}'.format(dd_dur), fontweight='bold', horizontalalignment='right', fontsize=8)

        ax.text(0.25, 0.9, 'Trades per Year', fontsize=8)
        ax.text(7.50, 0.9, '{:.1f}'.format(trd_yr), fontweight='bold', horizontalalignment='right', fontsize=8)
        ax.set_title('Curve', fontweight='bold')

        if self.benchmark is not None:
            returns_b = stats['returns_b']
            equity_b = stats['cum_returns_b']
            tot_ret_b = equity_b[-1] - 1.0
            cagr_b = perf.create_cagr(equity_b)
            sharpe_b = perf.create_sharpe_ratio(returns_b)
            sortino_b = perf.create_sortino_ratio(returns_b)
            rsq_b = perf.rsquared(range(equity_b.shape[0]), equity_b)
            dd_b, dd_max_b, dd_dur_b = perf.create_drawdowns(equity_b)

            ax.text(9.75, 8.9, '{:.0%}'.format(tot_ret_b), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(9.75, 7.9, '{:.2%}'.format(cagr_b), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(9.75, 6.9, '{:.2f}'.format(sharpe_b), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(9.75, 5.9, '{:.2f}'.format(sortino_b), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(9.75, 4.9, '{:.2%}'.format(returns_b.std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(9.75, 3.9, '{:.2f}'.format(rsq_b), fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(9.75, 2.9, '{:.2%}'.format(dd_max_b), color='red', fontweight='bold', horizontalalignment='right', fontsize=8)
            ax.text(9.75, 1.9, '{:.0f}'.format(dd_dur_b), fontweight='bold', horizontalalignment='right', fontsize=8)

            ax.set_title('Curve vs. Benchmark', fontweight='bold')

        ax.grid(False)
        ax.spines['top'].set_linewidth(2.0)
        ax.spines['bottom'].set_linewidth(2.0)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.set_ylabel('')
        ax.set_xlabel('')

        ax.axis([0, 10, 0, 10])
        return ax


    def _plot_txt_trade(self, stats, ax=None, **kwargs):
        """
        Outputs the statistics for the trades.
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        if ax is None:
            ax = plt.gca()

        pos = stats['positions']

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

        num_trades = pos.shape[0]
        win_pct = pos[pos["trade_pct"] > 0].shape[0] / float(num_trades)
        win_pct_str = '{:.0%}'.format(win_pct)
        avg_trd_pct = '{:.2%}'.format(np.mean(pos["trade_pct"]))
        avg_win_pct = '{:.2%}'.format(np.mean(pos[pos["trade_pct"] > 0]["trade_pct"]))
        avg_loss_pct = '{:.2%}'.format(np.mean(pos[pos["trade_pct"] <= 0]["trade_pct"]))
        max_win_pct = '{:.2%}'.format(np.max(pos["trade_pct"]))
        max_loss_pct = '{:.2%}'.format(np.min(pos["trade_pct"]))
        max_loss_dt = pos[pos["trade_pct"] == np.min(pos["trade_pct"])].entry_date.values[0]
        max_loss_dt = pd.to_datetime(str(max_loss_dt)).strftime('%Y-%m-%d')
        avg_dit = '{:.2f}'.format(np.mean(pos.time_in_pos))

        ax.text(0.5, 8.9, 'Trade Winning %', fontsize=8)
        ax.text(9.5, 8.9, win_pct_str, fontsize=8, fontweight='bold', horizontalalignment='right')

        ax.text(0.5, 7.9, 'Average Trade %', fontsize=8)
        ax.text(9.5, 7.9, avg_trd_pct, fontsize=8, fontweight='bold', horizontalalignment='right')

        ax.text(0.5, 6.9, 'Average Win %', fontsize=8)
        ax.text(9.5, 6.9, avg_win_pct, fontsize=8, fontweight='bold', color='green', horizontalalignment='right')

        ax.text(0.5, 5.9, 'Average Loss %', fontsize=8)
        ax.text(9.5, 5.9, avg_loss_pct, fontsize=8, fontweight='bold', color='red', horizontalalignment='right')

        ax.text(0.5, 4.9, 'Best Trade %', fontsize=8)
        ax.text(9.5, 4.9, max_win_pct, fontsize=8, fontweight='bold', color='green', horizontalalignment='right')

        ax.text(0.5, 3.9, 'Worst Trade %', fontsize=8)
        ax.text(9.5, 3.9, max_loss_pct, color='red', fontsize=8, fontweight='bold', horizontalalignment='right')

        ax.text(0.5, 2.9, 'Worst Trade Date', fontsize=8)
        ax.text(9.5, 2.9, max_loss_dt, fontsize=8, fontweight='bold', horizontalalignment='right')

        ax.text(0.5, 1.9, 'Avg Days in Trade', fontsize=8)
        ax.text(9.5, 1.9, avg_dit, fontsize=8, fontweight='bold', horizontalalignment='right')

        ax.text(0.5, 0.9, 'Trades', fontsize=8)
        ax.text(9.5, 0.9, num_trades, fontsize=8, fontweight='bold', horizontalalignment='right')

        ax.set_title('Trade', fontweight='bold')
        ax.grid(False)
        ax.spines['top'].set_linewidth(2.0)
        ax.spines['bottom'].set_linewidth(2.0)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.set_ylabel('')
        ax.set_xlabel('')

        ax.axis([0, 10, 0, 10])
        return ax


    def _plot_txt_time(self, stats, ax=None, **kwargs):
        """
        Outputs the statistics for various time frames.
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        returns = stats['returns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

        mly_ret = perf.aggregate_returns(returns, 'monthly')
        yly_ret = perf.aggregate_returns(returns, 'yearly')

        mly_pct = mly_ret[mly_ret >= 0].shape[0] / float(mly_ret.shape[0])
        mly_avg_win_pct = np.mean(mly_ret[mly_ret >= 0])
        mly_avg_loss_pct = np.mean(mly_ret[mly_ret < 0])
        mly_max_win_pct = np.max(mly_ret)
        mly_max_loss_pct = np.min(mly_ret)
        yly_pct = yly_ret[yly_ret >= 0].shape[0] / float(yly_ret.shape[0])
        yly_max_win_pct = np.max(yly_ret)
        yly_max_loss_pct = np.min(yly_ret)

        ax.text(0.5, 8.9, 'Winning Months %', fontsize=8)
        ax.text(9.5, 8.9, '{:.0%}'.format(mly_pct), fontsize=8, fontweight='bold',
                horizontalalignment='right')

        ax.text(0.5, 7.9, 'Average Winning Month %', fontsize=8)
        ax.text(9.5, 7.9, '{:.2%}'.format(mly_avg_win_pct), fontsize=8, fontweight='bold',
                color='red' if mly_avg_win_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 6.9, 'Average Losing Month %', fontsize=8)
        ax.text(9.5, 6.9, '{:.2%}'.format(mly_avg_loss_pct), fontsize=8, fontweight='bold',
                color='red' if mly_avg_loss_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 5.9, 'Best Month %', fontsize=8)
        ax.text(9.5, 5.9, '{:.2%}'.format(mly_max_win_pct), fontsize=8, fontweight='bold',
                color='red' if mly_max_win_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 4.9, 'Worst Month %', fontsize=8)
        ax.text(9.5, 4.9, '{:.2%}'.format(mly_max_loss_pct), fontsize=8, fontweight='bold',
                color='red' if mly_max_loss_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 3.9, 'Winning Years %', fontsize=8)
        ax.text(9.5, 3.9, '{:.0%}'.format(yly_pct), fontsize=8, fontweight='bold',
                horizontalalignment='right')

        ax.text(0.5, 2.9, 'Best Year %', fontsize=8)
        ax.text(9.5, 2.9, '{:.2%}'.format(yly_max_win_pct), fontsize=8,
                fontweight='bold', color='red' if yly_max_win_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 1.9, 'Worst Year %', fontsize=8)
        ax.text(9.5, 1.9, '{:.2%}'.format(yly_max_loss_pct), fontsize=8,
                fontweight='bold', color='red' if yly_max_loss_pct < 0 else 'green',
                horizontalalignment='right')

        # ax.text(0.5, 0.9, 'Positive 12 Month Periods', fontsize=8)
        # ax.text(9.5, 0.9, num_trades, fontsize=8, fontweight='bold', horizontalalignment='right')

        ax.set_title('Time', fontweight='bold')
        ax.grid(False)
        ax.spines['top'].set_linewidth(2.0)
        ax.spines['bottom'].set_linewidth(2.0)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.set_ylabel('')
        ax.set_xlabel('')

        ax.axis([0, 10, 0, 10])
        return ax


    def plot_results(self, filename=None):
        """
        Plot the Tearsheet
        """
        rc = {
            'lines.linewidth': 1.0,
            'axes.facecolor': '0.995',
            'figure.facecolor': '0.97',
            'font.family': 'serif',
            'font.serif': 'Ubuntu',
            'font.monospace': 'Ubuntu Mono',
            'font.size': 10,
            'axes.labelsize': 10,
            'axes.labelweight': 'bold',
            'axes.titlesize': 10,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 10,
            'figure.titlesize': 12
        }
        sns.set_context(rc)
        sns.set_style("whitegrid")
        sns.set_palette("deep", desat=.6)

        vertical_sections = 5
        fig = plt.figure(figsize=(10, vertical_sections * 3))
        fig.suptitle(self.title, y=0.96)
        gs = gridspec.GridSpec(vertical_sections, 3, wspace=0.25, hspace=0.5)

        stats = self.get_results()

        ax_equity = plt.subplot(gs[:2, :])
        ax_drawdown = plt.subplot(gs[2, :])
        ax_monthly_returns = plt.subplot(gs[3, :2])
        ax_yearly_returns = plt.subplot(gs[3, 2])
        ax_txt_curve = plt.subplot(gs[4, 0])
        ax_txt_trade = plt.subplot(gs[4, 1])
        ax_txt_time = plt.subplot(gs[4, 2])

        self._plot_equity(stats, ax=ax_equity)
        self._plot_drawdown(stats, ax=ax_drawdown)
        self._plot_monthly_returns(stats, ax=ax_monthly_returns)
        self._plot_yearly_returns(stats, ax=ax_yearly_returns)
        self._plot_txt_curve(stats, ax=ax_txt_curve)
        self._plot_txt_trade(stats, ax=ax_txt_trade)
        self._plot_txt_time(stats, ax=ax_txt_time)

        # Plot the figure
        plt.show()

        if filename is not None:
            fig.savefig(filename)


    def save(self, filename=""):
        now = datetime.now()

        # Save tearsheet figure
        filename = "tearsheet_" + now.strftime("%Y-%m-%d") + ".png"
        filename = os.path.expanduser(os.path.join(self.config.OUTPUT_DIR, filename))
        self.plot_results(filename)

        # Save the list of positions
        filename = "positions_" + now.strftime("%Y-%m-%d") + ".csv"
        filename = os.path.expanduser(os.path.join(self.config.OUTPUT_DIR, filename))
        pos = self._get_positions()
        keys = pos[0].keys()
        with open(filename, 'wb') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(pos)

        # Save the equity stats
        filename = "equity_" + now.strftime("%Y-%m-%d") + ".csv"
        filename = os.path.expanduser(os.path.join(self.config.OUTPUT_DIR, filename))
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.equity_file[0].keys())
            writer.writeheader()
            for row in self.equity_file:
                writer.writerow(row)
