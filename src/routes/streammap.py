import pathlib
import urllib

import flask
import requests
import src.functions.config
import src.functions.metadata

streammapBP = flask.Blueprint("streammap", __name__)


@streammapBP.route("/api/v1/streammap")
async def streammapFunction():
    a = flask.request.args.get("a")  # AUTH
    id = flask.request.args.get("id")  # ID
    name = flask.request.args.get("name")  # NAME
    parent = flask.request.args.get("parent")  # PARENT
    t = flask.request.args.get("t")  # TYPE
    server = flask.request.args.get("server")  # SERVER
    config = src.functions.config.readConfig()

    if config.get("kill_switch") == True:
        return flask.jsonify(
            {
                "code": 200,
                "content": [{"name": "UNAVAILABLE", "url": "", "type": "auto"}],
                "message": "Stream map was not generated because the kill_switch is enabled.",
                "success": True,
            }
        )

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        videos = [
            {
                "name": "Original",
                "url": "%s/api/v1/redirectdownload/%s?a=%s&id=%s"
                % (server, urllib.parse.quote(name), a, id),
                "type": "auto",
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
                    videos.append(
                        {
                            "name": fmt_data[1],
                            "url": "%s/api/v1/redirectdownload/%s?a=%s&id=%s&itag=%s"
                            % (server, urllib.parse.quote(name), a, id, fmt_data[0]),
                            "type": "auto",
                        }
                    )

        tracks = []
        if (
            config.get("fetch_assets") == True
            and t != "directory"
            and parent != None
            and parent != ""
        ):
            config, drive = src.functions.credentials.refreshCredentials(
                src.functions.config.readConfig()
            )
            og_title, og_year = src.functions.metadata.parseMovie(name)
            if og_title == None:
                og_name_path = pathlib.Path(name)
                og_title = og_name_path.stem
            params = {
                "pageToken": None,
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
                "fields": "files(id,name,mimeType,parents,videoMediaMetadata), incompleteSearch, nextPageToken",
                "q": "'%s' in parents and trashed = false and ((mimeType contains 'video' and name contains '%s') or name contains '.srt' or name contains '.vtt')"
                % (parent, og_title),
                "orderBy": "name",
            }
            try:
                response = drive.files().list(**params).execute()
            except:
                response = {"files": []}
            for file in response["files"]:
                title, year = src.functions.metadata.parseMovie(file["name"])
                extention = pathlib.Path(file["name"]).suffix
                if id != file["id"]:
                    if (
                        "video" in file["mimeType"]
                        and title == og_title
                        and year == og_year
                    ):
                        if file.get("videoMediaMetadata"):
                            videoMediaMetadata = file["videoMediaMetadata"]
                        else:
                            videoMediaMetadata = {"width": "null", "height": "null"}
                        videos.append(
                            {
                                "name": "%sx%s"
                                % (
                                    videoMediaMetadata.get("width", "null"),
                                    videoMediaMetadata.get("height", "null"),
                                ),
                                "url": "%s/api/v1/redirectdownload/%s?a=%s&id=%s"
                                % (server, urllib.parse.quote(file["name"]), a, id),
                                "type": "auto",
                            }
                        )
                    elif extention in [".srt", ".vtt"]:
                        tracks.append(
                            {
                                "name": file["name"],
                                "url": "%s/api/v1/subtitledownload/%s?a=%s&id=%s"
                                % (server, file["name"], a, file["id"]),
                            }
                        )
        if (
            config.get("prefer_mkv") == False
            and config.get("prefer_mp4") == False
            and len(videos) > 1
        ):
            default_video = 1
        elif config.get("prefer_mp4", True) == True and name.endswith(".mp4"):
            default_video = 0
        elif config.get("prefer_mkv", False) == True and name.endswith(".mkv"):
            default_video = 0
        elif len(videos) > 1:
            default_video = 1
        else:
            default_video = 0

        return flask.jsonify(
            {
                "code": 200,
                "content": {
                    "default_track": 0,
                    "default_video": default_video,
                    "tracks": tracks,
                    "videos": videos,
                },
                "message": "Stream map generated successfully.",
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
