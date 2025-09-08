import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HTTPClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return self._client

    async def post(self, url: str, headers: Dict[str, str], json_data: Dict[str, Any]) -> Dict[str, Any]:
        client = await self.get_client()
        try:
            response = await client.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error for {url}: {str(e)}")
            raise

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

http_client = HTTPClient()