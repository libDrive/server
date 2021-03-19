import datetime
import json
import os

import googleapiclient

import src.credentials


def readConfig():
    home_path = os.path.join(
        os.path.expanduser("~"), ".config", "libdrive", "config.json"
    )
    if os.path.exists(home_path):
        path = home_path
    elif os.path.exists("./config.json"):
        path = os.path.join(os.getcwd(), "config.json")
    else:
        dir_path = os.path.join(os.path.expanduser("~"), ".config", "libdrive")
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(home_path, "w+") as w:
            json.dump(
                obj={
                    "access_token": "",
                    "account_list": [],
                    "auth": False,
                    "build_interval": 360,
                    "category_list": [],
                    "client_id": "",
                    "client_secret": "",
                    "cloudflare": "",
                    "refresh_token": "",
                    "secret_key": "",
                    "signup": False,
                    "tmdb_api_key": "",
                    "token_expiry": "",
                    "transcoded": False,
                },
                fp=w,
                sort_keys=True,
                indent=4,
            )
        path = home_path
    with open(path) as r:
        config = json.load(r)
    try:
        datetime.datetime.strptime(config.get("token_expiry"), "%Y-%m-%d %H:%M:%S.%f")
    except:
        config["token_expiry"] = str(datetime.datetime.utcnow())
    return config


def updateConfig(config):
    home_path = os.path.join(
        os.path.expanduser("~"), ".config", "libdrive", "config.json"
    )
    if os.path.exists(home_path):
        path = home_path
    elif os.path.exists("./config.json"):
        path = os.path.join(os.getcwd(), "config.json")
    else:
        path = home_path
    with open(path, "w+") as w:
        json.dump(obj=config, fp=w, sort_keys=True, indent=4)
    if os.getenv("LIBDRIVE_CLOUD"):
        config, drive = src.credentials.refreshCredentials(config)
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
            path, mimetype="application/json", resumable=True
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
