from fastapi import FastAPI, HTTPException, Body

from ChatBotAPI.core.logger_factory import get_logger
from ChatBotAPI.model.schemas import ChatResponse, ChatRequest, IngredientInfo
from ChatBotAPI.repository.product_repository import ProductRepository
from ChatBotAPI.service.nlp_service import NLPService
from ChatBotAPI.service.response_gen_service import ResponseGenerator

app = FastAPI(
    title="Cosmetics Ingredient Chatbot API",
    description="API cung cấp thông tin về thành phần mỹ phẩm",
    version="1.0.0"
)

logger = get_logger()
nlp_service = NLPService()
product_repository = ProductRepository()
#response_generator = ResponseGenerator()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest = Body(...)):
    try:
        processed = nlp_service.process_text(request.query)
        if not processed["ingredients"]:
            return ChatResponse(answer="Không tìm thấy thành phần.", ingredients_found=[], confidence=0.0)
        results = await product_repository.search_ingredients(processed["ingredients"])
        answer = nlp_service.generate_response(processed["intent"], results, processed["original_text"])
        ingredients = [IngredientInfo(**r) for r in results]
        confidence = min(len(results) / len(processed["ingredients"]), 1.0)
        return ChatResponse(answer=answer, ingredients_found=ingredients, confidence=confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ping")
async def ping():
    return "pong"


