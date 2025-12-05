import json
import requests

from anilibria.functions import get_path

latest, latestLink = get_path()

def catalog_request(search_query, results_limit):
    if search_query:
        searchPar = {
            "limit": results_limit,
            "f[search]": search_query,
            "include": "id,name.main,type.description,episodes_total",
        }
    else:
        searchPar = {
            "limit": results_limit,
            "include": "id,name.main,type.description,episodes_total",
        }
    response = json.loads(
        requests.get(
            "https://api.anilibria.app/api/v1/anime/catalog/releases/?",
            params=searchPar,
        ).text
    )
    return response["data"]

def get_title(title_id):
    if title_id is not None:
        titlePar = {"exclude": "poster,description,genres,members"}
        url = (
            "https://api.anilibria.app/api/v1/anime/releases/"
            + title_id
            + "?"
        )
        title = json.loads(requests.get(url, params=titlePar).text)
        episodes = title["episodes"]
        latest.write_text(url)
    else:
        titlePar = {"exclude": "poster,description,genres,members"}
        url = latest.read_text()
        title = json.loads(requests.get(url, params=titlePar).text)
        episodes = title["episodes"]
    return title, episodes