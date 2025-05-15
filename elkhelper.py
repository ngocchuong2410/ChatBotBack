import logging

from elasticsearch import helpers, Elasticsearch

logger = logging.getLogger('elkhelper')

class ElasticsearchHelper:
    def __init__(self, host='http://localhost:9200', index_name='ingredients'):
        self.es = Elasticsearch(hosts=[host])
        self.index_name = index_name
        self.logger = logger

        if not self.es.indices.exists(index=self.index_name):
            self.create_index()

    # def create_index_if_not_exists(self):
    #     if not self.es.indices.exists(index=self.index_name):
    #         mapping = {
    #             "mappings": {
    #                 "properties": {
    #                     "id": {"type": "keyword"},
    #                     "name": {"type": "text"},
    #                     "aliases": {"type": "text"},
    #                     "what_it_does": {"type": "text"},
    #                     "functions": {"type": "text"},
    #                     "irritancy": {"type": "keyword"},
    #                     "comedogenicity": {"type": "keyword"},
    #                     "hazard_level": {"type": "keyword"},
    #                     "ewg_rating": {"type": "keyword"},
    #                     "description": {"type": "text"},
    #                     "url": {"type": "keyword"},
    #                     "scrape_date": {"type": "date", "format": "yyyy-MM-dd"}
    #                 }
    #             }
    #         }
    #         try:
    #             self.es.indices.create(index=self.index_name, body=mapping)
    #             self.logger.info(f"Created index '{self.index_name}' with custom mapping.")
    #         except Exception as e:
    #             self.logger.error(f"Failed to create index '{self.index_name}': {e}")
    #     else:
    #         self.logger.info(f"Index '{self.index_name}' already exists.")

    def create_index(self):
        # Tùy chỉnh schema nếu cần
        mappings = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text"},
                    "aliases": {"type": "text"},
                    "what_it_does": {"type": "text"},
                    "functions": {"type": "text"},
                    "irritancy": {"type": "keyword"},
                    "comedogenicity": {"type": "keyword"},
                    "hazard_level": {"type": "keyword"},
                    "ewg_rating": {"type": "keyword"},
                    "description": {"type": "text"},
                    "url": {"type": "keyword"},
                    "scrape_date": {"type": "date"}
                }
            }
        }

        self.es.indices.create(index=self.index_name, body=mappings)
        logging.info(f"Created index: {self.index_name}")

    def insert_one(self, doc):
        try:
            response = self.es.index(index=self.index_name, id=doc.get("id"), document=doc)
            logging.info(f"Inserted doc ID: {doc.get('id')}")
            return response
        except Exception as e:
            logging.error(f"Failed to insert document: {e}")
            return None

    def bulk_insert(self, docs):
        actions = [
            {
                "_index": self.index_name,
                "_id": doc.get("id"),
                "_source": doc
            }
            for doc in docs
        ]
        try:
            success, _ = helpers.bulk(self.es, actions)
            logging.info(f"Bulk inserted {success} documents.")
            return success
        except Exception as e:
            logging.error(f"Bulk insert failed: {e}")
            return 0