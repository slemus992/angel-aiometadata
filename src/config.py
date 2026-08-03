import os

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 "
        "Chrome/138 Safari/537.36"
    )
}

ANGEL_MOVIES = "https://www.angel.com/movies"
ANGEL_SHOWS = "https://www.angel.com/shows"

TMDB_MOVIE = "https://api.themoviedb.org/3/search/movie"
TMDB_SHOW = "https://api.themoviedb.org/3/search/tv"

OUTPUT_DIR = "output"

# MDBList sync (this is what actually makes the catalog AIOMetadata-compatible;
# AIOMetadata's "mdblist" custom catalog type only pulls from api.mdblist.com,
# it does not accept an arbitrary hosted JSON file)
MDBLIST_API_KEY = os.getenv("MDBLIST_API_KEY")
MDBLIST_LIST_NAME = os.getenv("MDBLIST_LIST_NAME", "Angel Studios")
MDBLIST_API_BASE = "https://api.mdblist.com"
