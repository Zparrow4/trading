# main.py

import time
import pandas as pd
from binance.client import Client # For KLINE_INTERVAL constants

from data_handling.binance_handler import BinanceHandler
from strategy.strategy import TradingStrategy
from trading_logic.order_executor import OrderExecutor
from trading_logic.risk_manager import RiskManager
from utils.logger import setup_logger
from config import Config

class TradingBot:
    def __init__(self):
        self.logger = setup_logger(log_file=Config.LOG_FILE, level=Config.LOG_LEVEL)
        self.logger.info("Initializing Trading Bot...")

        if Config.BINANCE_TESTNET:
            api_key_to_use = Config.BINANCE_API_KEY_TESTNET
            api_secret_to_use = Config.BINANCE_API_SECRET_TESTNET
        else:
            api_key_to_use = Config.BINANCE_API_KEY
            api_secret_to_use = Config.BINANCE_API_SECRET

        self.data_fetcher = BinanceHandler(
            api_key=api_key_to_use,
            api_secret=api_secret_to_use,
            testnet=Config.BINANCE_TESTNET
        )
        # TODO: OrderExecutor needs refactoring to use BinanceHandler or initialize its own client
        # For now, it uses dummy keys which won't work for actual Binance execution.
        self.order_executor = OrderExecutor(api_key="DUMMY_KEY", secret_key="DUMMY_SECRET")
        self.risk_manager = RiskManager(balance=Config.INITIAL_BALANCE, max_risk_per_trade=Config.MAX_RISK_PER_TRADE)

        self.symbol = Config.DEFAULT_SYMBOL
        self.kline_interval = Config.DEFAULT_KLINE_INTERVAL # e.g., Client.KLINE_INTERVAL_1HOUR
        self.trade_history = []

    def run_trading_loop(self):
        self.logger.info("Starting trading loop...")
        while True:
            try:
                # 1. Fetch data
                self.logger.info(f"Fetching klines for {self.symbol}, interval {self.kline_interval}...")
                # Fetch recent klines for simulation (e.g., last 100)
                # For live, you might fetch fewer, more frequently, or use websockets.
                klines_df = self.data_fetcher.fetch_klines(
                    symbol=self.symbol,
                    interval=self.kline_interval,
                    limit=100 # Adjust as needed for strategy lookback
                )

                if klines_df.empty:
                    self.logger.warning("No kline data fetched. Skipping this iteration.")
                    time.sleep(60) # Wait before retrying
                    continue

                # Rename 'Close' to 'close' for compatibility with existing Strategy class
                klines_df.rename(columns={'Close': 'close', 'Open_Time': 'date'}, inplace=True)
                klines_df.set_index('date', inplace=True) # Strategy expects date index

                # Use the latest kline as the current tick for decision making in this simulation
                # A real strategy might use more historical data from klines_df
                current_tick_data = klines_df.iloc[[-1]]

                # 2. Generate trading signals
                # Pass a copy of the relevant part of klines_df to the strategy
                # The strategy might require more than just the last tick for indicator calculation
                # For this example, TradingStrategy is initialized with the single current_tick_data,
                # but it might need to be adjusted if strategy requires longer series.
                # The current TradingStrategy calculates SMAs based on the df it receives.
                # If current_tick_data only has 1 row, SMAs will be NaN or same as close.
                # Let's pass a larger df to strategy if it's designed to calculate indicators itself.

                # For the current strategy, it calculates indicators on the passed dataframe.
                # So, we should pass a dataframe long enough for indicators to be meaningful.
                # If klines_df has enough data, use it. Otherwise, current_tick_data is a fallback.
                data_for_strategy = klines_df # Strategy will use this to calculate indicators

                self.logger.info("Generating trading signals...")
                trading_strategy = TradingStrategy(data_for_strategy)
                signals_df = trading_strategy.generate_signals()

                if signals_df.empty or 'positions' not in signals_df.columns:
                    self.logger.info("No new trading signals generated.")
                else:
                    latest_signal = signals_df.iloc[-1]
                    if latest_signal['positions'] == 1:  # Buy signal
                        self.handle_buy_signal(latest_signal)
                    elif latest_signal['positions'] == -1:  # Sell signal
                        self.handle_sell_signal(latest_signal)

                self.logger.info("Waiting for the next trading interval...")
                time.sleep(300)  # Wait for 5 minutes (adjust as needed)

            except Exception as e:
                self.logger.error(f"An error occurred in the trading loop: {e}", exc_info=True)
                time.sleep(60) # Wait a bit before retrying after an error

    def handle_buy_signal(self, signal_data):
        entry_price = signal_data['close'] # Assuming 'close' is the entry price
        stop_loss_price = entry_price * 0.98 # Example: 2% stop loss

        if self.risk_manager.check_trade_limit(len(self.trade_history), Config.MAX_CONCURRENT_TRADES):
            position_size = self.risk_manager.calculate_position_size(entry_price, stop_loss_price)
            if position_size > 0:
                self.logger.info(f"Executing BUY order for {position_size} of {self.symbol} at {entry_price}")
                order_result = self.order_executor.execute_order(self.symbol, "buy", position_size, price=entry_price)
                self.trade_history.append({"type": "buy", "price": entry_price, "quantity": position_size, "status": order_result.get("status")})
                self.logger.info(f"BUY order executed: {order_result}")
            else:
                self.logger.info("Buy signal received, but position size is zero. No order placed.")
        else:
            self.logger.info("Buy signal received, but max concurrent trades limit reached.")

    def handle_sell_signal(self, signal_data):
        # For simplicity, assume selling existing holdings if any
        # A more complex logic would involve checking current portfolio
        if any(trade['type'] == 'buy' and trade['status'] == 'success' for trade in self.trade_history): # Basic check if we have something to sell
            sell_price = signal_data['close'] # Assuming 'close' is the sell price
            # Determine quantity to sell (e.g., all shares of this symbol)
            quantity_to_sell = sum(trade['quantity'] for trade in self.trade_history if trade['type'] == 'buy' and trade['status'] == 'success' and trade.get('symbol') == self.symbol) # Simplified

            if quantity_to_sell > 0:
                self.logger.info(f"Executing SELL order for {quantity_to_sell} of {self.symbol} at {sell_price}")
                order_result = self.order_executor.execute_order(self.symbol, "sell", quantity_to_sell, price=sell_price)
                # Update trade history (e.g., mark as sold or remove)
                self.trade_history = [trade for trade in self.trade_history if not (trade['type'] == 'buy' and trade.get('symbol') == self.symbol)] # Simplified
                self.logger.info(f"SELL order executed: {order_result}")
            else:
                self.logger.info("Sell signal received, but no quantity to sell or already sold.")
        else:
            self.logger.info("Sell signal received, but no active buy positions to sell for this symbol.")


if __name__ == "__main__":
    bot = TradingBot()
    try:
        bot.run_trading_loop()
    except KeyboardInterrupt:
        bot.logger.info("Trading bot stopped by user.")
    except Exception as e:
        bot.logger.critical(f"Critical error causing bot to stop: {e}", exc_info=True)
