import aiohttp


class CacheAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_v1_url = f"{base_url}/api/v1"

    async def store(self, key: str, data: dict, ttl_seconds: int = 3600) -> dict:
        """Store data in cache"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "key": key,
                "data": data,
                "ttl_seconds": ttl_seconds
            }
            async with session.post(f"{self.api_v1_url}/cache", json=payload) as response:
                return await response.json()
            
    async def get(self, key: str) -> dict:
        """Get data from cache with a key"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_v1_url}/cache/{key}") as response:
                if response.status == 200:
                    result = await response.json()
                    return result["data"]
                return None
            
    async def delete(self, key: str):
        """Delete key from cache"""
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.api_v1_url}/cache/{key}") as response:
                return await response.json()

    async def health_check(self):
        """Check API health"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_v1_url}/health") as response:
                return await response.json()

    async def key_exists(self, key: str) -> dict:
        """Check if a key exists in the cache and get its TTL if it does"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_v1_url}/cache/{key}/exists") as response:
                return await response.json()
