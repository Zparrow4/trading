# trading_bot/data_handling/binance_handler.py

import os
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import pandas as pd
import time

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers: # Prevent duplicate handlers if reloaded
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()] # Explicitly add a handler
    )

class BinanceHandler:
    def __init__(self, api_key=None, api_secret=None, testnet=False):
        self.testnet = testnet
        env_prefix = "BINANCE_API"
        key_var = f"{env_prefix}_KEY{'_TESTNET' if testnet else ''}"
        secret_var = f"{env_prefix}_SECRET{'_TESTNET' if testnet else ''}"

        self.api_key = api_key if api_key else os.environ.get(key_var)
        self.api_secret = api_secret if api_secret else os.environ.get(secret_var)

        if not self.api_key or not self.api_secret:
            logger.error(f"Binance API key ({key_var}) and secret ({secret_var}) are required.")
            raise ValueError(f"Binance API key and secret must be provided via args or env vars: {key_var}, {secret_var}")

        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        logger.info(f"Binance client initialized. Testnet: {self.testnet}. API URL: {self.client.API_URL}")

    def _get_timestamp(self):
        # Using simple local timestamp. For production, consider server time synchronization.
        return int(time.time() * 1000)

    def fetch_klines(self, symbol, interval, limit=500, start_str=None, end_str=None):
        try:
            logger.info(f"Fetching klines for {symbol}, interval {interval}, limit {limit}, start: {start_str}, end: {end_str}")
            if start_str:
                klines_data = self.client.get_historical_klines(symbol, interval, start_str=start_str, end_str=end_str, limit=limit)
            else:
                klines_data = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)

            if not klines_data:
                logger.warning(f"No kline data for {symbol}, interval {interval}.")
                return pd.DataFrame()

            df = pd.DataFrame(klines_data, columns=[
                'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades',
                'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume', 'Ignore'
            ])

            num_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote_Asset_Volume',
                        'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume']
            df[num_cols] = df[num_cols].apply(pd.to_numeric, errors='coerce')

            df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
            df['Close_Time'] = pd.to_datetime(df['Close_Time'], unit='ms')

            logger.info(f"Fetched {len(df)} klines for {symbol}")
            return df[['Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time', 'Number_of_Trades']]
        except BinanceAPIException as e:
            logger.error(f"API Error fetching klines for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching klines for {symbol}: {e}")
        return pd.DataFrame()

    def get_account_balance(self, asset=None):
        try:
            logger.info(f"Fetching account balance. Asset: {asset or 'All'}")
            acc_info = self.client.get_account(timestamp=self._get_timestamp())
            balances = {}
            if 'balances' in acc_info:
                for item in acc_info['balances']:
                    if float(item['free']) > 0 or float(item['locked']) > 0:
                        balances[item['asset']] = {'free': float(item['free']), 'locked': float(item['locked'])}
                if asset:
                    return balances.get(asset, {'free': 0.0, 'locked': 0.0})
                return balances
            else:
                logger.error("Key 'balances' not in account_info.")
                return None
        except BinanceAPIException as e:
            logger.error(f"API Error fetching balance: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching balance: {e}")
        return None

    def _create_generic_order(self, params):
        logger.info(f"Creating order with params: { {k:v for k,v in params.items() if k != 'timestamp'} }")
        try:
            # python-binance create_order handles testnet internally if self.client was initialized with testnet=True
            # For explicit test orders that don't execute, use self.client.create_test_order(**params)
            if self.testnet:
                 # Using create_test_order to prevent actual order placement on testnet by default
                 # This validates parameters but doesn't execute.
                 # If actual execution on testnet is desired, switch to self.client.create_order
                logger.warning("Using create_test_order for testnet. Order will be validated but not executed.")
                order_response = self.client.create_test_order(**params)
            else:
                order_response = self.client.create_order(**params) # Live order

            logger.info(f"Order creation attempt successful: {order_response}")
            return order_response
        except BinanceAPIException as e:
            logger.error(f"API Error creating order: {e}")
        except BinanceOrderException as e:
            logger.error(f"Order Exception creating order: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating order: {e}")
        return None

    def _format_price(self, symbol, price):
        # This is a placeholder. For robust price formatting,
        # you'd fetch symbol info (client.get_symbol_info(symbol))
        # and use its tickSize to determine correct decimal places.
        # Example: return f"{float(price):.{precision}f}"
        return f"{float(price):.8f}".rstrip('0').rstrip('.') # Generic formatting

    def _format_quantity(self, symbol, quantity):
        # Placeholder similar to _format_price. Use stepSize from symbol info.
        return f"{float(quantity):.8f}".rstrip('0').rstrip('.') # Generic formatting

    def create_market_order(self, symbol, side, quantity=None, quote_order_qty=None):
        if quantity is None and quote_order_qty is None:
            raise ValueError("For MARKET order, either quantity or quote_order_qty must be specified.")

        params = {'symbol': symbol, 'side': side, 'type': Client.ORDER_TYPE_MARKET, 'timestamp': self._get_timestamp()}
        if quote_order_qty is not None:
            params['quoteOrderQty'] = self._format_quantity(symbol, quote_order_qty) # Format appropriately
        elif quantity is not None:
            params['quantity'] = self._format_quantity(symbol, quantity)
        return self._create_generic_order(params)

    def create_limit_order(self, symbol, side, quantity, price, time_in_force=Client.TIME_IN_FORCE_GTC):
        params = {
            'symbol': symbol, 'side': side, 'type': Client.ORDER_TYPE_LIMIT,
            'quantity': self._format_quantity(symbol, quantity),
            'price': self._format_price(symbol, price),
            'timeInForce': time_in_force, 'timestamp': self._get_timestamp()
        }
        return self._create_generic_order(params)

    def create_oco_order(self, symbol, side, quantity, price, stop_price, stop_limit_price,
                         list_client_order_id=None, limit_client_order_id=None,
                         stop_client_order_id=None, stop_limit_time_in_force=Client.TIME_IN_FORCE_GTC):
        params = {
            'symbol': symbol, 'side': side, 'quantity': self._format_quantity(symbol, quantity),
            'price': self._format_price(symbol, price), # Take profit limit price
            'stopPrice': self._format_price(symbol, stop_price), # Stop loss trigger price
            'stopLimitPrice': self._format_price(symbol, stop_limit_price), # Stop loss execution limit price
            'stopLimitTimeInForce': stop_limit_time_in_force,
            'timestamp': self._get_timestamp()
        }
        if list_client_order_id: params['listClientOrderId'] = list_client_order_id
        if limit_client_order_id: params['limitClientOrderId'] = limit_client_order_id
        if stop_client_order_id: params['stopClientOrderId'] = stop_client_order_id

        logger.info(f"Attempting to create OCO order with params: {params}")
        try:
            # OCO orders have a specific method in python-binance
            # It should respect the testnet flag on the client object.
            order_response = self.client.create_oco_order(**{k: v for k, v in params.items() if v is not None})
            logger.info(f"OCO {side} order creation attempt successful: {order_response}")
            return order_response
        except BinanceAPIException as e:
            logger.error(f"API Error creating OCO order for {symbol}: {e}")
        except BinanceOrderException as e:
            logger.error(f"Order Exception creating OCO order for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating OCO order for {symbol}: {e}")
        return None

    def get_order_status(self, symbol, order_id):
        try:
            logger.info(f"Fetching status for order {order_id} on {symbol}")
            order = self.client.get_order(symbol=symbol, orderId=order_id, timestamp=self._get_timestamp())
            return order
        except BinanceAPIException as e:
            logger.error(f"API Error fetching status for order {order_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching status for order {order_id}: {e}")
        return None

    def cancel_order(self, symbol, order_id):
        try:
            logger.info(f"Cancelling order {order_id} on {symbol}")
            result = self.client.cancel_order(symbol=symbol, orderId=order_id, timestamp=self._get_timestamp())
            return result
        except BinanceAPIException as e:
            logger.error(f"API Error cancelling order {order_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error cancelling order {order_id}: {e}")
        return None

    def get_open_orders(self, symbol=None):
        try:
            logger.info(f"Fetching open orders for {symbol or 'all symbols'}")
            params = {'timestamp': self._get_timestamp()}
            if symbol: params['symbol'] = symbol
            return self.client.get_open_orders(**params)
        except BinanceAPIException as e:
            logger.error(f"API Error fetching open orders: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching open orders: {e}")
        return None

if __name__ == '__main__':
    logging.info("--- Binance Handler Example Usage ---")
    # For this example to run, set env vars:
    # BINANCE_API_KEY_TESTNET, BINANCE_API_SECRET_TESTNET
    # To run against live (NOT RECOMMENDED HERE), set BINANCE_API_KEY, BINANCE_API_SECRET and change use_testnet to False.
    current_use_testnet = True

    try:
        handler = BinanceHandler(testnet=current_use_testnet)
        logger.info(f"Handler initialized for {'Testnet' if current_use_testnet else 'Live API'}.")

        logger.info("1. Fetching Klines for BTCUSDT...")
        klines_df = handler.fetch_klines('BTCUSDT', Client.KLINE_INTERVAL_1MINUTE, limit=3)
        if not klines_df.empty:
            print("Recent BTCUSDT klines:\n", klines_df.head())
        else:
            print("No klines fetched for BTCUSDT.")

        logger.info("2. Fetching USDT account balance...")
        balance_usdt = handler.get_account_balance(asset='USDT')
        if balance_usdt:
            print("USDT Balance:", balance_usdt)
        else:
            print("Could not fetch USDT balance or it's zero.")

        if current_use_testnet:
            logger.warning("Order examples will run using create_test_order (validation only) or against testnet endpoints.")

            logger.info("3. Example: Market Buy (Test Order - Validation only)")
            # Test order for $15 USDT worth of BTC. Min notional for BTCUSDT is usually around $10.
            market_order_params = {'symbol':'BTCUSDT', 'side':Client.SIDE_BUY, 'type':Client.ORDER_TYPE_MARKET, 'quoteOrderQty': 15.0, 'timestamp': handler._get_timestamp()}
            test_market_order = handler.client.create_test_order(**market_order_params)
            print("Test Market Buy Order Response (validation only):", test_market_order) # Should be {} if successful

            logger.info("4. Example: Limit Sell (Test Order - Validation only)")
            # Assume we want to sell 0.001 BTC at a high price
            limit_order_params = {'symbol':'BTCUSDT', 'side':Client.SIDE_SELL, 'type':Client.ORDER_TYPE_LIMIT,
                                  'quantity':0.0005, 'price': handler._format_price('BTCUSDT', 90000), # Price far away
                                  'timeInForce':Client.TIME_IN_FORCE_GTC, 'timestamp': handler._get_timestamp()}
            test_limit_order = handler.client.create_test_order(**limit_order_params)
            print("Test Limit Sell Order Response (validation only):", test_limit_order) # Should be {}

            # Note: Actual OCO orders against testnet require funds and careful parameterization.
            # The create_oco_order method in python-binance should work against testnet if client is in testnet mode.
            logger.info("5. Example: OCO Sell (Conceptual - parameters for a real testnet OCO)")
            # This would be for a scenario where you ALREADY OWN BTC and want to set TP/SL
            # OCO_QTY = 0.0005 # Amount of BTC you own and want to sell via OCO
            # CURRENT_PRICE_ESTIMATE = 60000 # Placeholder
            # TP_PRICE = CURRENT_PRICE_ESTIMATE * 1.10
            # SL_TRIGGER_PRICE = CURRENT_PRICE_ESTIMATE * 0.95
            # SL_LIMIT_PRICE = CURRENT_PRICE_ESTIMATE * 0.948
            # oco_order_actual_testnet = handler.create_oco_order(
            # symbol='BTCUSDT', side=Client.SIDE_SELL, quantity=OCO_QTY,
            # price=TP_PRICE, # Take Profit price
            # stop_price=SL_TRIGGER_PRICE, # Stop price
            # stop_limit_price=SL_LIMIT_PRICE # Stop Limit price
            # )
            # if oco_order_actual_testnet:
            # print("Actual OCO Sell Order on Testnet Response:", oco_order_actual_testnet)
            # else:
            # print("Failed to place actual OCO Sell Order on Testnet.")
            print("Conceptual OCO example. Uncomment and adjust parameters to run against testnet if you have balance.")


            logger.info("6. Fetching open orders for BTCUSDT on Testnet...")
            open_orders_list = handler.get_open_orders(symbol='BTCUSDT')
            if open_orders_list is not None:
                if open_orders_list:
                    print("Open BTCUSDT Orders on Testnet:", open_orders_list)
                    # Example: Cancel first open order if any (BE CAREFUL)
                    # order_id_to_cancel = open_orders_list[0]['orderId']
                    # print(f"Attempting to cancel order ID {order_id_to_cancel} on Testnet...")
                    # cancel_resp = handler.cancel_order('BTCUSDT', order_id_to_cancel)
                    # print("Cancel response:", cancel_resp)
                else:
                    print("No open orders for BTCUSDT on Testnet.")
            else:
                print("Failed to fetch open orders for BTCUSDT on Testnet.")
        else:
            logger.info("Skipping order execution examples as not running in testnet mode for safety.")

    except ValueError as e:
        logger.error(f"Configuration or Value Error: {e}")
    except BinanceAPIException as e:
        logger.error(f"Binance API Error during example execution: {e}")
    except Exception as e:
        logger.error(f"Unexpected Error during example execution: {e}", exc_info=True)

    logging.info("--- End of Binance Handler Example Usage ---")
