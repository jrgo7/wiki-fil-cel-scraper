from curses import meta
import logging
import urllib.parse

import pandas as pd
import requests
import wikipediaapi
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self):
        self._user_agent = "wiki-fil-cel-scraper/1.0 (contact: jrgo.dev@gmail.com)"

    def scrape():
        raise NotImplementedError


class WikipediaScraper(Scraper):
    def __init__(self):
        super().__init__()
        self.wikipedia = wikipediaapi.Wikipedia(self._user_agent)
        self.wikipedia_path = "https://en.wikipedia.org/wiki/"

    def scrape(self) -> pd.DataFrame:
        actors_urls: list[dict[str, str]] = [
            {
                "title": "List_of_Filipino_male_actors",
                "gender": "male",
            },
            {
                "title": "List_of_Filipino_actresses",
                "gender": "female",
            },
        ]
        actors_df = pd.concat(
            [
                pd.DataFrame(
                    data={
                        "name": self.get_links(entry["title"]),
                        "gender": entry["gender"],
                    }
                )
                for entry in actors_urls
            ]
        )
        actors_df.sort_values("name", inplace=True)
        actors_df = self.get_metadata(actors_df)
        return actors_df

    def get_links(self, title: str) -> list[str]:
        page = self.wikipedia.page(title)
        assert isinstance(page, wikipediaapi.WikipediaPage)
        links = page.links.keys()
        links = list(
            filter(
                lambda link: all(
                    [
                        substring not in link
                        for substring in [
                            ":",
                            "#",
                            "Wiki",
                            "List of",
                            "Metro Manila",
                            "Film Festival",
                            "Outsourcing",
                            "Filipino animation",
                            "Filipino people",
                            "Movie",
                            "Category",
                            "Template",
                            "File",
                            "Award",
                            "Actress",
                            "Animation",
                            "Cinema",
                            "Philippines",
                            "Circle"
                        ]
                    ]
                ),
                links,
            )
        )
        links = list(filter(lambda link: links.count(link) == 1, links))
        pd.DataFrame(links).to_csv("links.csv")
        return links

    def get_metadata(self, actors_df: pd.DataFrame) -> pd.DataFrame:
        data = {
            "wikipedia_url": [],
            "name": [],
            "birthdate": [],
            "image_urls": [],
        }
        for i, actor in tqdm(enumerate(actors_df["name"].to_list())):
            url = f"{self.wikipedia_path}{urllib.parse.quote(actor)}"
            logging.info(f"Getting metadata for {actor} ({url = })")
            response = requests.get(
                url,
                headers={"User-Agent": self._user_agent},
            )
            soup = BeautifulSoup(response.text, "html.parser")

            try:
                birthdate = self.find_birthdate(soup)
            except AttributeError:  # no bday text
                logger.warning("No birthday text found")
                birthdate = ""

            try:
                image_urls = self.find_images(soup)
            except AssertionError:
                logger.warning("No image URLs found")
                image_urls = []

            data["wikipedia_url"].append(url)
            data["name"].append(actor)
            data["birthdate"].append(birthdate)
            data["image_urls"].append(image_urls)

            if i % 200 == 0:
                logging.info(
                    "Checkpoint triggered. Saving current progress to checkpoint.csv"
                )
                metadata_df = pd.DataFrame(data)
                pd.merge(actors_df, metadata_df).to_csv("output/checkpoint.csv", index=False)

        metadata_df = pd.DataFrame(data)
        return pd.merge(actors_df, metadata_df)

    def find_birthdate(self, soup) -> str:
        bday_tag = soup.find("span", {"class": "bday"})
        return bday_tag.text.strip()

    def find_images(self, soup) -> list[str]:
        image_urls = []
        # infobox = soup.find("table", {"class": "infobox"})
        # assert(isinstance(infobox, Tag))
        # img_tags = infobox.find_all("img")
        img_tags = soup.find_all("img")
        if img_tags:
            for img_tag in img_tags:
                assert isinstance(img_tag, Tag)
                src = img_tag.get("src")
                if (
                    src.startswith("/static/images/")
                    or ".svg" in src
                    or "Special:" in src
                ):
                    continue
                print(src)
                if src.startswith("//"):
                    image_urls.append("https:" + src)
                else:
                    image_urls.append(src)
        return image_urls
