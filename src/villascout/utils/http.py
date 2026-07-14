from collections.abc import Mapping
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from villascout.config import Settings
from villascout.utils.logging import get_logger, redact_mapping


class HttpClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)
        self.logger = get_logger("http")

    async def get_json(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.settings.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((httpx.HTTPError, ValueError)),
            reraise=True,
            before_sleep=self._log_retry,
        ):
            with attempt:
                safe_params = redact_mapping(dict(params or {}))
                self.logger.info("api_request", url=url, params=safe_params)
                response = await self.client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        raise RuntimeError("unreachable retry state")

    async def close(self) -> None:
        await self.client.aclose()

    def _log_retry(self, retry_state: RetryCallState) -> None:
        self.logger.warning(
            "retrying_request",
            attempt=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception()) if retry_state.outcome else None,
        )
