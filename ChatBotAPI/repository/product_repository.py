from typing import List, Dict, Any

from ChatBotAPI.repository.es_repository import ElasticsearchRepository


class ProductRepository(ElasticsearchRepository):
    INDEX_NAME = "products"
    INGREDIENT_INDEX = "ingredients"

    def search_all(self):
        return self.search(index=self.INGREDIENT_INDEX, query={"match_all": {}})

    def find_by_name(self, name: str):
        return self.search(index=self.INGREDIENT_INDEX, query={"match": {"name": name}})

    def get_product(self, product_id: str):
        return self.get(index=self.INGREDIENT_INDEX, id=product_id)

    def save_product(self, product: dict, product_id: str = None):
        return self.index(index=self.INGREDIENT_INDEX, document=product, id=product_id)

    def delete_product(self, product_id: str):
        return self.delete(index=self.INGREDIENT_INDEX, id=product_id)

    async def search_ingredients(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        results = []
        for ingredient in ingredients:
            query = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"name": {"query": ingredient, "fuzziness": "AUTO"}}},
                            {"match": {"aliases": {"query": ingredient, "fuzziness": "AUTO"}}}
                        ],
                        "minimum_should_match": 1
                    }
                }
            }
            try:
                response = self.client.search(index=self.INGREDIENT_INDEX, body=query, size=5)
                for hit in response["hits"]["hits"]:
                    if hit["_score"] > 0.0:
                        source = hit["_source"]
                        results.append({
                            "name": source.get("name", ""),
                            "aliases": source.get("aliases", ""),
                            "what_it_does": source.get("what_it_does", ""),
                            "irritancy": source.get("irritancy", ""),
                            "comedogenicity": source.get("comedogenicity", ""),
                            "hazard_level": source.get("hazard_level", "Unknown"),
                            "ewg_rating": source.get("ewg_rating", ""),
                            "description": source.get("description", ""),
                            "effects": source.get("effects", []),
                            "alternatives": source.get("alternatives", []),
                            "score": hit["_score"]
                        })
            except Exception as e:
                self.logger.error(f"ES query error: {e}")
        return results
