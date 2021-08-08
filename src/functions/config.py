import datetime
import json
import os

import googleapiclient

import src.functions.credentials


def readConfig():
    if not os.path.exists("./config.json"):
        with open("config.json", "w+") as w:
            json.dump(
                obj={
                    "access_token": None,
                    "account_list": [],
                    "arcio": None,
                    "auth": False,
                    "build_interval": 360,
                    "category_list": [],
                    "client_id": None,
                    "client_secret": None,
                    "cloudflare": None,
                    "kill_switch": False,
                    "refresh_token": None,
                    "secret_key": "",
                    "service_accounts": [],
                    "subtitles": False,
                    "signup": False,
                    "tmdb_api_key": "",
                    "token_expiry": "",
                    "transcoded": False,
                },
                fp=w,
                sort_keys=True,
                indent=4,
            )
    with open("config.json", "r") as r:
        config = json.load(r)
    try:
        datetime.datetime.strptime(config.get("token_expiry"), "%Y-%m-%d %H:%M:%S.%f")
    except:
        config["token_expiry"] = str(datetime.datetime.utcnow())
    return config


def updateConfig(config):
    with open("config.json", "w+") as w:
        json.dump(obj=config, fp=w, sort_keys=True, indent=4)
    if os.getenv("LIBDRIVE_CLOUD"):
        config, drive = src.functions.credentials.refreshCredentials(config)
        params = {
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
            "fields": "files(id,name)",
            "q": "'%s' in parents and trashed = false and mimeType = 'application/json'"
            % (os.getenv("LIBDRIVE_CLOUD")),
        }
        files = drive.files().list(**params).execute()["files"]
        config_file = next((i for i in files if i["name"] == "config.json"), None)
        file_metadata = {
            "name": "config.json",
            "mimeType": "application/json",
            "parents": [os.getenv("LIBDRIVE_CLOUD")],
        }
        media = googleapiclient.http.MediaFileUpload(
            "config.json", mimetype="application/json", resumable=True
        )
        if config_file:
            params = {
                "fileId": config_file["id"],
                "media_body": media,
                "supportsAllDrives": True,
            }
            drive.files().update(**params).execute()
        else:
            params = {
                "body": file_metadata,
                "media_body": media,
                "supportsAllDrives": True,
            }
            drive.files().create(**params).execute()
