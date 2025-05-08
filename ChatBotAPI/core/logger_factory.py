import logging
import os
import sys
from threading import Lock

class _LoggerFactory:
    _instance = None
    _lock = Lock()

    def __new__(cls, name="chatbotAPI_app_logger", log_dir="logs", log_file="ChatBotAPI.log"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, name="chatbotAPI_crawler_app_logger", log_dir="logs", log_file="ChatBotAPI.log"):
        if self._initialized:
            return
        self.name = name
        self.log_dir = log_dir
        self.log_file = log_file
        self.logger = self._create_logger()
        self._initialized = True

    def _create_logger(self):
        os.makedirs(self.log_dir, exist_ok=True)
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        if logger.hasHandlers():
            return logger

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler = logging.FileHandler(os.path.join(self.log_dir, self.log_file))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

def get_logger():
    return _LoggerFactory().logger