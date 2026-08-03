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

            if not json_items:
                # The site's data shape probably changed. Find any dict that has
                # a "slug" key at all (regardless of what else is next to it) so
                # we can see what key names replaced "title".
                slug_nodes = self._find_nodes_with_key(data, "slug")
                log(f"Diagnostic: found {len(slug_nodes)} nodes containing a 'slug' key")
                if slug_nodes:
                    sample_keys = sorted(slug_nodes[0].keys())
                    log(f"Diagnostic: keys on a sample 'slug' node: {sample_keys}")
                    log(f"Diagnostic: sample node (truncated): {str(slug_nodes[0])[:400]}")

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

    def _find_nodes_with_key(self, data, key) -> List[Dict]:
        """Diagnostic helper: finds any dict containing the given key, anywhere in the tree."""
        nodes = []
        if isinstance(data, dict):
            if key in data:
                nodes.append(data)
            for value in data.values():
                nodes.extend(self._find_nodes_with_key(value, key))
        elif isinstance(data, list):
            for item in data:
                nodes.extend(self._find_nodes_with_key(item, key))
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
