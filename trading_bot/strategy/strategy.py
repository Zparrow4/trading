# trading_bot/strategy/strategy.py

import pandas as pd
from .indicator_calculator import IndicatorCalculator

class TradingStrategy:
    def __init__(self, data_df, short_ema_period=44, long_ema_period=200, sr_window=20):
        if not isinstance(data_df, pd.DataFrame):
            raise ValueError("data_df must be a pandas DataFrame.")
        required_cols = ['close'] # Base requirement
        if not all(col in data_df.columns for col in required_cols):
            raise ValueError(f"data_df must contain columns: {', '.join(required_cols)}.")

        self.data_df = data_df.copy()
        self.calculator = IndicatorCalculator(self.data_df) # Calculator gets its own copy
        self.short_ema_period = short_ema_period
        self.long_ema_period = long_ema_period
        self.sr_window = sr_window

    def generate_signals(self):
        self.data_df['ema_short'] = self.calculator.calculate_ema(window=self.short_ema_period)
        self.data_df['ema_long'] = self.calculator.calculate_ema(window=self.long_ema_period)

        self.data_df['support'] = self.calculator.calculate_rolling_low(window=self.sr_window)
        self.data_df['resistance'] = self.calculator.calculate_rolling_high(window=self.sr_window)

        self.data_df['signal'] = 0
        bullish_ema = self.data_df['ema_short'] > self.data_df['ema_long']
        bearish_ema = self.data_df['ema_short'] < self.data_df['ema_long']
        self.data_df.loc[bullish_ema, 'signal'] = 1
        self.data_df.loc[bearish_ema, 'signal'] = -1

        previous_signal = self.data_df['signal'].shift(1).fillna(0)
        self.data_df['position'] = 0

        # Buy crossover: previous signal was not 1 (i.e., was 0 or -1) and current signal is 1
        buy_crossover = (previous_signal != 1) & (self.data_df['signal'] == 1)
        self.data_df.loc[buy_crossover, 'position'] = 1

        # Sell crossover: previous signal was not -1 (i.e., was 0 or 1) and current signal is -1
        sell_crossover = (previous_signal != -1) & (self.data_df['signal'] == -1)
        self.data_df.loc[sell_crossover, 'position'] = -1

        return self.data_df

if __name__ == '__main__':
    periods = 60
    close_prices_main = [i + (i * 0.1 * (1 if i < periods/2 else -1)) for i in range(10, 10 + periods)]
    main_data = {
        'date': pd.date_range(start='2023-01-01', periods=periods, freq='D'),
        'close': close_prices_main,
        'high': [p + 0.5 for p in close_prices_main],
        'low': [p - 0.5 for p in close_prices_main]
    }
    main_sample_df_strat = pd.DataFrame(main_data).set_index('date')

    # Use smaller periods for example visibility
    strategy_main = TradingStrategy(main_sample_df_strat.copy(), short_ema_period=5, long_ema_period=10, sr_window=7)
    signals_df_main = strategy_main.generate_signals()
    print("Trading Signals (EMA Crossover with S/R):\n", signals_df_main.tail(15))
