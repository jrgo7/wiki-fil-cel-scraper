CONFIG: dict[str, list[str] | str | bool] = {
    "BASE_URLS": [
        "https://en.wikipedia.org/wiki/List_of_Filipino_male_actors",
        "https://en.wikipedia.org/wiki/List_of_Filipino_actresses",
    ],
    "OUTPUT_DIR": "output",
    "OUTPUT_CSV": "filipino_actors_actresses.csv",
    "USER_AGENT": "wiki-fil-cel-scraper/1.0 (contact: jrgo.dev@gmail.com)",
    "API_ENDPOINT": "https://en.wikipedia.org/w/api.php",
}
