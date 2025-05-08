import os
from elasticsearch import Elasticsearch
from threading import Lock
from ChatBotAPI.core.logger_factory import get_logger  # Giả sử bạn đã có logger singleton ở đây

logger = get_logger()

class _ESClientFactory:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._client = self._create_client()
        self._initialized = True

    def _create_client(self):
        # === Read config from .env or defaults ===
        host = os.getenv("ELASTICSEARCH_HOST", "http://localhost")
        port = os.getenv("ELASTICSEARCH_PORT", "9200")
        user = os.getenv("ELASTICSEARCH_USER", None)
        password = os.getenv("ELASTICSEARCH_PASSWORD", None)

        es_url = f"{host}:{port}"

        es_kwargs = {
            "hosts": [es_url],
            "request_timeout": 10,
            "max_retries": 3,
            "retry_on_timeout": True
        }

        if user and password:
            es_kwargs["basic_auth"] = (user, password)

        client = Elasticsearch(**es_kwargs)

        if client.ping():
            logger.info(f"Elasticsearch connected: {es_url}")
        else:
            logger.warning("Elasticsearch is not responding!")

        return client

    def get_client(self):
        return self._client


def get_es_client():
    return _ESClientFactory().get_client()
