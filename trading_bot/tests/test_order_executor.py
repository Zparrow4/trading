# test_order_executor.py

import unittest
from unittest.mock import patch, MagicMock

# Adjust the import path according to your project structure
from trading_logic.order_executor import OrderExecutor

class TestOrderExecutor(unittest.TestCase):

    def setUp(self):
        self.executor = OrderExecutor(api_key="test_api_key", secret_key="test_secret_key")

    def test_execute_buy_order_success(self):
        # For this test, we assume the broker API call is successful
        # In a real scenario, you might mock the broker connection object
        print("Simulating successful buy order execution...")
        result = self.executor.execute_order("AAPL", "buy", 10, price=150.00)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["order_id"], "12345") # As per current mock implementation
        self.assertEqual(result["filled_quantity"], 10)
        print(f"Buy order test result: {result}")

    def test_execute_sell_order_success(self):
        print("Simulating successful sell order execution...")
        result = self.executor.execute_order("MSFT", "sell", 5, price=280.00)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["order_id"], "12345")
        self.assertEqual(result["filled_quantity"], 5)
        print(f"Sell order test result: {result}")

    def test_execute_market_order_success(self):
        print("Simulating successful market sell order execution...")
        result = self.executor.execute_order("GOOG", "sell", 2) # Market order (no price)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["filled_quantity"], 2)
        print(f"Market sell order test result: {result}")

    def test_execute_order_invalid_type(self):
        print("Testing invalid order type...")
        with self.assertRaises(ValueError) as context:
            self.executor.execute_order("TSLA", "hold", 10)
        self.assertIn("Order type must be 'buy' or 'sell'", str(context.exception))
        print(f"Invalid order type test passed with exception: {context.exception}")

    # Example of how you might mock a broker API call if it were more complex
    @patch('trading_logic.order_executor.OrderExecutor.execute_order') # Assuming execute_order calls a broker method
    def test_execute_order_with_broker_mock(self, mock_execute_order_method):
        # This mock is a bit meta as it mocks the method we are testing.
        # A better approach would be to mock a lower-level broker interaction if it existed.
        # For now, this demonstrates the @patch usage.

        mock_execute_order_method.return_value = {"status": "success", "order_id": "mock_id_67890", "filled_quantity": 7}

        executor_mocked = OrderExecutor(api_key="mock_key", secret_key="mock_secret")
        result = executor_mocked.execute_order("NVDA", "buy", 7, price=700.00)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["order_id"], "mock_id_67890")
        self.assertEqual(result["filled_quantity"], 7)
        mock_execute_order_method.assert_called_with("NVDA", "buy", 7, price=700.00)
        print(f"Mocked broker call test result: {result}")

if __name__ == '__main__':
    # This allows running tests directly, but usually, you'd use 'python -m unittest discover'
    # Adding a simple print to confirm test execution if run directly
    print("Starting OrderExecutor tests...")
    unittest.main()
    print("Finished OrderExecutor tests.")
