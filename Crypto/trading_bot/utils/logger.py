import logging

def setup_logger(name: str = 'trading_bot', log_file: str = 'trading_bot.log', level=logging.INFO):
    """Function to set up a logger."""
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger