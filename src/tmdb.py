import requests
from rapidfuzz import fuzz

from config import (
    TMDB_API_KEY,
    TMDB_MOVIE,
    TMDB_SHOW,
)

from logger import log


class TMDBMatcher:

    def __init__(self):

        self.session = requests.Session()

        self.cache = {}

    # -----------------------------------------------------

    def match_movie(self, title, year=None):

        return self._search(
            title,
            year,
            TMDB_MOVIE,
            "movie"
        )

    # -----------------------------------------------------

    def match_show(self, title, year=None):

        return self._search(
            title,
            year,
            TMDB_SHOW,
            "tv"
        )

    # -----------------------------------------------------

    def _search(
        self,
        title,
        year,
        endpoint,
        media_type
    ):

        key = (media_type, title.lower(), year)

        if key in self.cache:
            return self.cache[key]

        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "include_adult": False,
        }

        if year:
            if media_type == "movie":
                params["year"] = year
            else:
                params["first_air_date_year"] = year

        r = self.session.get(
            endpoint,
            params=params,
            timeout=30
        )

        r.raise_for_status()

        data = r.json()

        results = data.get("results", [])

        if not results:

            log(f"No TMDb match: {title}")

            self.cache[key] = None

            return None

        best = self._best_match(
            title,
            year,
            results,
            media_type
        )

        self.cache[key] = best

        return best

    # -----------------------------------------------------

    def _best_match(
        self,
        wanted_title,
        wanted_year,
        results,
        media_type
    ):

        highest = -1

        winner = None

        for item in results:

            if media_type == "movie":
                candidate = item.get("title", "")
                date = item.get("release_date", "")
            else:
                candidate = item.get("name", "")
                date = item.get("first_air_date", "")

            score = fuzz.token_sort_ratio(
                wanted_title.lower(),
                candidate.lower()
            )

            if wanted_year and date:

                try:

                    tmdb_year = int(date[:4])

                    diff = abs(tmdb_year - wanted_year)

                    if diff == 0:
                        score += 15
                    elif diff == 1:
                        score += 8
                    elif diff > 2:
                        score -= 15

                except Exception:
                    pass

            if score > highest:

                highest = score

                winner = item

        if highest < 70:

            log(f"Rejected weak match ({highest}) : {wanted_title}")

            return None

        return {
            "tmdb_id": winner["id"],
            "title": winner.get("title")
            or winner.get("name"),
            "overview": winner.get("overview"),
            "poster": winner.get("poster_path"),
            "backdrop": winner.get("backdrop_path"),
            "rating": winner.get("vote_average"),
            "votes": winner.get("vote_count"),
            "language": winner.get("original_language"),
            "popularity": winner.get("popularity"),
            "year": (
                winner.get("release_date")
                or winner.get("first_air_date", "")
            )[:4],
            "media_type": media_type,
        }
