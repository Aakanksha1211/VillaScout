import re
from collections.abc import Iterable

from bs4 import BeautifulSoup

from villascout.models.domain import AmenitySet, Contact, Price


class WebsiteParser:
    email_pattern = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    phone_pattern = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}")
    price_pattern = re.compile(r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.\d+)?)", re.IGNORECASE)

    def parse(self, html: str) -> tuple[AmenitySet, Contact, Price, list[str]]:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        lower_text = text.lower()
        links = [anchor.get("href", "") for anchor in soup.find_all("a")]
        images = [img.get("src", "") for img in soup.find_all("img") if img.get("src")]
        return (
            AmenitySet(
                bedrooms=self._number_near(text, ["bedroom", "bedrooms", "bhk"]),
                bathrooms=self._number_near(text, ["bathroom", "bathrooms", "bath"]),
                guests=self._number_near(text, ["guest", "guests", "sleeps", "occupancy"]),
                pool=self._contains(lower_text, ["pool", "swimming pool"]),
                private_pool=self._contains(lower_text, ["private pool"]),
                bbq=self._contains(lower_text, ["bbq", "barbecue", "barbeque"]),
                bonfire=self._contains(lower_text, ["bonfire", "campfire"]),
                parking=self._contains(lower_text, ["parking", "car park"]),
                wifi=self._contains(lower_text, ["wifi", "wi-fi", "wireless internet"]),
                pet_friendly=self._contains(lower_text, ["pet friendly", "pets allowed"]),
                caretaker=self._contains(lower_text, ["caretaker", "care taker", "housekeeper"]),
                check_in=self._time_near(text, ["check-in", "check in"]),
                check_out=self._time_near(text, ["check-out", "check out"]),
            ),
            Contact(
                email=self._first_match(self.email_pattern, text),
                phone=self._first_match(self.phone_pattern, text),
                whatsapp=self._first_containing(links, ["wa.me", "whatsapp"]),
                instagram=self._first_containing(links, ["instagram.com"]),
            ),
            self._parse_price(text),
            images,
        )

    def _parse_price(self, text: str) -> Price:
        match = self.price_pattern.search(text)
        if match is None:
            return Price()
        raw = match.group(0)
        return Price(amount=float(match.group(1).replace(",", "")), currency="INR", raw_text=raw)

    @staticmethod
    def _contains(text: str, needles: Iterable[str]) -> bool:
        return any(needle in text for needle in needles)

    @staticmethod
    def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        return match.group(0) if match else None

    @staticmethod
    def _first_containing(values: Iterable[str], needles: Iterable[str]) -> str | None:
        return next((value for value in values if any(needle in value for needle in needles)), None)

    @staticmethod
    def _number_near(text: str, labels: Iterable[str]) -> int | None:
        for label in labels:
            patterns = [
                rf"(\d+)\s+{re.escape(label)}",
                rf"{re.escape(label)}\s*[:\-]?\s*(\d+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    return int(match.group(1))
        return None

    @staticmethod
    def _time_near(text: str, labels: Iterable[str]) -> str | None:
        for label in labels:
            match = re.search(
                rf"{re.escape(label)}\s*[:\-]?\s*([0-2]?\d(?::[0-5]\d)?\s*(?:am|pm)?)",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                return match.group(1)
        return None
