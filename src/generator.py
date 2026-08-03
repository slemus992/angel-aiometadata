import json
import hashlib
from pathlib import Path
from tmdb import TMDBMatcher
from config import OUTPUT_DIR
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
        
        complete = movie_catalog + show_catalog
        
        # MDBList expects a flat array of TMDB IDs or IMDb IDs.
        # We will output a simple JSON list of the tmdb_ids.
        mdblist_format = [item["tmdb_id"] for item in complete if "tmdb_id" in item]
        
        self._write_json("angel_mdblist.json", mdblist_format)

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
