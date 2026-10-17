import logging
from datetime import datetime
import os

class AppLogger:
    def __init__(self, log_dir="app_logs", log_file_prefix="app_log_", log_level=logging.INFO):
        self.log_dir = log_dir
        self.log_file_prefix = log_file_prefix
        self.log_level = log_level
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """Sets up the logger with file and console handlers."""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file_name = f"{self.log_file_prefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file_path = os.path.join(self.log_dir, log_file_name)

        logger = logging.getLogger('PeopleCounterAppLogger')
        logger.setLevel(self.log_level)
        logger.propagate = False # Prevent messages from being passed to the root logger

        # File Handler
        file_handler = logging.FileHandler(log_file_path)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def debug(self, message):
        self.logger.debug(message)