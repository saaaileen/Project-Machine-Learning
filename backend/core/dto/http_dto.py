from pydantic import BaseModel
from typing import Optional, Any

class HttpResponse(BaseModel):
    code: int
    status: str
    messages: str
    data: Any = None
    error_message: Optional[str] = None 


class LoginRequest(BaseModel):
    password: str
 