import re

from elasticsearch.helpers import bulk

from es_repository import ElasticsearchRepository


class ProductRepository(ElasticsearchRepository):
    INDEX_NAME = "products"
    INGREDIENT_INDEX = "cosmetic_ingredients"

    def search_all(self):
        return self.search(index=self.INDEX_NAME, query={"match_all": {}})

    def find_by_name(self, name: str):
        return self.search(index=self.INDEX_NAME, query={"match": {"name": name}})

    def get_product(self, product_id: str):
        return self.get(index=self.INDEX_NAME, id=product_id)

    def save_product(self, product: dict, product_id: str = None):
        return self.index(index=self.INDEX_NAME, document=product, id=product_id)

    def delete_product(self, product_id: str):
        return self.delete(index=self.INDEX_NAME, id=product_id)

    def _create_index(self):

        # Định nghĩa cấu trúc mapping cho index
        mapping = {
            "mappings": {
                "properties": {
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "aliases": {"type": "text"},
                    "what_it_does": {"type": "text"},
                    "irritancy": {"type": "keyword"},
                    "comedogenicity": {"type": "keyword"},
                    "hazard_level": {"type": "keyword"},
                    "ewg_rating": {"type": "float"},
                    "description": {"type": "text"},
                    "functions": {"type": "keyword"},
                    "url": {"type": "keyword"},
                    "last_updated": {"type": "date"}
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "ingredient_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding"]
                        }
                    }
                }
            }
        }

        try:
            if not self.client.indices.exists(index=self.INGREDIENT_INDEX):
                self.client.indices.create(index=self.INGREDIENT_INDEX, body=mapping)
                self.logger.info(f"Đã tạo index '{self.INGREDIENT_INDEX}'")
            else:
                self.logger.info(f"Index '{self.INGREDIENT_INDEX}' đã tồn tại")
        except Exception as e:
            self.logger.error(f"Lỗi khi tạo index: {str(e)}")
            raise

    def save_ingredients(self, data_list: list[dict]):
        """
        Lưu danh sách dữ liệu thành phần vào Elasticsearch.

        Args:
            data_list: Danh sách các dict chứa dữ liệu thành phần
        """
        if not data_list:
            self.logger.warning("Không có dữ liệu để lưu vào Elasticsearch")
            return

        actions = []
        for data in data_list:
            if not data:
                continue

            doc_id = re.sub(r'[^a-z0-9]', '_', data.get("name", "").lower())
            if not doc_id:
                continue

            actions.append({
                "_index": self.INGREDIENT_INDEX,
                "_id": doc_id,
                "_source": data
            })

        if actions:
            try:
                success_count, _ = bulk(self.client, actions)
                self.logger.info(f"Đã lưu {success_count} thành phần vào Elasticsearch")
            except Exception as e:
                self.logger.exception(f"Lỗi khi lưu dữ liệu thành phần vào Elasticsearch: {e}")
