# trading_bot/strategy/indicator_calculator.py

import pandas as pd
import numpy as np # For float('inf')

class IndicatorCalculator:
    def __init__(self, data_df):
        if not isinstance(data_df, pd.DataFrame):
            raise ValueError("data_df must be a pandas DataFrame.")
        if 'close' not in data_df.columns:
            raise ValueError("data_df must contain a 'close' column.")
        self.data_df = data_df.copy()

    def calculate_sma(self, window, column='close'):
        if column not in self.data_df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame for SMA.")
        return self.data_df[column].rolling(window=window, min_periods=min(window, 1)).mean()

    def calculate_ema(self, window, column='close'):
        if column not in self.data_df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame for EMA.")
        return self.data_df[column].ewm(span=window, adjust=False, min_periods=min(window, 1)).mean()

    def calculate_rsi(self, window=14, column='close'):
        if column not in self.data_df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame for RSI.")
        delta = self.data_df[column].diff()

        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=window, min_periods=1).mean()
        avg_loss = loss.rolling(window=window, min_periods=1).mean()

        rs = avg_gain / avg_loss
        # Handle division by zero: if avg_loss is 0, RS is infinite (or NaN if avg_gain is also 0)
        rs[avg_loss == 0] = np.inf
        # If both avg_gain and avg_loss are 0, rs will be nan (0/0), then rsi also nan. This is acceptable.

        rsi = 100.0 - (100.0 / (1.0 + rs))

        # If avg_gain > 0 and avg_loss == 0, rs is inf, rsi is 100.
        # If avg_gain == 0 and avg_loss > 0, rs is 0, rsi is 0.
        return rsi

    def calculate_rolling_high(self, window, column='high'):
        # Default to 'high' column, fallback to 'close' if 'high' not present
        col_to_use = column if column in self.data_df.columns else 'close'
        if 'high' in self.data_df.columns: # Prefer 'high' if available
             col_to_use = 'high'
        elif 'close' not in self.data_df.columns : # Must have at least 'close'
            raise ValueError(f"Neither 'high' nor 'close' column found for rolling high.")

        return self.data_df[col_to_use].rolling(window=window, min_periods=min(window, 1)).max()

    def calculate_rolling_low(self, window, column='low'):
        # Default to 'low' column, fallback to 'close' if 'low' not present
        col_to_use = column if column in self.data_df.columns else 'close'
        if 'low' in self.data_df.columns: # Prefer 'low' if available
            col_to_use = 'low'
        elif 'close' not in self.data_df.columns:
             raise ValueError(f"Neither 'low' nor 'close' column found for rolling low.")

        return self.data_df[col_to_use].rolling(window=window, min_periods=min(window, 1)).min()

if __name__ == '__main__':
    raw_data = {
        'date': pd.to_datetime(['2023-01-%02d' % i for i in range(1, 11)]),
        'open': [i + 0.5 for i in range(10, 20)],
        'high': [i + 1.0 for i in range(10, 20)],
        'low': [i - 0.5 for i in range(10, 20)],
        'close': list(range(10, 20))
    }
    main_sample_df = pd.DataFrame(raw_data).set_index('date')
    main_calculator = IndicatorCalculator(main_sample_df.copy())
    print("Original Data:\n", main_sample_df)
    main_sample_df['ema5'] = main_calculator.calculate_ema(5)
    main_sample_df['support5'] = main_calculator.calculate_rolling_low(5)
    main_sample_df['resistance5'] = main_calculator.calculate_rolling_high(5)
    main_sample_df['rsi5'] = main_calculator.calculate_rsi(5)
    print("\nCalculated Indicators:\n", main_sample_df)
