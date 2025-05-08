from elasticsearch import Elasticsearch
from ChatBotAPI.factory.es_pool_factory import get_es_client
from ChatBotAPI.core.logger_factory import get_logger

class ElasticsearchRepository():
    def __init__(self, client: Elasticsearch = None, logger=None):
        self.client = client or get_es_client()
        self.logger = logger or get_logger()

    def search(self, index: str, query: dict) -> dict:
        try:
            return self.client.search(index=index, query=query)
        except Exception as e:
            self.logger.exception(f"Error searching index '{index}': {e}")
            raise

    def get(self, index: str, id: str) -> dict:
        try:
            return self.client.get(index=index, id=id)
        except Exception as e:
            self.logger.exception(f"Error getting document '{id}' from index '{index}': {e}")
            raise

    def index(self, index: str, document: dict, id: str = None) -> dict:
        try:
            return self.client.index(index=index, document=document, id=id)
        except Exception as e:
            self.logger.exception(f"Error indexing document to index '{index}': {e}")
            raise

    def delete(self, index: str, id: str) -> dict:
        try:
            return self.client.delete(index=index, id=id)
        except Exception as e:
            self.logger.exception(f"Error deleting document '{id}' from index '{index}': {e}")
            raise
