# logger.py

import logging
import os

def setup_logger(log_file='trading_bot.log', level=logging.INFO):
    """
    Sets up a logger for the trading bot.
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_file_path = os.path.join('logs', log_file)

    logger = logging.getLogger('TradingBotLogger')
    logger.setLevel(level)

    # Create handlers
    c_handler = logging.StreamHandler()  # Console handler
    f_handler = logging.FileHandler(log_file_path) # File handler
    c_handler.setLevel(level)
    f_handler.setLevel(level)

    # Create formatters and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)

    # Add handlers to the logger
    if not logger.handlers: # Avoid adding multiple handlers if logger already exists
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger

if __name__ == '__main__':
    logger = setup_logger()
    logger.info("Logger setup complete.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
