import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import Redis, ConnectionPool


load_dotenv(dotenv_path="../../.env", override=True)

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", None)
REDIS_PORT = os.getenv("REDIS_PORT", None)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_SSL = os.getenv("REDIS_SSL", "False").lower() == "true"

# Redis connection pool
redis_pool = None


async def get_redis_connection() -> Redis:
    """Get redis connection using the pool"""
    global redis_pool
    if redis_pool is None:
        # Construct the URL with proper SSL configuration
        protocol = "rediss" if REDIS_SSL else "redis"
        url = f"{protocol}://{REDIS_HOST}:{REDIS_PORT}"
        
        redis_pool = ConnectionPool.from_url(
            url,
            password=REDIS_PASSWORD,
            ssl_cert_reqs=None if REDIS_SSL else None,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20
        )
    return Redis(connection_pool=redis_pool)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Cache lifespan manager"""
    try:
        redis_conn = await get_redis_connection()
        print("Connected to Azure Redis Cache successfully")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        raise

    yield # application runs here

    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        print("Redis connection closed")
