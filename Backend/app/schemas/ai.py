# app/schemas/ai.py
from pydantic import BaseModel

class AIQueryRequest(BaseModel):
    question: str

class AIQueryResponse(BaseModel):
    response: str