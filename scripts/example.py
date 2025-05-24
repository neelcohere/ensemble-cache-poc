from client.client import CacheAPIClient
import asyncio


async def main():
    data = {
        "account_number": "2312313123",
        "demographics": ["hello"],
        "remits": ["hi"],
    }
    key = "2312313123"
    
    client = CacheAPIClient()

    health_response = await client.health_check()
    print("Health check response:", health_response)

    store_response = await client.store(key=key, data=data)
    print("Store response:", store_response)

    get_account = await client.get(key=key)
    print("Get stored account:", get_account)


if __name__ == "__main__":
    asyncio.run(main())
