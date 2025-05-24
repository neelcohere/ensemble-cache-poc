import os
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from client.client import CacheAPIClient

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manager for triggering and polling workflows"""

    def __init__(
        self, 
        base_url: str = "https://demo.north.cohere.com", 
        bearer_token: Optional[str] = None
    ):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/internal/v1/workflows"
        self.bearer_token = bearer_token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional bearer token"""
        headers = {"Content-Type": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        return headers

    async def trigger_workflow(self, agent_id: str, template_id: str, inputs: Dict[str, Any]) -> str:
        """Trigger a workflow"""
        payload = {
            "agent_id": agent_id,
            "template_id": template_id,
            "inputs": inputs
        }
        headers = self._get_headers()

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/runs/start", json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    run_id = result.get("id")
                    if not run_id:
                        raise Exception("No run_id returned from workflow trigger")
                    return run_id
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger workflows: {response.status} - {error_text}")
        
    async def get_workflow_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of workflow run"""
        headers = self._get_headers()

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/runs/{run_id}", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get workflow status: {response.status} - {error_text}")
                
    async def poll_until_complete(self, run_id: str, poll_interval: int = 5, max_wait_time: int = 3600) -> Dict[str, Any]:
        """Poll workflow till completion"""
        start_time = time.time()
        poll_count = 0

        logger.info(f"Starting to poll workflow {run_id}")

        while time.time() - start_time < max_wait_time:
            poll_count += 1
            try:
                status_data = await self.get_workflow_status(run_id)
                status = status_data.get("status", "UNKNOWN")

                logging.info(f"POLL {poll_count}: workflow status - {status}")

                if status == "COMPLETED":
                    elapsed_time = time.time() - start_time
                    logger.info(f"Workflow run {run_id} completed after {elapsed_time:.1f} secs ({poll_count} polls)")
                    return status_data
                elif status == "FAILED" or status == "ERROR":
                    logger.error(f"Workflow failed with status: {status}")
                    error_msg = status_data.get("error")
                    raise Exception(f"Workflow failed: {error_msg}")
                elif status == "RUNNING":
                    logger.info(f"Workflow still running...")
                else:
                    logger.warning(f"Unknown status: {status}")

                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.error(f"Error polling workflow: {str(e)}")
                raise
        
        # Timeout reached
        elapsed_time = time.time() - start_time
        raise TimeoutError(f"Workflow did not complete within {max_wait_time} secs")


async def run_workflow_with_cache(
    cache_client: CacheAPIClient,
    manager: WorkflowManager,
    workflow_payload: Dict[str, Any],
):
    # Trigger workflow
    run_id = await manager.trigger_workflow(**workflow_payload)

    # Create an empty cache item for this account throughout the duration of this workflow
    key = workflow_payload["inputs"]["accountnumber"] + "-" + workflow_payload["inputs"]["clientid"]
    empty_data = {
        "demographics": {},
        "remits": {},
        "transactions": {},
        "claims": {},
        "notes": {},
        "action": {}
    }

    health_check = await cache_client.health_check()

    if health_check.get("redis_connected") == "connected" and health_check.get("status") == "healthy":
        # Store empty cache object
        await cache_client.store(key=key, data=empty_data)

    final_status = await manager.poll_until_complete(run_id=run_id)

    # Check if workflow finished and delete the cache item
    if final_status:
        await cache_client.delete(key=key)

    return final_status


if __name__ == "__main__":
    manager = WorkflowManager(bearer_token=os.getenv("BEARER_TOKEN"))
    cache_client = CacheAPIClient()

    workflow_payload = {
        "agent_id": "bae08bc3-6160-4838-bcd4-510fea5542cc",
        "template_id": "60c8e694-5dfd-4ba4-9eee-efa1f7d0d5f3",
        "inputs": {
            "accountnumber": "20000000",
            "clientid": "12345678"
        }
    }

    asyncio.run(run_workflow_with_cache(cache_client, manager, workflow_payload))
