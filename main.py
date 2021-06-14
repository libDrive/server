import datetime
import io
import json
import logging
import os
import re
import threading
import time

import apscheduler.schedulers.background
import colorama
import flask
import flask_cors
import googleapiclient
import requests

import src.config
import src.credentials
import src.metadata

colorama.init()
print(
    "====================================================\n\033[96m               libDrive - \033[92mv1.3.4\033[94m\n                   @eliasbenb\033[0m\n====================================================\n"
)

print("\033[91mREADING CONFIG...\033[0m")
if os.getenv("LIBDRIVE_CONFIG"):
    config_str = os.getenv("LIBDRIVE_CONFIG")
    with open("config.json", "w+") as w:
        json.dump(obj=json.loads(config_str), fp=w, sort_keys=True, indent=4)
config = src.config.readConfig()
print("DONE.\n")

print("\033[91mREADING METADATA...\033[0m")
metadata = src.metadata.readMetadata(config)
if os.getenv("LIBDRIVE_CLOUD") and config.get("refresh_token"):
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
        src.config.updateConfig(config)
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

print("DONE.\n")

if not config.get("account_list"):
    config["account_list"] = []
if not config.get("auth"):
    config["auth"] = False
if not config.get("build_interval"):
    config["build_interval"] = 360
if not config.get("build_type"):
    config["build_type"] = "hybrid"
if not config.get("category_list"):
    config["category_list"] = []
if not config.get("cloudflare"):
    config["cloudflare"] = ""
if not config.get("transcoded"):
    config["transcoded"] = False
if not config.get("service_accounts"):
    config["service_accounts"] = []
if not config.get("signup"):
    config["signup"] = False
if not config.get("subtitles"):
    config["subtitles"] = False

if config.get("account_list") == []:
    config["auth"] = False

with open("config.json", "w+") as w:
    json.dump(obj=config, fp=w, sort_keys=True, indent=4)


def threaded_metadata():
    for thread in threading.enumerate():
        if thread.name == "metadata_thread":
            print("DONE.\n")
            return (
                {
                    "code": 500,
                    "content": None,
                    "message": "libDrive is already building metadata, please wait.",
                    "success": False,
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
            "code": 200,
            "content": None,
            "message": "libDrive is building your new metadata.",
            "success": True,
        },
        200,
    )


def create_app():
    if os.path.exists("./build"):
        if config.get("arcio") and config.get("arcio") != "":
            req = requests.get("https://arc.io/arc-sw.js")
            with open("./build/arc-sw.js", "wb") as wb:
                wb.write(req.content)
            with open("./build/index.html", "r+") as r:
                old_html = re.sub(
                    r"<script async src=[\"\']https:\/\/arc.io\/widget.min.js#(?P<arcio_id>.{1,15})[\"\']><\/script>",
                    "",
                    r.read(),
                )
                code = config.get("arcio")
                if code == "dev":
                    code = "tUUqUjhw"
                new_html = old_html.replace(
                    "<head>",
                    '<head><script async src="https://arc.io/widget.min.js#%s"></script>'
                    % (code),
                )
                r.seek(0)
                r.write(new_html)
        else:
            if os.path.exists("./build/arc-sw.js"):
                os.remove("./build/arc-sw.js")
            with open("./build/index.html", "r+") as r:
                old_html = r.read()
                new_html = new_html = re.sub(
                    r"<script async src=[\"\']https:\/\/arc.io\/widget.min.js#(?P<arcio_id>.{5,15})[\"\']><\/script>",
                    "",
                    old_html,
                )
                r.seek(0)
                r.write(new_html)

    app = flask.Flask(__name__, static_folder="build")

    build_interval = config.get("build_interval")
    if not build_interval:
        build_interval = 360
    if build_interval != 0:
        print("\033[91mCREATING CRON JOB...\033[0m")
        sched = apscheduler.schedulers.background.BackgroundScheduler(daemon=True)
        sched.add_job(
            threaded_metadata,
            "interval",
            minutes=build_interval,
        )
        sched.start()
        print("DONE.\n")

    config_categories = [d["id"] for d in config["category_list"]]
    metadata_categories = [d["id"] for d in metadata]
    if len(metadata) > 0 and sorted(config_categories) == sorted(metadata_categories):
        if build_interval == 0:
            return app
        elif datetime.datetime.utcnow() <= datetime.datetime.strptime(
            metadata[-1]["buildTime"], "%Y-%m-%d %H:%M:%S.%f"
        ) + datetime.timedelta(minutes=build_interval):
            return app
        else:
            threaded_metadata()
    else:
        threaded_metadata()

    return app


app = create_app()
flask_cors.CORS(app)
app.secret_key = config.get("secret_key")

from src.routes.auth import authBP
from src.routes.config import configBP
from src.routes.debug import debugBP
from src.routes.download import downloadBP
from src.routes.environment import environmentBP
from src.routes.image import imageBP
from src.routes.metadata import metadataBP
from src.routes.ping import pingBP
from src.routes.rebuild import rebuildBP
from src.routes.redirectdownload import redirectdownloadBP
from src.routes.restart import restartBP
from src.routes.signup import signupBP
from src.routes.streammap import streammapBP
from src.routes.subtitledownload import subtitledownloadBP

app.register_blueprint(authBP)
app.register_blueprint(configBP)
app.register_blueprint(debugBP)
app.register_blueprint(downloadBP)
app.register_blueprint(environmentBP)
app.register_blueprint(imageBP)
app.register_blueprint(metadataBP)
app.register_blueprint(pingBP)
app.register_blueprint(rebuildBP)
app.register_blueprint(redirectdownloadBP)
app.register_blueprint(restartBP)
app.register_blueprint(signupBP)
app.register_blueprint(streammapBP)
app.register_blueprint(subtitledownloadBP)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
async def serve(path):
    if (path != "") and os.path.exists("%s/%s" % (app.static_folder, path)):
        return flask.send_from_directory(app.static_folder, path)
    else:
        return flask.send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    print("\033[91mSERVING SERVER...\033[0m")
    if not os.path.exists("./logs"):
        os.mkdir("./logs")
    now = time.time()
    for f in os.listdir("./logs"):
        if os.stat(os.path.join("./logs", f)).st_mtime < now - 86400:
            if os.path.isfile(os.path.join("./logs", f)):
                try:
                    os.remove(os.path.join("./logs", f))
                except OSError:
                    pass
    logging.basicConfig(
        filename="./logs/%s.log"
        % (datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")),
        level=logging.DEBUG,
    )
    LIBDRIVE_DEBUG = os.getenv("LIBDRIVE_DEBUG")
    if LIBDRIVE_DEBUG:
        if LIBDRIVE_DEBUG.lower() == "true":
            LIBDRIVE_DEBUG = True
        else:
            LIBDRIVE_DEBUG = False
    else:
        LIBDRIVE_DEBUG = False
    print("DONE.\n")
    app.run(
        host="0.0.0.0",
        port=31145,
        threaded=True,
        debug=LIBDRIVE_DEBUG,
    )
