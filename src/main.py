import logging
import coloredlogs
import os
from etl import scraper
from etl.transformer import Transformer
import pandas as pd

logger = logging.getLogger(__name__)
coloredlogs.install(level="INFO")


def main():
    os.makedirs("output", exist_ok=True)
    scrape()
    transform("output/actors.csv")


def scrape():
    logging.info("Scraping Wikipedia")
    wiki_scraper = scraper.WikipediaScraper()
    actors_df = wiki_scraper.scrape()
    actors_df.to_csv("output/actors.csv", index=False)


def transform(actors_df_path):
    actors_df = pd.read_csv(actors_df_path)
    logging.info("Transforming Wikipedia")
    actors_df = Transformer.transform(actors_df)
    actors_df.to_csv("output/actors_cleaned.csv", index=False)


if __name__ == "__main__":
    main()
