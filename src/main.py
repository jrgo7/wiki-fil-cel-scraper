import logging
import os
import time

import coloredlogs

from config import CONFIG
from scrape import Scraper

logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")


def main():
    logger.info("Starting the Filipino Actors and Actresses Scraper")
    scrape = Scraper()

    logger.info("Fetching actor and actress links from Wikipedia")
    assert isinstance(CONFIG["OUTPUT_DIR"], str)
    os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
    all_links: list[str] = []
    assert isinstance(CONFIG["BASE_URLS"], list)
    for url in CONFIG["BASE_URLS"]:
        links = scrape.get_actors_links(url)
        all_links.extend(links)
    logger.debug(f"Total links found: {len(all_links)}")

    logger.info("Scraping data for each actor and actress")
    with open(f"{CONFIG['OUTPUT_DIR']}/{CONFIG['OUTPUT_CSV']}", "w") as f:
        f.write("Name,Birthdate,ImageURLs\n")
        for name in all_links:
            birthdate = scrape.get_actor_birthdate(name)
            if birthdate is None:
                logger.warning(f"Birthdate not found for {name}")
                continue
            try:
                images = scrape.get_images(name)
                image_urls = ";".join(images)
            except Exception: # TODO: specify exception
                logger.error(f"Failed to get images for {name}")
                image_urls = ""
            f.write(f'"{name}","{birthdate}","{image_urls}"\n')
            time.sleep(1)
    logger.info("Scraping completed successfully")


if __name__ == "__main__":
    main()
