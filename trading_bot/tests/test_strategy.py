# trading_bot/tests/test_strategy.py

import unittest
import pandas as pd
import numpy as np
from trading_bot.strategy.strategy import TradingStrategy

class TestTradingStrategy(unittest.TestCase):

    def _create_test_df(self, num_periods=40):
        # Creates a DataFrame with a simple crossover pattern
        prices = np.concatenate([
            np.linspace(20, 30, num_periods // 2), # Trend up
            np.linspace(30, 20, num_periods - (num_periods // 2)) # Trend down
        ])
        data = {
            'date': pd.date_range(start='2023-01-01', periods=num_periods, freq='D'),
            'close': prices,
            'high': prices + 0.5,
            'low': prices - 0.5
        }
        return pd.DataFrame(data).set_index('date')

    def test_generate_signals_columns_exist(self):
        df = self._create_test_df()
        strategy = TradingStrategy(df, short_ema_period=5, long_ema_period=10, sr_window=5)
        signals_df = strategy.generate_signals()
        expected_cols = ['ema_short', 'ema_long', 'support', 'resistance', 'signal', 'position']
        for col in expected_cols:
            self.assertIn(col, signals_df.columns, f"Column '{col}' missing.")

    def test_signal_and_position_logic(self):
        df = self._create_test_df(num_periods=50) # Longer period for EMAs to cross
        # Use EMA periods that are likely to cross with the generated data
        strategy = TradingStrategy(df, short_ema_period=10, long_ema_period=20, sr_window=10)
        signals_df = strategy.generate_signals()

        # Check for at least one buy signal (signal == 1)
        self.assertTrue((signals_df['signal'] == 1).any(), "No buy signal (signal=1) found.")
        # Check for at least one sell signal (signal == -1)
        self.assertTrue((signals_df['signal'] == -1).any(), "No sell signal (signal=-1) found.")

        # Check for at least one buy position (position == 1)
        self.assertTrue((signals_df['position'] == 1).any(), "No buy position (position=1) entry found.")
        # Check for at least one sell position (position == -1)
        self.assertTrue((signals_df['position'] == -1).any(), "No sell position (position=-1) entry found.")

        # Verify buy position logic:
        # When position is 1, signal must be 1.
        # The signal at the previous step must have been 0 or -1.
        buy_entries = signals_df[signals_df['position'] == 1]
        if not buy_entries.empty:
            for idx, row in buy_entries.iterrows():
                self.assertEqual(row['signal'], 1, f"At buy entry {idx}, signal should be 1.")
                loc = signals_df.index.get_loc(idx)
                if loc > 0:
                    prev_signal = signals_df['signal'].iloc[loc - 1]
                    self.assertIn(prev_signal, [0, -1], f"Signal before buy entry at {idx} was not 0 or -1.")

        # Verify sell position logic:
        sell_entries = signals_df[signals_df['position'] == -1]
        if not sell_entries.empty:
            for idx, row in sell_entries.iterrows():
                self.assertEqual(row['signal'], -1, f"At sell entry {idx}, signal should be -1.")
                loc = signals_df.index.get_loc(idx)
                if loc > 0:
                    prev_signal = signals_df['signal'].iloc[loc - 1]
                    self.assertIn(prev_signal, [0, 1], f"Signal before sell entry at {idx} was not 0 or 1.")

    def test_sr_values_within_bounds(self):
        df = self._create_test_df()
        strategy = TradingStrategy(df, short_ema_period=5, long_ema_period=10, sr_window=5)
        signals_df = strategy.generate_signals()

        # After the initial SR window, support <= low and resistance >= high
        stable_sr_df = signals_df.iloc[strategy.sr_window -1 :] # -1 because window includes current bar
        self.assertTrue((stable_sr_df['support'] <= stable_sr_df['low']).all())
        self.assertTrue((stable_sr_df['resistance'] >= stable_sr_df['high']).all())

if __name__ == '__main__':
    unittest.main()
