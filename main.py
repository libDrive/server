import os

from src.config import readConfig, writeConfig
from src.credentials import refreshCredentials

if os.path.exists("config.env"):
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, environment = readConfig()
else:
    writeConfig()

drive, access_token = refreshCredentials(
    "", client_id, client_secret, refresh_token, True)
