import logging
from typing import Optional

import requests
import wikipediaapi
from bs4 import BeautifulSoup

from config import CONFIG

logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self):
        assert isinstance(CONFIG["USER_AGENT"], str)
        self.wiki_wiki = wikipediaapi.Wikipedia(
            CONFIG["USER_AGENT"], "en", extract_format=wikipediaapi.ExtractFormat.HTML
        )

    def get_images(self, page_title: str) -> list[str]:
        # TODO
        return []

    def get_actor_birthdate(self, page_title: str) -> Optional[str]:
        logger.info(f"Scraping data for: {page_title}")
        # page = self.wiki_wiki.page(page_title)
        page = requests.get(
            f"https://en.wikipedia.org/wiki/{page_title}",
            headers={"User-Agent": CONFIG["USER_AGENT"]},
        )
        soup = BeautifulSoup(page.text, "html.parser")
        print(soup)
        bday_span = soup.find("span", {"class": "bday"})
        if bday_span:
            return bday_span.text
        return None

    def get_actors_links(self, list_url: str) -> list[str]:
        logging.info(f"Fetching actor links from: {list_url}")
        page = self.wiki_wiki.page(
            list_url.replace("https://en.wikipedia.org/wiki/", "")
        )
        logging.debug(page.links)
        links = list(page.links.keys())

        def clean_links(links: list[str]) -> list[str]:
            return list(
                filter(
                    lambda x: all(
                        [
                            all(
                                [
                                    c not in x
                                    for c in [
                                        ":",
                                        "#",
                                        "Wiki",
                                        "List_of",
                                        "Category",
                                        "Template",
                                        "File",
                                    ]
                                ]
                            ),
                        ]
                    ),
                    links,
                )
            )

        return clean_links(links)
