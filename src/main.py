from angel import AngelScraper
from generator import Generator
from logger import log


def main():

    log("Starting Angel sync")

    scraper = AngelScraper()

    movies = scraper.movies()

    shows = scraper.shows()

    Generator(movies, shows).generate()

    log("Finished")


if __name__ == "__main__":
    main()
