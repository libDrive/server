import os

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

metadata = writeMetadata(category_list, drive)
