import json
import os

import requests

from src.config import readConfig, writeConfig
from src.credentials import refreshCredentials
from src.metadata import writeMetadata

if os.path.exists("config.env"):
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, environment = readConfig()
else:
    writeConfig()
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, environment = readConfig()

drive, access_token = refreshCredentials(
    "", client_id, client_secret, refresh_token, True)

configuration_url = "http://api.themoviedb.org/3/configuration?api_key=" + tmdb_api_key
configuration_content = json.loads(
    (requests.get(configuration_url)).content)
backdrop_base_url = configuration_content["images"]["base_url"] + \
    configuration_content["images"]["backdrop_sizes"][3]
poster_base_url = configuration_content["images"]["base_url"] + \
    configuration_content["images"]["poster_sizes"][3]

metadata = writeMetadata(category_list, drive, tmdb_api_key, backdrop_base_url, poster_base_url)
