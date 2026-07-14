from datetime import UTC, datetime

from playwright.async_api import async_playwright

from villascout.models.domain import Villa
from villascout.services.enrichment.parser import WebsiteParser
from villascout.utils.cache import FileCache
from villascout.utils.logging import get_logger


class WebsiteEnricher:
    def __init__(self, cache: FileCache, parser: WebsiteParser | None = None) -> None:
        self.cache = cache
        self.parser = parser or WebsiteParser()
        self.logger = get_logger("enrichment.website")

    async def enrich(self, villa: Villa) -> Villa:
        if villa.contact.website is None:
            return villa
        url = str(villa.contact.website)
        try:
            html = await self._get_html(url)
            amenities, contact, price, images = self.parser.parse(html)
            merged_contact = villa.contact.model_copy(
                update={
                    key: value
                    for key, value in contact.model_dump().items()
                    if value is not None and getattr(villa.contact, key) is None
                }
            )
            return villa.model_copy(
                update={
                    "amenities": villa.amenities.model_copy(
                        update={
                            key: value
                            for key, value in amenities.model_dump().items()
                            if value is not None
                        }
                    ),
                    "contact": merged_contact,
                    "price": price if price.amount is not None else villa.price,
                    "images": list(dict.fromkeys([*villa.images, *images])),
                    "enriched_at": datetime.now(UTC),
                }
            )
        except Exception as exc:
            self.logger.warning(
                "website_enrichment_failed",
                url=url,
                villa=villa.name,
                error=str(exc),
            )
            return villa

    async def _get_html(self, url: str) -> str:
        cached = await self.cache.get_text("websites", url)
        if cached is not None:
            return cached
        self.logger.info("website_request", url=url)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            html = await page.content()
            await browser.close()
        await self.cache.set_text("websites", url, html)
        return html
