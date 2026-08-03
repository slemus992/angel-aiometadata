import json
import hashlib
from pathlib import Path
from tmdb import TMDBMatcher
from mdblist_sync import MDBListSync
from config import OUTPUT_DIR, MDBLIST_API_KEY
from logger import log

class Generator:
    def __init__(self, movies, shows):
        self.movies = movies
        self.shows = shows
        self.matcher = TMDBMatcher()
        Path(OUTPUT_DIR).mkdir(exist_ok=True)

    def generate(self):
        log("Matching movies")
        movie_catalog = self._build_catalog(self.movies, is_movie=True)
        
        log("Matching shows")
        show_catalog = self._build_catalog(self.shows, is_movie=False)

        movie_ids = [item["tmdb_id"] for item in movie_catalog]
        show_ids = [item["tmdb_id"] for item in show_catalog]

        # Kept as a local snapshot/debug artifact and for change detection -
        # this file itself is NOT what AIOMetadata reads. See mdblist_sync.py
        # for why a hosted JSON file can't be used as an AIOMetadata catalog
        # source directly.
        self._write_json("angel_mdblist.json", {"movies": movie_ids, "shows": show_ids})

        if MDBLIST_API_KEY:
            log("Syncing catalog to MDBList")
            MDBListSync().sync(movie_ids, show_ids)
        else:
            log(
                "MDBLIST_API_KEY not set - skipping MDBList sync. "
                "Set it to actually push this catalog into AIOMetadata-compatible form "
                "(the list itself is auto-created on first run)."
            )

    def _build_catalog(self, items, is_movie=True):
        catalog = []
        seen = set()
        
        for item in items:
            title = item["title"]
            year = item.get("year")
            
            if is_movie:
                match = self.matcher.match_movie(title, year)
            else:
                match = self.matcher.match_show(title, year)
                
            if not match:
                log(f"Could not find TMDb match for: {title}")
                continue
                
            if match["tmdb_id"] in seen:
                continue
                
            seen.add(match["tmdb_id"])
            catalog.append(match)
            
        return catalog

    def _write_json(self, filename, data):
        path = Path(OUTPUT_DIR) / filename
        text = json.dumps(data, indent=4)
        
        new_hash = hashlib.sha256(text.encode()).hexdigest()
        
        if path.exists():
            old_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if old_hash == new_hash:
                log(f"{filename} unchanged")
                return
                
        path.write_text(text, encoding="utf-8")
        log(f"Updated {filename}")
