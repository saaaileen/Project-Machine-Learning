from pydantic import BaseModel
from typing import Optional, Any, List

class HttpResponse(BaseModel):
    code: int
    status: str
    messages: str
    data: Any = None
    error_message: Optional[str] = None 


class LoginRequest(BaseModel):
    password: str


class UseModelRequest(BaseModel):
    model_name: str = "logisticRegression"
    row_indices: Optional[List[int]] = None