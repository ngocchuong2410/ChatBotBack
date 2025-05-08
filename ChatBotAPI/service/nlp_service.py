from typing import List, Dict, Any

import spacy

from ChatBotAPI.core.logger_factory import get_logger

logger = get_logger()
class NLPService:
    def __init__(self):
        self.nlp = self._load_spacy_model()

    def _load_spacy_model(self):
        try:
            return spacy.load("en_core_news_lg")
        except OSError:
            logger.warning("Using fallback spaCy model")
            for model in ["en_core_news_md", "en_core_news_sm", "en_core_web_sm"]:
                try:
                    return spacy.load(model)
                except OSError:
                    continue
            raise RuntimeError("No suitable spaCy model found")

    # Hàm xử lý text sử dụng spaCy
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Xử lý text đầu vào sử dụng spaCy để trích xuất các thực thể có thể là thành phần mỹ phẩm
        """
        doc = self.nlp(text)

        # Trích xuất các thực thể có thể là thành phần mỹ phẩm
        potential_ingredients = []

        # Lấy các danh từ riêng và các danh từ chung
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "SUBSTANCE", "CHEMICAL", "ORG", "MISC"]:
                potential_ingredients.append(ent.text)

        # Lấy thêm các cụm danh từ có thể là thành phần
        for chunk in doc.noun_chunks:
            potential_ingredients.append(chunk.text)

        # Loại bỏ các từ trùng lặp và làm sạch
        unique_ingredients = list(set(potential_ingredients))
        cleaned_ingredients = [ing.strip().lower() for ing in unique_ingredients if len(ing.strip()) > 2]

        # Phân tích ý định của người dùng
        intent = "ingredient_info"  # Default intent

        # Kiểm tra các từ khóa để xác định intent
        dangerous_keywords = ["nguy hiểm", "độc hại", "có hại", "tác dụng phụ", "nguy hại"]
        safe_keywords = ["an toàn", "lành tính", "tốt cho da", "không độc hại"]
        alternative_keywords = ["thay thế", "thay", "dùng gì", "sản phẩm khác"]

        if any(keyword in text.lower() for keyword in dangerous_keywords):
            intent = "hazard_info"
        elif any(keyword in text.lower() for keyword in safe_keywords):
            intent = "safety_info"
        elif any(keyword in text.lower() for keyword in alternative_keywords):
            intent = "alternative_info"

        return {
            "ingredients": cleaned_ingredients,
            "intent": intent,
            "original_text": text
        }

    # Hàm tạo câu trả lời
    def generate_response(self, intent: str, ingredients_data: List[Dict[str, Any]], original_query: str) -> str:
        """
        Tạo câu trả lời dựa trên intent và dữ liệu về thành phần
        """
        if not ingredients_data:
            return "Tôi không tìm thấy thông tin về thành phần mỹ phẩm trong câu hỏi của bạn. Vui lòng cung cấp tên cụ thể của thành phần mỹ phẩm bạn muốn tìm hiểu."

        response = ""

        if intent == "ingredient_info":
            response = f"Tôi đã tìm thấy thông tin về {len(ingredients_data)} thành phần mỹ phẩm:\n\n"

            for idx, ingredient in enumerate(ingredients_data, 1):
                hazard_level = ingredient["hazard_level"]
                hazard_emoji = "🟢" if hazard_level.lower() in ["an toàn", "low",
                                                               "thấp"] else "🟠" if hazard_level.lower() in [
                    "trung bình", "medium"] else "🔴"

                response += f"{idx}. {hazard_emoji} {ingredient['name']} (Mức độ nguy hại: {hazard_level})\n"
                response += f"   {ingredient['description']}\n"

                if ingredient.get("effects") and len(ingredient["effects"]) > 0:
                    response += f"   Tác động tiềm ẩn: {', '.join(ingredient['effects'])}\n"

                response += "\n"

        elif intent == "hazard_info":
            dangerous_ingredients = [ing for ing in ingredients_data if
                                     ing["hazard_level"].lower() in ["cao", "high", "trung bình", "medium"]]

            if dangerous_ingredients:
                response = f"Trong số các thành phần bạn hỏi, có {len(dangerous_ingredients)} thành phần có mức độ nguy hại đáng chú ý:\n\n"

                for idx, ingredient in enumerate(dangerous_ingredients, 1):
                    hazard_level = ingredient["hazard_level"]
                    hazard_emoji = "🟠" if hazard_level.lower() in ["trung bình", "medium"] else "🔴"

                    response += f"{idx}. {hazard_emoji} {ingredient['name']} (Mức độ nguy hại: {hazard_level})\n"
                    response += f"   {ingredient['description']}\n"

                    if ingredient.get("effects") and len(ingredient["effects"]) > 0:
                        response += f"   Tác động tiềm ẩn: {', '.join(ingredient['effects'])}\n"

                    response += "\n"
            else:
                response = "Tốt quá! Các thành phần bạn hỏi đều có mức độ nguy hại thấp hoặc không có thông tin về tác động tiêu cực đáng kể."

        elif intent == "safety_info":
            safe_ingredients = [ing for ing in ingredients_data if
                                ing["hazard_level"].lower() in ["an toàn", "low", "thấp"]]

            if safe_ingredients:
                response = f"Trong số các thành phần bạn hỏi, có {len(safe_ingredients)} thành phần được đánh giá là an toàn:\n\n"

                for idx, ingredient in enumerate(safe_ingredients, 1):
                    response += f"{idx}. 🟢 {ingredient['name']} (Mức độ nguy hại: {ingredient['hazard_level']})\n"
                    response += f"   {ingredient['description']}\n\n"
            else:
                response = "Tôi không tìm thấy thành phần nào có mức độ an toàn cao trong danh sách bạn hỏi. Hãy cân nhắc tìm các sản phẩm thay thế."

        elif intent == "alternative_info":
            response = "Dưới đây là một số thành phần thay thế an toàn hơn:\n\n"

            for idx, ingredient in enumerate(ingredients_data, 1):
                if ingredient.get("alternatives") and len(ingredient["alternatives"]) > 0:
                    response += f"{idx}. Thay vì {ingredient['name']} (Mức độ nguy hại: {ingredient['hazard_level']}), bạn có thể tìm các sản phẩm chứa:\n"
                    response += f"   {', '.join(ingredient['alternatives'])}\n\n"
                else:
                    response += f"{idx}. Với {ingredient['name']} (Mức độ nguy hại: {ingredient['hazard_level']}), hiện chưa có thông tin về thành phần thay thế.\n\n"

        # Thêm lời khuyên chung
        response += "Lưu ý: Thông tin trên chỉ mang tính tham khảo. Mỗi người có thể phản ứng khác nhau với các thành phần mỹ phẩm. Nếu bạn có làn da nhạy cảm, hãy tham khảo ý kiến của bác sĩ da liễu."

        return response
