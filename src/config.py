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
