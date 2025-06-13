# trading_bot/tests/test_binance_handler.py
import unittest
import os
from unittest.mock import patch, MagicMock, call
import pandas as pd
import logging

# Suppress specific logger output during tests for cleaner test results
logging.getLogger('trading_bot.data_handling.binance_handler').setLevel(logging.WARNING)

try:
    from trading_bot.data_handling.binance_handler import BinanceHandler
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException
except ImportError:
    # This block allows tests to be discovered even if imports fail,
    # though the tests themselves will likely fail if imports are broken.
    class BinanceHandler: pass
    class Client: # Minimal mock for constants
        KLINE_INTERVAL_1MINUTE = "1m"; KLINE_INTERVAL_1HOUR = "1h"
        SIDE_BUY = "BUY"; SIDE_SELL = "SELL"
        ORDER_TYPE_MARKET = "MARKET"; ORDER_TYPE_LIMIT = "LIMIT"; TIME_IN_FORCE_GTC = "GTC"
        API_TESTNET_URL = "https://testnet.binance.vision/api" # Example
    class BinanceAPIException(Exception): pass
    class BinanceOrderException(Exception): pass


@patch.dict(os.environ, {
    "BINANCE_API_KEY_TESTNET": "test_api_key_testnet",
    "BINANCE_API_SECRET_TESTNET": "test_api_secret_testnet",
    "BINANCE_API_KEY": "test_api_key_live",
    "BINANCE_API_SECRET": "test_api_secret_live",
})
class TestBinanceHandler(unittest.TestCase):

    def setUp(self):
        self.client_patcher = patch('trading_bot.data_handling.binance_handler.Client')
        self.MockBinanceClientClass = self.client_patcher.start()
        self.mock_binance_client_instance = self.MockBinanceClientClass.return_value

        # Default mock behaviors for the client instance
        self.mock_binance_client_instance.get_server_time.return_value = {'serverTime': int(pd.Timestamp.now().timestamp() * 1000)}
        self.mock_binance_client_instance.API_URL = Client.API_TESTNET_URL # Simulate testnet URL by default

    def tearDown(self):
        self.client_patcher.stop()

    def test_initialization_testnet(self):
        handler = BinanceHandler(testnet=True)
        self.assertTrue(handler.testnet)
        self.MockBinanceClientClass.assert_called_once_with(
            "test_api_key_testnet", "test_api_secret_testnet", testnet=True
        )
        self.assertEqual(handler.client, self.mock_binance_client_instance)

    def test_initialization_live(self):
        handler = BinanceHandler(testnet=False)
        self.assertFalse(handler.testnet)
        self.MockBinanceClientClass.assert_called_once_with(
            "test_api_key_live", "test_api_secret_live", testnet=False
        )

    def test_initialization_missing_keys_raises_valueerror(self):
        with patch.dict(os.environ, {}, clear=True): # No env vars
            with self.assertRaisesRegex(ValueError, "Binance API key and secret must be provided"):
                BinanceHandler(api_key=None, api_secret=None, testnet=True)

    def test_fetch_klines_success(self):
        handler = BinanceHandler(testnet=True)
        sample_data = [[1600000000000, '100', '110', '90', '105', '1000', 1600000059999, '105000', 10, '500', '52500', '0']]
        self.mock_binance_client_instance.get_klines.return_value = sample_data

        df = handler.fetch_klines('BTCUSDT', Client.KLINE_INTERVAL_1MINUTE, limit=1)

        self.mock_binance_client_instance.get_klines.assert_called_once_with(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=1)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(df['Open'].iloc[0], 100.0)

    def test_fetch_historical_klines_success(self):
        handler = BinanceHandler(testnet=True)
        sample_data = [[1600000000000, '100', '110', '90', '105', '1000', 1600000059999, '105000', 10, '500', '52500', '0']]
        self.mock_binance_client_instance.get_historical_klines.return_value = sample_data

        df = handler.fetch_klines('BTCUSDT', Client.KLINE_INTERVAL_1HOUR, limit=1, start_str="1 day ago UTC")

        self.mock_binance_client_instance.get_historical_klines.assert_called_once_with(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1HOUR, limit=1, start_str="1 day ago UTC", end_str=None)
        self.assertEqual(len(df), 1)

    def test_fetch_klines_api_exception(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.get_klines.side_effect = BinanceAPIException("API Error")
        df = handler.fetch_klines('BTCUSDT', Client.KLINE_INTERVAL_1MINUTE)
        self.assertTrue(df.empty)

    def test_get_account_balance_specific_asset(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.get_account.return_value = {
            'balances': [{'asset': 'USDT', 'free': '100.0', 'locked': '10.0'}]
        }
        balance = handler.get_account_balance('USDT')
        self.assertEqual(balance, {'free': 100.0, 'locked': 10.0})

    def test_get_account_balance_all_assets(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.get_account.return_value = {
            'balances': [
                {'asset': 'USDT', 'free': '100.0', 'locked': '10.0'},
                {'asset': 'BTC', 'free': '0.5', 'locked': '0.1'},
                {'asset': 'ETH', 'free': '0.0', 'locked': '0.0'} # Zero balance
            ]
        }
        balances = handler.get_account_balance()
        self.assertIn('USDT', balances)
        self.assertIn('BTC', balances)
        self.assertNotIn('ETH', balances) # Should not include zero balances
        self.assertEqual(balances['BTC'], {'free': 0.5, 'locked': 0.1})

    def test_create_market_order_testnet_validation(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.create_test_order.return_value = {"status": "test success"} # Mock response for test order

        response = handler.create_market_order('BTCUSDT', Client.SIDE_BUY, quantity=0.01)

        self.mock_binance_client_instance.create_test_order.assert_called_once()
        call_args = self.mock_binance_client_instance.create_test_order.call_args[1] # Get kwargs
        self.assertEqual(call_args['symbol'], 'BTCUSDT')
        self.assertEqual(call_args['side'], Client.SIDE_BUY)
        self.assertEqual(call_args['type'], Client.ORDER_TYPE_MARKET)
        self.assertEqual(call_args['quantity'], '0.01000000') # Check formatting
        self.assertEqual(response, {"status": "test success"})

    def test_create_limit_order_live(self):
        # For live, we expect create_order to be called
        handler = BinanceHandler(testnet=False) # This will use live keys
        self.mock_binance_client_instance.create_order.return_value = {"status": "live success"}

        response = handler.create_limit_order('ETHUSDT', Client.SIDE_SELL, quantity=1.5, price=2000)

        self.mock_binance_client_instance.create_order.assert_called_once()
        call_args = self.mock_binance_client_instance.create_order.call_args[1]
        self.assertEqual(call_args['symbol'], 'ETHUSDT')
        self.assertEqual(call_args['price'], '2000.00000000')
        self.assertEqual(call_args['quantity'], '1.50000000')
        self.assertEqual(response, {"status": "live success"})

    def test_create_oco_order_testnet(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.create_oco_order.return_value = {"status": "oco test success"}

        response = handler.create_oco_order(
            symbol='BNBUSDT', side=Client.SIDE_SELL, quantity=1,
            price=600, stop_price=580, stop_limit_price=579
        )
        self.mock_binance_client_instance.create_oco_order.assert_called_once()
        call_args = self.mock_binance_client_instance.create_oco_order.call_args[1]
        self.assertEqual(call_args['symbol'], 'BNBUSDT')
        self.assertEqual(call_args['price'], '600.00000000') # OCO uses create_oco_order directly
        self.assertEqual(response, {"status": "oco test success"})

    def test_get_order_status(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.get_order.return_value = {"symbol": "LTCUSDT", "status": "FILLED"}
        status = handler.get_order_status("LTCUSDT", "12345")
        self.mock_binance_client_instance.get_order.assert_called_once_with(symbol="LTCUSDT", orderId="12345", timestamp=unittest.mock.ANY)
        self.assertEqual(status, {"symbol": "LTCUSDT", "status": "FILLED"})

    def test_cancel_order(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.cancel_order.return_value = {"status": "CANCELED"}
        response = handler.cancel_order("ADAUSDT", "67890")
        self.mock_binance_client_instance.cancel_order.assert_called_once_with(symbol="ADAUSDT", orderId="67890", timestamp=unittest.mock.ANY)
        self.assertEqual(response, {"status": "CANCELED"})

    def test_get_open_orders(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.get_open_orders.return_value = [{"symbol": "XRPUSDT", "orderId": "111"}]
        orders = handler.get_open_orders(symbol="XRPUSDT")
        self.mock_binance_client_instance.get_open_orders.assert_called_once_with(symbol="XRPUSDT", timestamp=unittest.mock.ANY)
        self.assertEqual(len(orders), 1)

    def test_get_open_orders_all(self):
        handler = BinanceHandler(testnet=True)
        self.mock_binance_client_instance.get_open_orders.return_value = [{"symbol": "DOTUSDT", "orderId": "222"}]
        orders = handler.get_open_orders() # No symbol
        self.mock_binance_client_instance.get_open_orders.assert_called_once_with(timestamp=unittest.mock.ANY)
        self.assertEqual(len(orders), 1)

if __name__ == '__main__':
    unittest.main()
