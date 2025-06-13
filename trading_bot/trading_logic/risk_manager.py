# risk_manager.py

class RiskManager:
    def __init__(self, balance, max_risk_per_trade):
        self.balance = balance
        self.max_risk_per_trade = max_risk_per_trade  # Percentage of balance

    def calculate_position_size(self, entry_price, stop_loss_price):
        """
        Calculates the position size based on max risk per trade.
        """
        risk_amount = self.balance * self.max_risk_per_trade
        risk_per_share = entry_price - stop_loss_price
        if risk_per_share <= 0:
            return 0  # Avoid division by zero or illogical position sizing
        position_size = risk_amount / risk_per_share
        return position_size

    def check_trade_limit(self, current_trades, max_concurrent_trades):
        """
        Checks if the number of current trades is within the allowed limit.
        """
        return current_trades < max_concurrent_trades

if __name__ == '__main__':
    manager = RiskManager(balance=10000, max_risk_per_trade=0.02) # 2% risk per trade

    # Example: Calculate position size
    position_size = manager.calculate_position_size(entry_price=150, stop_loss_price=145)
    print(f"Calculated Position Size: {position_size:.2f} shares")

    # Example: Check trade limit
    can_trade = manager.check_trade_limit(current_trades=3, max_concurrent_trades=5)
    print(f"Can open new trade: {can_trade}")
