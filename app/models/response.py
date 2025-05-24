from pydantic import BaseModel
from typing import Optional, Any, Dict


class CacheResponse(BaseModel):
    key: str
    data: Dict[str, Any]
    cached_at: str
    ttl_remaining: Optional[int] = None
