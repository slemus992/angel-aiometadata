import json
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
        self.base_url = "https://www.angel.com"

    # ---------------------------

    def movies(self):
        log("Loading movies")
        return self._scrape_page(ANGEL_MOVIES, "movies")

    # ---------------------------

    def shows(self):
        log("Loading shows")
        return self._scrape_page(ANGEL_SHOWS, "shows")

    # ---------------------------

    def _scrape_page(
        self,
        url: str,
        media_type: str,
    ) -> List[Dict]:
        
        log(f"Scraping Angel Studios {media_type} from {url}")
        response = self.session.get(url, timeout=30)
        log(f"Response: HTTP {response.status_code}, {len(response.text)} bytes")
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        script_tag = soup.find("script", id="__NEXT_DATA__")

        if not script_tag:
            log(f"Could not find Next.js data on {url}")
            log(f"Page title tag: {soup.title.string if soup.title else 'none'}")
            log(f"First 300 chars of body: {response.text[:300]!r}")
            return []

        try:
            data = json.loads(script_tag.string)
            json_items = self._extract_media_nodes(data)
            log(f"Found {len(json_items)} raw title/slug nodes in __NEXT_DATA__ before dedup")

            unique_items = self._format_items(json_items, media_type)
            log(f"Found {len(unique_items)} {media_type} using embedded JSON")

            return unique_items
            
        except json.JSONDecodeError:
            log("Failed to parse JSON from page.")
            return []

    # ---------------------------

    def _extract_media_nodes(self, data) -> List[Dict]:
        """Recursively find dictionaries that contain 'slug' and 'title'"""
        nodes = []
        if isinstance(data, dict):
            if "title" in data and "slug" in data:
                nodes.append(data)
            for value in data.values():
                nodes.extend(self._extract_media_nodes(value))
        elif isinstance(data, list):
            for item in data:
                nodes.extend(self._extract_media_nodes(item))
        return nodes

    # ---------------------------

    def _format_items(self, items: List[Dict], content_type: str) -> List[Dict]:
        catalog = []
        seen = set()
        
        for item in items:
            title = item.get("title")
            slug = item.get("slug")
            
            if not title or not slug:
                continue
                
            key = title.lower()
            if key in seen:
                continue
                
            seen.add(key)
                
            catalog.append({
                "title": title,
                "year": item.get("releaseYear") or item.get("year"),
                "slug": slug,
                "angel_url": f"{self.base_url}/{content_type}/{slug}",
                "poster": item.get("posterUrl") or item.get("image"),
                "type": "movie" if content_type == "movies" else "show"
            })
            
        return catalog
