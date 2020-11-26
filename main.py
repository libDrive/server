import os

from src.config import readConfig, writeConfig

if os.path.exists("config.env"):
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, environment = readConfig()
else:
    writeConfig()
