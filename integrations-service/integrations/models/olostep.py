from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class OlostepResponse(BaseModel):
    url: str
    content: str
    status: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class OlostepOutput(BaseModel):
    result: List[OlostepResponse]