# config.py

import os

class Config:
    # Binance API Credentials
    # For live trading, set BINANCE_API_KEY and BINANCE_API_SECRET environment variables
    # For testnet trading, set BINANCE_API_KEY_TESTNET and BINANCE_API_SECRET_TESTNET environment variables
    BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "YOUR_DEFAULT_BINANCE_LIVE_API_KEY")
    BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET", "YOUR_DEFAULT_BINANCE_LIVE_API_SECRET")
    BINANCE_API_KEY_TESTNET = os.environ.get("BINANCE_API_KEY_TESTNET", "YOUR_DEFAULT_BINANCE_TESTNET_API_KEY")
    BINANCE_API_SECRET_TESTNET = os.environ.get("BINANCE_API_SECRET_TESTNET", "YOUR_DEFAULT_BINANCE_TESTNET_API_SECRET")

    # Set to True to use Binance Testnet, False for Live trading
    BINANCE_TESTNET = os.environ.get("BINANCE_TESTNET", "True").lower() in ('true', '1', 't')

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_USER = os.environ.get("DB_USER", "user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
    DB_NAME = os.environ.get("DB_NAME", "trading_db")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "trading_bot.log")

    # Risk Management Settings
    MAX_RISK_PER_TRADE = float(os.environ.get("MAX_RISK_PER_TRADE", 0.01)) # 1% of total balance
    MAX_CONCURRENT_TRADES = int(os.environ.get("MAX_CONCURRENT_TRADES", 5))
    INITIAL_BALANCE = float(os.environ.get("INITIAL_BALANCE", 10000.0)) # Used by RiskManager, actual balance comes from exchange

    # Trading Parameters
    DEFAULT_SYMBOL = os.environ.get("DEFAULT_SYMBOL", "BTCUSDT") # Default symbol for trading
    DEFAULT_KLINE_INTERVAL = os.environ.get("DEFAULT_KLINE_INTERVAL", "1h") # Default kline interval (e.g., 1m, 5m, 1h, 1d)


if __name__ == '__main__':
    # Example of accessing configuration values
    print(f"Binance Testnet Enabled: {Config.BINANCE_TESTNET}")
    if Config.BINANCE_TESTNET:
        print(f"Binance API Key (Testnet): {Config.BINANCE_API_KEY_TESTNET}")
    else:
        print(f"Binance API Key (Live): {Config.BINANCE_API_KEY}")

    print(f"Database Host: {Config.DB_HOST}")
    print(f"Log Level: {Config.LOG_LEVEL}")
    print(f"Max Risk Per Trade: {Config.MAX_RISK_PER_TRADE}")
    print(f"Default Symbol: {Config.DEFAULT_SYMBOL}")
    print(f"Default Kline Interval: {Config.DEFAULT_KLINE_INTERVAL}")
