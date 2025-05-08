from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class IngredientInfo(BaseModel):
    name: str
    hazard_level: str
    description: str
    effects: Optional[List[str]] = None
    alternatives: Optional[List[str]] = None


class ChatResponse(BaseModel):
    answer: str
    ingredients_found: List[IngredientInfo]
    confidence: float
