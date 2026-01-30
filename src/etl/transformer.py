import ast
import logging
import os.path

import face_recognition
import pandas as pd
import requests
from tqdm import tqdm

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
        mask = pd.Series()
        os.makedirs("output/images/clean", exist_ok=True)
        for url in tqdm(urls):
            file_path = os.path.join("output", "images", basename := os.path.basename(url))
            logger.info(f"{file_path}")
            try:
                response = requests.get(url, headers={"User-Agent": Transformer.USER_AGENT})
                response.raise_for_status()
                with open(file_path, "wb") as fp:
                    fp.write(response.content)
                image = face_recognition.load_image_file(file_path)
                face_locations = face_recognition.face_locations(image)
                has_one_face = len(face_locations) == 1
                at_least_250px = image.shape[0] >= 250
                logging.info(f" - {has_one_face = }\t {at_least_250px}")
            except Exception:
                has_one_face = False
            current = pd.Series([has_one_face and at_least_250px])
            mask = pd.concat([mask, current])

            if has_one_face and at_least_250px:
                os.rename(file_path, os.path.join("output", "images", "clean", basename))
        return mask.to_numpy()