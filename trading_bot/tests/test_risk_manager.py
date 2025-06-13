# test_risk_manager.py

import unittest

# Adjust the import path according to your project structure
from trading_logic.risk_manager import RiskManager

class TestRiskManager(unittest.TestCase):

    def setUp(self):
        self.initial_balance = 10000
        self.risk_per_trade_percentage = 0.02 # 2%
        self.manager = RiskManager(balance=self.initial_balance, max_risk_per_trade=self.risk_per_trade_percentage)

    def test_calculate_position_size_valid(self):
        entry_price = 150
        stop_loss_price = 145
        expected_risk_amount = self.initial_balance * self.risk_per_trade_percentage # 10000 * 0.02 = 200
        risk_per_share = entry_price - stop_loss_price # 150 - 145 = 5
        expected_position_size = expected_risk_amount / risk_per_share # 200 / 5 = 40

        position_size = self.manager.calculate_position_size(entry_price, stop_loss_price)
        self.assertEqual(position_size, expected_position_size)

    def test_calculate_position_size_zero_risk_per_share(self):
        # Stop loss is at or above entry price, should result in zero position size
        position_size_at_entry = self.manager.calculate_position_size(entry_price=150, stop_loss_price=150)
        self.assertEqual(position_size_at_entry, 0)

        position_size_above_entry = self.manager.calculate_position_size(entry_price=150, stop_loss_price=155)
        self.assertEqual(position_size_above_entry, 0)

    def test_calculate_position_size_no_balance(self):
        manager_no_balance = RiskManager(balance=0, max_risk_per_trade=0.02)
        position_size = manager_no_balance.calculate_position_size(entry_price=150, stop_loss_price=145)
        self.assertEqual(position_size, 0)

    def test_calculate_position_size_no_risk_percentage(self):
        manager_no_risk = RiskManager(balance=10000, max_risk_per_trade=0)
        position_size = manager_no_risk.calculate_position_size(entry_price=150, stop_loss_price=145)
        self.assertEqual(position_size, 0)

    def test_check_trade_limit_below_max(self):
        can_trade = self.manager.check_trade_limit(current_trades=3, max_concurrent_trades=5)
        self.assertTrue(can_trade)

    def test_check_trade_limit_at_max(self):
        can_trade = self.manager.check_trade_limit(current_trades=5, max_concurrent_trades=5)
        self.assertFalse(can_trade)

    def test_check_trade_limit_above_max(self):
        can_trade = self.manager.check_trade_limit(current_trades=6, max_concurrent_trades=5)
        self.assertFalse(can_trade)

    def test_check_trade_limit_zero_max(self):
        can_trade = self.manager.check_trade_limit(current_trades=0, max_concurrent_trades=0)
        self.assertFalse(can_trade)

        can_trade_with_open = self.manager.check_trade_limit(current_trades=1, max_concurrent_trades=0)
        self.assertFalse(can_trade_with_open)


if __name__ == '__main__':
    unittest.main()
