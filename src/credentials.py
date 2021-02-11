import json

import googleapiclient.discovery
import httplib2
import oauth2client


def refreshCredentials(config):
    credentials = oauth2client.client.GoogleCredentials(
        "", config["client_id"], config["client_secret"], config["refresh_token"], None, "https://accounts.google.com/o/oauth2/token", None)
    http = credentials.authorize(httplib2.Http())
    credentials.refresh(http)
    config["access_token"] = credentials.access_token
    config["token_expiry"] = str(credentials.token_expiry)
    drive = googleapiclient.discovery.build(
        "drive", "v3", credentials=credentials)
    with open("config.json", "w+") as w:
        json.dump(config, w)

    return config, drive
