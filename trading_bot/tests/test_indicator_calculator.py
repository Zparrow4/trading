# trading_bot/tests/test_indicator_calculator.py

import unittest
import pandas as pd
import numpy as np
from trading_bot.strategy.indicator_calculator import IndicatorCalculator

class TestIndicatorCalculator(unittest.TestCase):

    def setUp(self):
        self.data = {
            'open': [10, 11, 10.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5],
            'high': [10.5, 12.5, 11.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5],
            'low':  [9.5, 10.5, 10.0, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5],
            'close':[10, 12, 11, 13, 14, 15, 16, 17, 18, 19]
        }
        self.sample_df = pd.DataFrame(self.data)
        self.calculator = IndicatorCalculator(self.sample_df.copy())

    def test_constructor_errors(self):
        with self.assertRaisesRegex(ValueError, "data_df must be a pandas DataFrame"):
            IndicatorCalculator("not a dataframe")
        with self.assertRaisesRegex(ValueError, "data_df must contain a 'close' column"):
            IndicatorCalculator(pd.DataFrame({'not_close': [1,2,3]}))

    def test_calculate_sma_min_periods(self):
        sma_3 = self.calculator.calculate_sma(window=3)
        self.assertFalse(sma_3.isnull().any(), "SMA with min_periods=1 should not have NaNs for window < len(data)")
        self.assertAlmostEqual(sma_3.iloc[0], self.sample_df['close'].iloc[0]) # First value
        self.assertAlmostEqual(sma_3.iloc[1], self.sample_df['close'].iloc[:2].mean()) # Mean of first two

    def test_calculate_ema_min_periods(self):
        ema_3 = self.calculator.calculate_ema(window=3)
        self.assertFalse(ema_3.isnull().any(), "EMA with min_periods=1 should not have NaNs")
        self.assertAlmostEqual(ema_3.iloc[0], self.sample_df['close'].iloc[0])

    def test_calculate_rsi_edge_cases(self):
        # All prices same
        flat_df = pd.DataFrame({'close': [10] * 10})
        flat_calc = IndicatorCalculator(flat_df)
        rsi_flat = flat_calc.calculate_rsi(window=5)
        self.assertTrue(rsi_flat.iloc[1:].isnull().all() or (rsi_flat.iloc[1:] == 50).all(), "RSI for flat price should be NaN or neutral (e.g. 50), depending on exact 0/0 handling")


        # All prices increasing
        increasing_df = pd.DataFrame({'close': np.arange(10, 20)})
        increasing_calc = IndicatorCalculator(increasing_df)
        rsi_increasing = increasing_calc.calculate_rsi(window=5)
        # First RSI is NaN (due to diff). Subsequent are 100.
        self.assertTrue(np.isnan(rsi_increasing.iloc[0]))
        self.assertTrue((rsi_increasing.iloc[1:] == 100.0).all())

        # All prices decreasing
        decreasing_df = pd.DataFrame({'close': np.arange(20, 10, -1)})
        decreasing_calc = IndicatorCalculator(decreasing_df)
        rsi_decreasing = decreasing_calc.calculate_rsi(window=5)
        self.assertTrue(np.isnan(rsi_decreasing.iloc[0]))
        self.assertTrue((rsi_decreasing.iloc[1:] == 0.0).all())

    def test_calculate_rolling_high(self):
        rh_3 = self.calculator.calculate_rolling_high(window=3)
        self.assertFalse(rh_3.isnull().any())
        self.assertEqual(rh_3.iloc[0], self.sample_df['high'].iloc[0])
        self.assertEqual(rh_3.iloc[2], self.sample_df['high'].iloc[:3].max())
        self.assertEqual(rh_3.iloc[5], self.sample_df['high'].iloc[3:6].max())

    def test_calculate_rolling_low(self):
        rl_3 = self.calculator.calculate_rolling_low(window=3)
        self.assertFalse(rl_3.isnull().any())
        self.assertEqual(rl_3.iloc[0], self.sample_df['low'].iloc[0])
        self.assertEqual(rl_3.iloc[2], self.sample_df['low'].iloc[:3].min())
        self.assertEqual(rl_3.iloc[5], self.sample_df['low'].iloc[3:6].min())

    def test_rolling_uses_close_if_high_low_absent(self):
        df_only_close = pd.DataFrame({'close': self.sample_df['close']})
        calc_only_close = IndicatorCalculator(df_only_close.copy())
        rh_3 = calc_only_close.calculate_rolling_high(window=3)
        self.assertEqual(rh_3.iloc[2], df_only_close['close'].iloc[:3].max())
        rl_3 = calc_only_close.calculate_rolling_low(window=3)
        self.assertEqual(rl_3.iloc[2], df_only_close['close'].iloc[:3].min())

if __name__ == '__main__':
    unittest.main()
