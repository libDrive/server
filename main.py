import base64
import datetime
import io
import json
import os
import random
import re
import sys
import threading
import urllib

import apscheduler.schedulers.background
import colorama
import flask
import flask_cors
import googleapiclient
import requests
from PIL import Image, ImageDraw, ImageFont

import src.config
import src.credentials
import src.metadata

colorama.init()
print(
    "====================================================\n\033[96m               libDrive - \033[92mv1.2.5\033[94m\n                   @eliasbenb\033[0m\n====================================================\n"
)


print("\033[91mREADING CONFIG...\033[0m")
if os.getenv("LIBDRIVE_CONFIG"):
    config_str = os.getenv("LIBDRIVE_CONFIG")
    dir_path = os.path.join(os.path.expanduser("~"), ".config", "libdrive")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(
        os.path.join(dir_path, "config.json"),
        "w+",
    ) as w:
        json.dump(obj=json.loads(config_str), fp=w, sort_keys=True, indent=4)
config = src.config.readConfig()
print("DONE.\n")

print("\033[91mREADING METADATA...\033[0m")
metadata = src.metadata.readMetadata(config)
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
    metadata_file = next((i for i in files if i["name"] == "metadata.json"), None)
    if config_file:
        request = drive.files().get_media(fileId=config_file["id"])
        fh = io.BytesIO()
        downloader = googleapiclient.http.MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        config = json.loads(fh.getvalue())
        config, drive = src.credentials.refreshCredentials(config)
        with open(config_file["name"], "w+") as w:
            json.dump(config, w)
    if metadata_file:
        request = drive.files().get_media(fileId=metadata_file["id"])
        fh = io.BytesIO()
        downloader = googleapiclient.http.MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        metadata = json.loads(fh.getvalue())
        with open("metadata.json", "w+") as w:
            json.dump(metadata, w)
global font_req
font_req = requests.get(
    "https://raw.githack.com/googlefonts/roboto/master/src/hinted/Roboto-Regular.ttf",
    "rb",
)
print("DONE.\n")


def threaded_metadata():
    for thread in threading.enumerate():
        if thread.name == "metadata_thread":
            print("DONE.\n")
            return (
                {
                    "error": {
                        "code": 500,
                        "message": "libDrive is already building metadata, please wait.",
                    }
                },
                500,
            )
    config = src.config.readConfig()
    if len(config.get("category_list")) > 0:
        metadata_thread = threading.Thread(
            target=src.metadata.writeMetadata,
            args=(config,),
            daemon=True,
            name="metadata_thread",
        )
        metadata_thread.start()
    else:
        with open("./metadata.json", "w+") as w:
            w.write(json.dumps([]))
    return (
        {
            "success": {
                "code": 200,
                "message": "libDrive is building your new metadata",
            }
        },
        200,
    )


def create_app():
    app = flask.Flask(__name__, static_folder="build")

    if config["build_interval"] != 0:
        print("\033[91mCREATING CRON JOB...\033[0m")
        sched = apscheduler.schedulers.background.BackgroundScheduler(daemon=True)
        sched.add_job(
            threaded_metadata,
            "interval",
            minutes=config["build_interval"],
        )
        sched.start()
        print("DONE.\n")

    config_categories = [d["id"] for d in config["category_list"]]
    metadata_categories = [d["id"] for d in metadata]
    if len(metadata) > 0 and sorted(config_categories) == sorted(metadata_categories):
        if config["build_interval"] == 0:
            return app
        elif datetime.datetime.utcnow() <= datetime.datetime.strptime(
            metadata[-1]["buildTime"], "%Y-%m-%d %H:%M:%S.%f"
        ) + datetime.timedelta(minutes=config["build_interval"]):
            return app
        else:
            threaded_metadata()
    else:
        threaded_metadata()

    return app


app = create_app()
flask_cors.CORS(app)
app.secret_key = config["secret_key"]


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if (path != "") and os.path.exists("%s/%s" % (app.static_folder, path)):
        return flask.send_from_directory(app.static_folder, path)
    else:
        return flask.send_from_directory(app.static_folder, "index.html")


@app.route("/api/v1/auth")
def authAPI():
    config = src.config.readConfig()
    u = flask.request.args.get("u")  # USERNAME
    p = flask.request.args.get("p")  # PASSWORD
    a = flask.request.args.get("a")  # AUTH
    rules = flask.request.args.get("rules")  # RULES
    if config.get("auth") == False:
        return (
            flask.jsonify(
                {
                    "success": {
                        "code": 200,
                        "content": "/browse",
                        "message": "Authentication completed successfully!",
                    }
                }
            ),
            200,
        )
    elif rules == "signup":
        return (
            flask.jsonify(
                {
                    "success": {
                        "code": 202,
                        "conntent": config.get("signup"),
                        "message": "Signup is available on this server.",
                    }
                }
            ),
            202,
        )
    elif any(u == account["username"] for account in config["account_list"]) and any(
        p == account["password"] for account in config["account_list"]
    ):
        account = next(
            (
                i
                for i in config["account_list"]
                if i["username"] == u and i["password"] == p
            ),
            None,
        )
        return flask.jsonify(account), 200
    elif any(a == account["auth"] for account in config["account_list"]):
        account = next((i for i in config["account_list"] if i["auth"] == a), None)
        return flask.jsonify(account), 200
    else:
        return (
            flask.jsonify(
                {
                    "error": {
                        "code": 401,
                        "message": "The username and/or password provided was incorrect.",
                    }
                }
            ),
            401,
        )


@app.route("/api/v1/signup")
def signupAPI():
    config = src.config.readConfig()
    u = flask.request.args.get("u")  # USERNAME
    p = flask.request.args.get("p")  # PASSWORD
    if config.get("signup"):
        if any(u == account["username"] for account in config["account_list"]):
            return (
                flask.jsonify(
                    {
                        "error": {
                            "code": 409,
                            "message": "An account with this username already exists.",
                        }
                    }
                ),
                409,
            )
        else:
            auth = "".join(
                random.choices("abcdefghijklmnopqrstuvwxyz" + "0123456789", k=50)
            )
            account = {"username": u, "password": p, "pic": "", "auth": auth}
            config["account_list"].append(account)
            src.config.updateConfig(config)
            return (
                flask.jsonify(
                    {
                        "success": {
                            "code": 200,
                            "content": account,
                            "message": "Registration successful!",
                        }
                    }
                ),
                200,
            )
    else:
        return (
            flask.jsonify(
                {
                    "error": {
                        "code": 401,
                        "message": "This server has disabled user sign up.",
                    }
                }
            ),
            401,
        )


@app.route("/api/v1/environment")
def environmentAPI():
    config = src.config.readConfig()
    a = flask.request.args.get("a")  # AUTH
    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        account = next((i for i in config["account_list"] if i["auth"] == a), None)
        if account:
            if account.get("whitelist"):
                category_list = []
                for category in config["category_list"]:
                    if any(
                        category["id"] == whitelist
                        for whitelist in account["whitelist"]
                    ):
                        category_list.append(category)
                    else:
                        pass
                tmp_environment = {
                    "account_list": account,
                    "category_list": category_list,
                }
                return flask.jsonify(tmp_environment), 200
            else:
                tmp_environment = {
                    "account_list": account,
                    "category_list": config["category_list"],
                }
                return flask.jsonify(tmp_environment), 200
        else:
            tmp_environment = {
                "account_list": {"pic": "k"},
                "category_list": config["category_list"],
            }
            return flask.jsonify(tmp_environment), 200


@app.route("/api/v1/metadata")
def metadataAPI():
    config = src.config.readConfig()
    tmp_metadata = src.metadata.readMetadata(config)
    a = flask.request.args.get("a")  # AUTH
    c = flask.request.args.get("c")  # CATEGORY
    q = flask.request.args.get("q")  # SEARCH-QUERY
    s = flask.request.args.get("s")  # SORT-ORDER
    r = flask.request.args.get("r")  # RANGE
    id = flask.request.args.get("id")  # ID
    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        account = next((i for i in config["account_list"] if i["auth"] == a), None)
        whitelisted_categories_metadata = []
        for category in tmp_metadata:
            category_config = next(
                (i for i in config["category_list"] if i["id"] == category["id"]), None
            )
            if category_config.get("whitelist"):
                if account["auth"] in category_config["whitelist"]:
                    whitelisted_categories_metadata.append(category)
            else:
                whitelisted_categories_metadata.append(category)
        tmp_metadata = whitelisted_categories_metadata
        whitelisted_accounts_metadata = []
        if account:
            if account.get("whitelist"):
                for x in tmp_metadata:
                    if any(x["id"] == whitelist for whitelist in account["whitelist"]):
                        whitelisted_accounts_metadata.append(x)
                tmp_metadata = whitelisted_accounts_metadata
        if c:
            tmp_metadata = [
                next((i for i in tmp_metadata if i["categoryInfo"]["name"] == c), None)
            ]
            if tmp_metadata:
                pass
            else:
                return (
                    flask.jsonify(
                        {
                            "error": {
                                "code": 400,
                                "message": "The category provided could not be found.",
                            }
                        }
                    ),
                    400,
                )
        if q:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = [
                    item
                    for item in category["children"]
                    if q.lower() in item["title"].lower()
                ]
                index += 1
        if s:
            index = 0
            for category in tmp_metadata:
                if s == "alphabet-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: k["title"]
                        )
                    except:
                        pass
                elif s == "alphabet-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: k["title"], reverse=True
                        )
                    except:
                        pass
                elif s == "date-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: tuple(map(int, k["releaseDate"].split("-"))),
                        )
                    except:
                        pass
                elif s == "date-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: tuple(map(int, k["releaseDate"].split("-"))),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "popularity-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: float(k["popularity"])
                        )
                    except:
                        pass
                elif s == "popularity-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: float(k["popularity"]),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "vote-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: float(k["voteAverage"])
                        )
                    except:
                        pass
                elif s == "vote-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: float(k["voteAverage"]),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "random":
                    try:
                        random.shuffle(tmp_metadata[index]["children"])
                    except:
                        pass
                else:
                    return None
                index += 1
        if r:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = eval(
                    "category['children']" + "[" + r + "]"
                )
                index += 1
        if id:
            tmp_metadata = src.metadata.jsonExtract(tmp_metadata, "id", id, False)
            if tmp_metadata:
                tmp_metadata["children"] = []
                if (
                    tmp_metadata.get("title")
                    and tmp_metadata.get("type") == "directory"
                ):
                    for item in src.drivetools.driveIter(tmp_metadata, drive, "video"):
                        if item["mimeType"] == "application/vnd.google-apps.folder":
                            item["type"] = "directory"
                            tmp_metadata["children"].append(item)
                        else:
                            item["type"] = "file"
                            tmp_metadata["children"].append(item)
                return flask.jsonify(tmp_metadata), 200
            tmp_metadata = (
                drive.files().get(fileId=id, supportsAllDrives=True).execute()
            )
            if tmp_metadata["mimeType"] == "application/vnd.google-apps.folder":
                tmp_metadata["type"] = "directory"
                tmp_metadata["children"] = []
                for item in src.drivetools.driveIter(tmp_metadata, drive, "video"):
                    if (
                        tmp_metadata.get("mimeType")
                        == "application/vnd.google-apps.folder"
                    ):
                        tmp_metadata["type"] = "directory"
                        tmp_metadata["children"].append(item)
                    else:
                        tmp_metadata["type"] = "file"
                        tmp_metadata["children"].append(item)

        return flask.jsonify(tmp_metadata), 200
    else:
        return (
            flask.jsonify(
                {
                    "error": {
                        "code": 401,
                        "message": "Your credentials are invalid!",
                    }
                }
            ),
            401,
        )


@app.route("/api/v1/redirectdownload/<name>")
def downloadRedirectAPI(name):
    id = flask.request.args.get("id")
    itag = flask.request.args.get("itag")

    config = src.config.readConfig()
    if (
        datetime.datetime.strptime(
            config.get("token_expiry", datetime.datetime.utcnow()),
            "%Y-%m-%d %H:%M:%S.%f",
        )
        <= datetime.datetime.utcnow()
    ):
        config, drive = src.credentials.refreshCredentials(config)

    tmp_metadata = src.metadata.jsonExtract(
        src.metadata.readMetadata(config), "id", id, False
    )
    if tmp_metadata:
        name = tmp_metadata.get("name", name)
    args = "?"
    for arg in flask.request.args:
        args += "%s=%s&" % (arg, flask.request.args[arg])
    session = {"access_token": config.get("access_token")}

    session["url"] = "https://www.googleapis.com/drive/v3/files/%s?alt=media" % (id)
    if itag and itag != "" and config.get("transcoded") == True:
        req = requests.get(
            "https://docs.google.com/get_video_info?docid=%s" % (id),
            headers={"Authorization": "Bearer %s" % config.get("access_token")},
        )
        parsed = urllib.parse.parse_qs(urllib.parse.unquote(req.text))
        if parsed.get("status") == ["ok"]:
            for stream in parsed["url"]:
                if ("itag=%s" % (itag)) in stream:
                    url = stream
                    break
            cookie_string = "; ".join(
                [str(x) + "=" + str(y) for x, y in req.cookies.items()]
            )
            session["cookie"] = cookie_string
            session["transcoded"] = config.get("transcoded")
            session["url"] = url

    sessionB64 = base64.b64encode(json.dumps(session).encode("ascii")).decode("ascii")

    if config.get("cloudflare") and config.get("cloudflare") != "":
        return flask.redirect(
            config.get("cloudflare")
            + "/api/v1/download/%s%ssession=%s&" % (name, args, sessionB64),
            code=302,
        )
    else:
        return flask.redirect(
            "/api/v1/download/%s%ssession=%s&" % (name, args, sessionB64), code=302
        )


@app.route("/api/v1/download/<name>")
def downloadAPI(name):
    def download_file(streamable):
        with streamable as stream:
            stream.raise_for_status()
            for chunk in stream.iter_content(chunk_size=4096):
                yield chunk

    a = flask.request.args.get("a")
    id = flask.request.args.get("id")
    session = json.loads(
        base64.b64decode(flask.request.args.get("session").encode("ascii")).decode(
            "ascii"
        )
    )

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        headers = {
            key: value for (key, value) in flask.request.headers if key != "Host"
        }
        headers["Authorization"] = "Bearer %s" % (session.get("access_token"))
        if session.get("transcoded") == True and session.get("cookie"):
            headers.update({"cookie": session.get("cookie")})
            resp = requests.request(
                method=flask.request.method,
                url=session.get("url"),
                headers=headers,
                data=flask.request.get_data(),
                allow_redirects=True,
                stream=True,
            )
            excluded_headers = [
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "connection",
            ]
            headers = [
                (name, value)
                for (name, value) in resp.raw.headers.items()
                if name.lower() not in excluded_headers
            ]
            return flask.Response(
                flask.stream_with_context(download_file(resp)),
                resp.status_code,
                headers,
            )
        else:
            resp = requests.request(
                method=flask.request.method,
                url="https://www.googleapis.com/drive/v3/files/%s?alt=media" % (id),
                headers=headers,
                data=flask.request.get_data(),
                cookies=flask.request.cookies,
                allow_redirects=False,
                stream=True,
            )
            excluded_headers = [
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "connection",
            ]
            headers = [
                (name, value)
                for (name, value) in resp.raw.headers.items()
                if name.lower() not in excluded_headers
            ]
            return flask.Response(
                flask.stream_with_context(download_file(resp)),
                resp.status_code,
                headers,
            )
    else:
        return (
            flask.jsonify(
                {
                    "error": {
                        "code": 401,
                        "message": "Your credentials are invalid!",
                    }
                }
            ),
            401,
        )


@app.route("/api/v1/stream_map")
def stream_mapAPI():
    a = flask.request.args.get("a")
    id = flask.request.args.get("id")
    name = flask.request.args.get("name")
    server = flask.request.args.get("server")

    config = src.config.readConfig()
    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        stream_list = [
            {
                "size": 4320,
                "src": "%s/api/v1/redirectdownload/%s?a=%s&id=%s"
                % (server, name, a, id),
            }
        ]
        if config.get("transcoded") == True:
            req = requests.get(
                "https://docs.google.com/get_video_info?authuser=&docid=%s&access_token=%s"
                % (id, config["access_token"]),
                headers={"Authorization": "Bearer %s" % config["access_token"]},
            )
            parsed = urllib.parse.parse_qs(urllib.parse.unquote(req.text))
            qualities = [4320, 2880, 2160, 1440, 1080, 720, 576, 480, 360, 240]
            if parsed.get("status") == ["ok"]:
                for fmt in parsed["fmt_list"][0].split(","):
                    fmt_data = fmt.split("/")
                    fmt_resoltion = [int(x) for x in fmt_data[1].split("x")]
                    quality = min(qualities, key=lambda x: abs(x - min(fmt_resoltion)))
                    stream_list.append(
                        {
                            "size": quality,
                            "src": "%s/api/v1/redirectdownload/%s?a=%s&id=%s&itag=%s"
                            % (server, name, a, id, fmt_data[0]),
                        }
                    )
                return flask.jsonify(
                    {
                        "success": {
                            "code": 200,
                            "content": stream_list,
                            "message": "Stream list generated successfully!",
                        }
                    }
                )
        return flask.jsonify(
            {
                "success": {
                    "code": 200,
                    "content": stream_list,
                    "message": "Stream list generated successfully!",
                }
            }
        )
    else:
        return (
            flask.jsonify(
                {
                    "error": {
                        "code": 401,
                        "message": "Your credentials are invalid!",
                    }
                }
            ),
            401,
        )


@app.route("/api/v1/config", methods=["GET", "POST"])
def configAPI():
    config = src.config.readConfig()
    if flask.request.method == "GET":
        secret = flask.request.args.get("secret")
        if secret == config["secret_key"]:
            return flask.jsonify(config), 200
        else:
            return (
                flask.jsonify(
                    {
                        "error": {
                            "code": 401,
                            "message": "The secret key provided was incorrect.",
                        }
                    }
                ),
                401,
            )
    elif flask.request.method == "POST":
        secret = flask.request.args.get("secret")
        if secret == None:
            secret = ""
        if secret == config["secret_key"]:
            data = flask.request.json
            data["token_expiry"] = str(datetime.datetime.utcnow())
            src.config.updateConfig(data)
            return (
                flask.jsonify(
                    {
                        "success": {
                            "code": 200,
                            "message": "libDrive is updating your config",
                        }
                    }
                ),
                200,
            )
        else:
            return (
                flask.jsonify(
                    {
                        "error": {
                            "code": 401,
                            "message": "The secret key provided was incorrect.",
                        }
                    }
                ),
                401,
            )


@app.route("/api/v1/image/<image_type>")
def imageAPI(image_type):
    text = flask.request.args.get("text")
    extention = flask.request.args.get("extention")
    if image_type == "poster":
        img = Image.new("RGB", (342, 513), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_size = 1
        font_bytes = io.BytesIO(font_req.content)
        font = ImageFont.truetype(font_bytes, font_size)
        img_fraction = 0.9
        breakpoint = img_fraction * img.size[0]
        jumpsize = 75
        while True:
            if font.getsize(text)[0] < breakpoint:
                font_size += jumpsize
            else:
                jumpsize = jumpsize // 2
                font_size -= jumpsize
            font_bytes = io.BytesIO(font_req.content)
            font = ImageFont.truetype(font_bytes, font_size)
            if jumpsize <= 1:
                break

        width, height = draw.textsize(text, font=font)
        draw.text(
            ((342 - width) / 2, (513 - height) / 2), text, fill="black", font=font
        )
        output = io.BytesIO()
        img.save(output, format=extention)
        output.seek(0, 0)
        return flask.send_file(
            output, mimetype="image/%s" % (extention), as_attachment=False
        )
    elif image_type == "backdrop":
        img = Image.new("RGB", (1280, 720), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_size = 1
        font_bytes = io.BytesIO(font_req.content)
        font = ImageFont.truetype(font_bytes, font_size)
        img_fraction = 0.9
        breakpoint = img_fraction * img.size[0]
        jumpsize = 75
        while True:
            if font.getsize(text)[0] < breakpoint:
                font_size += jumpsize
            else:
                jumpsize = jumpsize // 2
                font_size -= jumpsize
            font_bytes = io.BytesIO(font_req.content)
            font = ImageFont.truetype(font_bytes, font_size)
            if jumpsize <= 1:
                break

        width, height = draw.textsize(text, font=font)
        draw.text(
            ((1280 - width) / 2, (720 - height) / 2), text, fill="black", font=font
        )
        output = io.BytesIO()
        img.save(output, format=extention)
        output.seek(0, 0)
        return flask.send_file(
            output, mimetype="image/%s" % (extention), as_attachment=False
        )
    elif image_type == "thumbnail":
        id = flask.request.args.get("id")
        params = {
            "fileId": id,
            "fields": "thumbnailLink",
            "supportsAllDrives": True,
        }
        res = drive.files().get(**params).execute()
        if res.get("thumbnailLink"):
            thumbnail = re.sub(r"(s[^s]*)$", "s3840", res["thumbnailLink"])
            return flask.redirect(thumbnail, code=302)
        else:
            return (
                flask.jsonify(
                    {
                        "error": {
                            "code": 500,
                            "message": "The thumbnail does not exist on Google's servers.",
                        }
                    }
                ),
                500,
            )


@app.route("/api/v1/rebuild")
def rebuildAPI():
    config = src.config.readConfig()
    a = flask.request.args.get("a")
    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        res, code = threaded_metadata()
        return flask.jsonify(res), code
    else:
        return (
            flask.jsonify(
                {
                    "error": {
                        "code": 401,
                        "message": "The secret key provided was incorrect.",
                    }
                }
            ),
            401,
        )


@app.route("/api/v1/restart")
def restartAPI():
    config = src.config.readConfig()
    secret = flask.request.args.get("secret")
    if secret == config["secret_key"]:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        return (
            flask.jsonify(
                {
                    "error": {
                        "code": 401,
                        "message": "The secret key provided was incorrect.",
                    }
                }
            ),
            401,
        )


@app.route("/api/v1/ping")
def pingAPI():
    return (
        {
            "success": {
                "code": 200,
                "message": "Pong",
            }
        },
        200,
    )


if __name__ == "__main__":
    print("\033[91mSERVING SERVER...\033[0m")
    print("DONE.\n")
    app.run(
        host="0.0.0.0",
        port=31145,
        threaded=True,
        debug=os.getenv("LIBDRIVE_DEBUG"),
    )
