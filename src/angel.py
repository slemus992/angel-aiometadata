import json
import re
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from config import (
    ANGEL_MOVIES,
    ANGEL_SHOWS,
    HEADERS,
)

from logger import log


class AngelScraper:

    def __init__(self):

        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ---------------------------

    def movies(self):

        log("Loading movies")

        return self._scrape_page(
            ANGEL_MOVIES,
            "movie"
        )

    # ---------------------------

    def shows(self):

        log("Loading shows")

        return self._scrape_page(
            ANGEL_SHOWS,
            "show"
        )

    # ---------------------------

    def _scrape_page(
        self,
        url: str,
        media_type: str,
    ) -> List[Dict]:

        response = self.session.get(url, timeout=30)

        response.raise_for_status()

        html = response.text

        # ----------------------------------
        # First attempt:
        # Angel often embeds JSON data.
        # ----------------------------------

        json_items = self._extract_json(html)

        if json_items:

            log(f"Found {len(json_items)} {media_type}s using embedded JSON")

            return json_items

        log("No embedded JSON found")

        log("Falling back to HTML parsing")

        return self._extract_html(html, media_type)

    # ---------------------------

    def _extract_json(
        self,
        html: str
    ) -> List[Dict]:

        soup = BeautifulSoup(
            html,
            "lxml"
        )

        scripts = soup.find_all("script")

        results = []

        for script in scripts:

            if not script.string:
                continue

            text = script.string

            # Look for title objects

            matches = re.findall(
                r'"title":"(.*?)"',
                text
            )

            years = re.findall(
                r'"releaseYear":(\d+)',
                text
            )

            if not matches:
                continue

            for index, title in enumerate(matches):

                year = None

                if index < len(years):

                    year = int(years[index])

                results.append(
                    {
                        "title": title,
                        "year": year,
                    }
                )

        unique = []

        seen = set()

        for item in results:

            key = item["title"].lower()

            if key in seen:
                continue

            seen.add(key)

            unique.append(item)

        return unique

    # ---------------------------

    def _extract_html(
        self,
        html: str,
        media_type: str,
    ) -> List[Dict]:

        soup = BeautifulSoup(
            html,
            "lxml"
        )

        results = []

        seen = set()

        candidates = soup.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "span",
                "a",
            ]
        )

        for node in candidates:

            text = node.get_text(
                strip=True
            )

            if len(text) < 2:
                continue

            if len(text) > 120:
                continue

            if text.lower() in seen:
                continue

            if any(
                word in text.lower()
                for word in (
                    "browse",
                    "continue",
                    "watch now",
                    "episode",
                    "season",
                    "login",
                    "account",
                    "gift",
                    "pricing",
                )
            ):
                continue

            seen.add(text.lower())

            results.append(
                {
                    "title": text,
                    "year": None,
                }
            )

        return results
