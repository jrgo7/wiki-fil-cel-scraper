import logging
import coloredlogs
import os
import scraper

logger = logging.getLogger(__name__)
coloredlogs.install(level="INFO")


def main():
    logging.info("Starting Wikipedia Scraper")
    wiki_scraper = scraper.WikipediaScraper()
    actors_df = wiki_scraper.scrape()
    os.makedirs("output", exist_ok=True)
    actors_df.to_csv("output/actors.csv", index=False)
    logging.info("Wikipedia Scraper Finished")


if __name__ == "__main__":
    main()
