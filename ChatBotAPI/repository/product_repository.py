from typing import List, Dict, Any

from ChatBotAPI.repository.es_repository import ElasticsearchRepository


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

    async def search_ingredients(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        results = []
        for ingredient in ingredients:
            query = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"name": {"query": ingredient, "fuzziness": "AUTO"}}},
                            {"match": {"aliases": {"query": ingáyedient, "fuzziness": "AUTO"}}}
                        ],
                        "minimum_should_match": 1
                    }
                }
            }
            try:
                response = self.client.search(index=self.INDEX_NAME, body=query, size=5)
                for hit in response["hits"]["hits"]:
                    if hit["_score"] > 5.0:
                        source = hit["_source"]
                        results.append({
                            "name": source.get("name", ""),
                            "hazard_level": source.get("hazard_level", "Unknown"),
                            "description": source.get("description", ""),
                            "effects": source.get("effects", []),
                            "alternatives": source.get("alternatives", []),
                            "score": hit["_score"]
                        })
            except Exception as e:
                self.logger.error(f"ES query error: {e}")
        return results
