"""
Pushes the matched Angel Studios catalog into a real list on mdblist.com.

Why this exists: AIOMetadata's "mdblist" custom catalog type only ever calls
api.mdblist.com under the hood (confirmed by reading its getCatalog.ts source) -
it does not accept an arbitrary self-hosted JSON file as a catalog source.
So the only way to get this data into AIOMetadata as a real Stremio catalog
is to own an actual MDBList list and keep it in sync via MDBList's API.

Request/response shapes below are confirmed against the official open-source
Go CLI (github.com/luckylittle/mdblist-cli), which calls the real
api.mdblist.com endpoints:
  GET  /lists/{id}/items                 -> {"movies": [{"id": <tmdb>, ...}], "shows": [...]}
  POST /lists/{id}/items/add    body {"movies": [{"tmdb": id}], "shows": [{"tmdb": id}]}
  POST /lists/{id}/items/remove same body shape as add

Requires:
  MDBLIST_API_KEY  - from your MDBList account preferences
  MDBLIST_LIST_NAME - name of a list you own on mdblist.com (default: "Angel Studios").
                      Create this once, manually, in the mdblist.com UI - MDBList's
                      API confirmed (via a real 404) that it does not support creating
                      lists programmatically, only reading/modifying existing ones.
                      After that one-time step, everything else here is automatic.
"""

import requests

from config import MDBLIST_API_KEY, MDBLIST_LIST_NAME, MDBLIST_API_BASE
from logger import log


class MDBListSync:

    def __init__(self):
        if not MDBLIST_API_KEY:
            raise ValueError("MDBLIST_API_KEY must be set to sync to MDBList.")
        self.session = requests.Session()
        self.api_key = MDBLIST_API_KEY
        self.list_name = MDBLIST_LIST_NAME
        self.list_id = self._find_list_id()

    # ---------------------------

    def _find_list_id(self):
        r = self.session.get(
            f"{MDBLIST_API_BASE}/lists/user",
            params={"apikey": self.api_key},
            timeout=30,
        )
        r.raise_for_status()
        for lst in r.json():
            if lst.get("name", "").strip().lower() == self.list_name.strip().lower():
                log(f"Found existing MDBList list '{self.list_name}' (id {lst['id']})")
                return lst["id"]

        raise RuntimeError(
            f"No list named '{self.list_name}' found on your MDBList account. "
            f"MDBList doesn't support creating lists via API - go create a static list "
            f"called exactly '{self.list_name}' once at mdblist.com (My Lists > New List), "
            f"then re-run this."
        )

    # ---------------------------

    def sync(self, movie_tmdb_ids, show_tmdb_ids):
        """Reconciles the list on mdblist.com to exactly match the given ID sets."""

        current_movies, current_shows = self._get_current_items()

        wanted_movies = set(movie_tmdb_ids)
        wanted_shows = set(show_tmdb_ids)

        to_add_movies = wanted_movies - current_movies
        to_add_shows = wanted_shows - current_shows

        to_remove_movies = current_movies - wanted_movies
        to_remove_shows = current_shows - wanted_shows

        if to_add_movies or to_add_shows:
            log(f"Adding {len(to_add_movies)} movies, {len(to_add_shows)} shows to MDBList")
            self._modify_items(to_add_movies, to_add_shows, action="add")
        else:
            log("No new items to add to MDBList")

        if to_remove_movies or to_remove_shows:
            log(f"Removing {len(to_remove_movies)} movies, {len(to_remove_shows)} shows from MDBList")
            self._modify_items(to_remove_movies, to_remove_shows, action="remove")
        else:
            log("No stale items to remove from MDBList")

    # ---------------------------

    def _get_current_items(self):
        """Returns (movie_tmdb_ids: set, show_tmdb_ids: set) currently on the list."""

        url = f"{MDBLIST_API_BASE}/lists/{self.list_id}/items"
        params = {"apikey": self.api_key, "limit": 1000}

        movie_ids = set()
        show_ids = set()
        offset = 0

        while True:
            params["offset"] = offset
            r = self.session.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            movies = data.get("movies", [])
            shows = data.get("shows", [])

            # Each item's top-level "id" field is the TMDb id (imdb_id is separate).
            for m in movies:
                if m.get("id"):
                    movie_ids.add(m["id"])

            for s in shows:
                if s.get("id"):
                    show_ids.add(s["id"])

            if len(movies) + len(shows) < params["limit"]:
                break
            offset += params["limit"]

        return movie_ids, show_ids

    # ---------------------------

    def _modify_items(self, movie_ids, show_ids, action):
        if not movie_ids and not show_ids:
            return

        url = f"{MDBLIST_API_BASE}/lists/{self.list_id}/items/{action}"
        params = {"apikey": self.api_key}

        payload = {
            "movies": [{"tmdb": tid} for tid in movie_ids],
            "shows": [{"tmdb": tid} for tid in show_ids],
        }

        r = self.session.post(url, params=params, json=payload, timeout=30)

        if not r.ok:
            log(f"MDBList sync request failed ({r.status_code}): {r.text[:300]}")
        r.raise_for_status()
