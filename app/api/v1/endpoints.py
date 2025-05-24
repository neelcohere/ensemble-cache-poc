import json
import os
from typing import Any, Dict
from datetime import datetime, UTC

from fastapi import FastAPI, HTTPException, APIRouter

from core.cache import get_redis_connection
from models.item import CacheItem
from models.response import CacheResponse

# FastAPI app
app = FastAPI(
    title="Redis Cache API",
    description="A Redis-based caching service for storing and retrieving JSON objects",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# API Router for v1 endpoints
v1_router = APIRouter(prefix="/api/v1", tags=["Cache API v1"])


@v1_router.post("/cache", response_model=dict)
async def store_in_cache(item: CacheItem) -> Dict[str, Any]:
    """Store item (json obj) in Redis cache on Azure"""

    try:
        redis_conn = await get_redis_connection()

        cache_entry = {
            "data": item.data,
            "cached_at": datetime.now(UTC).isoformat(),
            "original_ttl": item.ttl_seconds
        }

        cache_value = json.dumps(cache_entry)
        await redis_conn.setex(
            name=item.key,
            time=item.ttl_seconds,
            value=cache_value
        )

        return {
            "success": True,
            "message": f"Stored '{item.key}' in cache",
            "key": item.key,
            "ttl_seconds": item.ttl_seconds,
            "cached_at": cache_entry["cached_at"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store in cache: {str(e)}")


@v1_router.get("/cache/{key}", response_model=CacheResponse)
async def get_from_cache(key: str) -> CacheResponse:
    """Retrieve a cached json object from Redis"""
    try:
        redis_conn = await get_redis_connection()

        cached_value = await redis_conn.get(key)
        if cached_value is None:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        
        cached_entry = json.loads(cached_value)

        ttl_remaining = await redis_conn.ttl(key)
        if ttl_remaining == -1:
            ttl_remaining = None # key exists, but has no expiration

        return CacheResponse(
            key=key,
            data=cached_entry["data"],
            cached_at=cached_entry["cached_at"],
            ttl_remaining=ttl_remaining
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON data in cache")
    except Exception as e:
        if "not found" in str(e):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to retrieve from cache: {str(e)}")


@v1_router.delete("/cache/{key}")
async def delete_from_cache(key: str) -> dict[str, Any]:
    """Delete an existing item in Redis"""
    try:
        redis_conn = await get_redis_connection()
        
        deleted_count = await redis_conn.delete(key)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found in cache")
        
        return {
            "success": True,
            "message": f"Deleted '{key}' from cache"
        }
    except Exception as e:
        if "not found" in str(e):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to delete from cache: {str(e)}")


@v1_router.get("/cache/{key}/exists")
async def check_key_exists(key: str) -> dict[str, Any]:
    """Check if a key exists in Redis cache"""
    try:
        redis_conn = await get_redis_connection()
        exists = await redis_conn.exists(key)

        result = {"key": key, "exists": bool(exists)}

        if exists:
            ttl = await redis_conn.ttl(key)
            result["ttl_remaining"] = ttl if ttl != -1 else None

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check key existence: {str(e)}")


@v1_router.get("/cache")
async def list_cache_keys(pattern: str = "*") -> dict[str, Any]:
    """List all keys in cache matching a pattern"""
    try:
        redis_conn = await get_redis_connection()
        keys = await redis_conn.keys(pattern)

        return {
            "pattern": pattern,
            "keys": keys,
            "count": len(keys)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list keys: {str(e)}")


@v1_router.post("/cache/bulk")
async def store_bulk_in_cache(items: list[CacheItem]) -> dict[str, Any]:
    """Store items in bulk in the cache"""
    try:
        redis_conn = await get_redis_connection()
        pipe = redis_conn.pipeline()

        stored_keys = []
        for item in items:
            cache_entry = {
                "data": item.data,
                "cached_at": datetime.now(UTC).isoformat(),
                "original_ttl": item.ttl_seconds
            }
            cache_value = json.dumps(cache_entry)
            pipe.setex(item.key, item.ttl_seconds, cache_value)
            stored_keys.append(item.key)
        
        await pipe.execute()

        return {
            "success": True,
            "message": f"Stored {len(items)} items in cache",
            "keys": stored_keys
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store bulk items: {str(e)}")


@v1_router.get("/health")
async def health_check():
    """
    Health check endpoint that tests Redis connection
    """
    try:
        redis_conn = await get_redis_connection()
        await redis_conn.ping()
        return {
            "status": "healthy",
            "redis": "connected",
            "version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "redis": "disconnected",
            "error": str(e),
            "version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat()
        }


app.include_router(v1_router)


@app.get("/")
async def root():
    """
    API information and available versions
    """
    return {
        "service": "Redis Cache API",
        "version": "1.0.0",
        "status": "running",
        "available_versions": ["v1"],
        "endpoints": {
            "v1": "/api/v1",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "timestamp": datetime.now(UTC).isoformat()
    }
