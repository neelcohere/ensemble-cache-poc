from pydantic import BaseModel
from typing import Optional, Any, Dict


class CacheItem(BaseModel):
    key: str
    data: Dict[str, Any]
    ttl_seconds: Optional[int] = 3600 # default 1 hour
