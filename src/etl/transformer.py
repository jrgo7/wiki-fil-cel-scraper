from requests.exceptions import HTTPError
from requests.models import Response
from IPython.utils.py3compat import decode
import ast
import logging
import os.path

import face_recognition
import pandas as pd
import requests
from tqdm import tqdm
from PIL import Image
from PIL.ExifTags import TAGS
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class Transformer:
    USER_AGENT = "wiki-fil-cel-scraper/1.0 (contact: jrgo.dev@gmail.com)"

    @staticmethod
    def transform(df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrame `df` must have the following columns:
        * name
        * gender
        * birthdate
        * image_urls: str
        """
        df = df.dropna().reset_index(drop=True)
        df["image_urls"] = df["image_urls"].apply(ast.literal_eval)
        df["image_urls_count"] = df["image_urls"].apply(len)
        df = df[df["image_urls_count"] > 0]
        df = (
            df.drop(columns="image_urls_count")
            .explode("image_urls")
            .rename(columns={"image_urls": "image_url"})
        )
        df = df[Transformer.is_face(df["image_url"])]
        return df

    @staticmethod
    def is_face(urls: pd.Series) -> pd.Series:
        def download_url(url):
            response = requests.get(url, headers={"User-Agent": Transformer.USER_AGENT})
            response.raise_for_status()
            with open(file_path, "wb") as fp:
                fp.write(response.content)
        mask = pd.Series()
        os.makedirs("output/images/clean", exist_ok=True)
        for url in tqdm(urls):
            file_path = os.path.join(
                "output", "images", basename := os.path.basename(url)
            )
            logger.info(f"{file_path}")
            try:
                # download_url(url)
                image = face_recognition.load_image_file(file_path)
                face_locations = face_recognition.face_locations(image)
                has_one_face = len(face_locations) == 1
                is_big_enough = image.shape[0] >= 50
                logging.info(f" - {has_one_face = }\t {is_big_enough = }")
            except Exception:
                has_one_face = False
            current = pd.Series([has_one_face and is_big_enough])
            mask = pd.concat([mask, current])

            if has_one_face and is_big_enough:
                os.rename(
                    file_path, os.path.join("output", "images", "clean", basename)
                )
        return mask.to_numpy()

    @staticmethod
    def engineer_features(df_path: str) -> pd.DataFrame:
        df = pd.read_csv(df_path)
        df["path"] = df["image_url"].apply(
            lambda url: os.path.join(basename := os.path.basename(url))
        )
        df["birthdate"] = pd.to_datetime(df["birthdate"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed")
        df.to_csv("output/actors_with_timestamp_birthdate.csv")
        df["age"] = (df["timestamp"] - df["birthdate"]).dt.days / 365.25
        df.dropna(inplace=True)
        return df

    @staticmethod
    def get_timestamp(image_path: str):
        logger.info(f"Getting timestamp for {image_path = }")
        if "px-" in image_path:
            image_path = "".join(image_path.split("px-")[1:])
        url = f"https://commons.wikimedia.org/wiki/File:{os.path.basename(image_path)}"
        logger.info(f"{url = }")
        try:
            response = requests.get(url, headers={"User-Agent": Transformer.USER_AGENT})
            response.raise_for_status()
        except HTTPError:
            # TODO: Use Exif Tags
            logger.warning("No dice")
            return ""
        assert isinstance(response, Response)
        logger.info("Page received; finding timestamp")
        bs4 = BeautifulSoup(response.text, features="html.parser")
        try:
            time_tag = bs4.select_one("time")
            time_val = time_tag.get("datetime")
        except Exception:
            try:
                time_tag = bs4.select_one("#fileinfotpl_date + td")
                time_val = time_tag.string
            except Exception:
                logger.warning("No timestamp found")
                return ""
        logger.info(f"{time_val = }")
        return time_val

    @staticmethod
    def clean_timestamps(df_path: str) -> pd.DataFrame:
        actors_df = pd.read_csv(df_path)
        prefixes = ["\n", "published "]
        suffixes = [" (original upload date)"]
        for prefix in prefixes:
            actors_df["timestamp"] = actors_df["timestamp"].str.removeprefix(prefix)
        for suffix in suffixes:
            actors_df["timestamp"] = actors_df["timestamp"].str.removesuffix(suffix)
        def not_letters_only(input_string):
            return not bool(''.join(c for c in str(input_string) if c.isalpha()))
        actors_df = actors_df[actors_df["timestamp"].apply(not_letters_only)]
        actors_df["birthdate"] = pd.to_datetime(actors_df["birthdate"])
        actors_df["timestamp"] = pd.to_datetime(actors_df["timestamp"], format="mixed")
        return actors_df
