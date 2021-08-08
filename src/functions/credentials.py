import random

import googleapiclient.discovery
import httplib2
import oauth2client
from oauth2client.service_account import ServiceAccountCredentials


def refreshCredentials(config):
    service_acconts = config.get("service_accounts")
    if type(service_acconts) == list:
        if len(service_acconts) > 0:
            random_sa = random.choice(service_acconts)
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                random_sa,
                "https://www.googleapis.com/auth/drive",
                "https://accounts.google.com/o/oauth2/token",
            )
        else:
            credentials = oauth2client.client.GoogleCredentials(
                config.get("access_token"),
                config.get("client_id"),
                config.get("client_secret"),
                config.get("refresh_token"),
                None,
                "https://accounts.google.com/o/oauth2/token",
                None,
            )
    else:
        credentials = oauth2client.client.GoogleCredentials(
            config.get("access_token"),
            config.get("client_id"),
            config.get("client_secret"),
            config.get("refresh_token"),
            None,
            "https://accounts.google.com/o/oauth2/token",
            None,
        )
    http = credentials.authorize(httplib2.Http())
    credentials.refresh(http)
    config["access_token"] = credentials.access_token
    config["token_expiry"] = str(credentials.token_expiry)
    drive = googleapiclient.discovery.build("drive", "v3", credentials=credentials)
    return config, drive
