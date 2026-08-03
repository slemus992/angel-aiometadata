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

        Path(OUTPUT_DIR).mkdir(
            exist_ok=True
        )

    # -------------------------------------------------

    def generate(self):

        log("Matching movies")

        movie_catalog = self._build_movies()

        log("Matching shows")

        show_catalog = self._build_shows()

        complete = movie_catalog + show_catalog

        complete.sort(
            key=lambda x: x["title"].lower()
        )

        self._write_json(
            "angel_movies.json",
            movie_catalog
        )

        self._write_json(
            "angel_shows.json",
            show_catalog
        )

        self._write_json(
            "angel_complete.json",
            complete
        )

    # -------------------------------------------------

    def _build_movies(self):

        catalog = []

        seen = set()

        for movie in self.movies:

            title = movie["title"]

            year = movie.get("year")

            match = self.matcher.match_movie(
                title,
                year
            )

            if not match:
                continue

            if match["tmdb_id"] in seen:
                continue

            seen.add(match["tmdb_id"])

            catalog.append(match)

        catalog.sort(
            key=lambda x: x["title"].lower()
        )

        return catalog

    # -------------------------------------------------

    def _build_shows(self):

        catalog = []

        seen = set()

        for show in self.shows:

            title = show["title"]

            year = show.get("year")

            match = self.matcher.match_show(
                title,
                year
            )

            if not match:
                continue

            if match["tmdb_id"] in seen:
                continue

            seen.add(match["tmdb_id"])

            catalog.append(match)

        catalog.sort(
            key=lambda x: x["title"].lower()
        )

        return catalog

    # -------------------------------------------------

    def _write_json(
        self,
        filename,
        data
    ):

        path = Path(
            OUTPUT_DIR
        ) / filename

        text = json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )

        new_hash = hashlib.sha256(
            text.encode()
        ).hexdigest()

        if path.exists():

            old_hash = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()

            if old_hash == new_hash:

                log(f"{filename} unchanged")

                return

        path.write_text(
            text,
            encoding="utf-8"
        )

        log(f"Updated {filename}")
