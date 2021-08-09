import os
import urllib

import flask
import requests
import src.functions.config

streammapBP = flask.Blueprint("streammap", __name__)


@streammapBP.route("/api/v1/streammap")
async def streammapFunction():
    a = flask.request.args.get("a")  # AUTH
    id = flask.request.args.get("id")  # ID
    name = flask.request.args.get("name")  # NAME
    server = flask.request.args.get("server")  # SERVER
    config = src.functions.config.readConfig()

    if config.get("kill_switch") == True:
        return flask.jsonify(
            {
                "code": 200,
                "content": [{"name": "UNAVAILABLE", "url": "", "type": "normal"}],
                "message": "Stream list generated successfully.",
                "success": True,
            }
        )

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        stream_list = [
            {
                "name": "Original",
                "url": "%s/api/v1/redirectdownload/%s?a=%s&id=%s"
                % (server, urllib.parse.quote(name), a, id),
                "type": "normal",
            }
        ]
        if config.get("transcoded") == True:
            req = requests.get(
                "https://drive.google.com/get_video_info?docid=%s" % (id),
                headers={"Authorization": "Bearer %s" % (config.get("access_token"))},
            )
            parsed = urllib.parse.parse_qs(urllib.parse.unquote(req.text))
            if parsed.get("status") == ["ok"]:
                for fmt in parsed["fmt_list"][0].split(","):
                    fmt_data = fmt.split("/")
                    stream_list.append(
                        {
                            "name": fmt_data[1],
                            "url": "%s/api/v1/redirectdownload/%s?a=%s&id=%s&itag=%s"
                            % (server, urllib.parse.quote(name), a, id, fmt_data[0]),
                            "type": "auto",
                        }
                    )

        subtitle = {"url": ""}
        if config.get("subtitles") == True:
            config, drive = src.functions.credentials.refreshCredentials(
                src.functions.config.readConfig()
            )
            params = {
                "supportsAllDrives": True,
                "fields": "parents",
                "fileId": id,
            }
            parent = drive.files().get(**params).execute()["parents"][0]
            params = {
                "pageToken": None,
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
                "fields": "files(id,name,mimeType,parents), incompleteSearch, nextPageToken",
                "q": "'%s' in parents and trashed = false and (name contains '.srt' or name contains '.vtt')"
                % (parent),
                "orderBy": "name",
            }
            while True:
                response = drive.files().list(**params).execute()
                for file in response["files"]:
                    name_split = os.path.splitext(name)[0]
                    if name_split in file["name"]:
                        subtitle = {
                            "url": "%s/api/v1/subtitledownload/%s?a=%s&id=%s"
                            % (server, file["name"], a, file["id"])
                        }
                try:
                    params["pageToken"] = response["nextPageToken"]
                except KeyError:
                    break

        if (
            config.get("prefer_mkv") == False
            and config.get("prefer_mp4") == False
            and len(stream_list) > 1
        ):
            default_quality = 1
        elif config.get("prefer_mp4", True) == True and name.endswith(".mp4"):
            default_quality = 0
        elif config.get("prefer_mkv", False) == True and name.endswith(".mkv"):
            default_quality = 0
        elif len(stream_list) > 1:
            default_quality = 1
        else:
            default_quality = 0

        return flask.jsonify(
            {
                "code": 200,
                "content": {
                    "default_quality": default_quality,
                    "sources": stream_list,
                    "subtitle": subtitle,
                },
                "message": "Stream list generated successfully!",
                "success": True,
            }
        )
    else:
        return (
            flask.jsonify(
                {
                    "code": 401,
                    "content": None,
                    "message": "Your credentials are invalid.",
                    "success": False,
                }
            ),
            401,
        )
