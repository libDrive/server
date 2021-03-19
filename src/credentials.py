import json

import googleapiclient.discovery
import httplib2
import oauth2client


def refreshCredentials(config):
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
    with open("config.json", "w+") as w:
        json.dump(obj=config, fp=w, sort_keys=True, indent=4)

    return config, drive
