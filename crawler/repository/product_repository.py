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
