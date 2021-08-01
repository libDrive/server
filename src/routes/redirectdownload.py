import base64
import datetime
import json
import urllib

import flask
import requests
import src.config

redirectdownloadBP = flask.Blueprint(
    "redirectdownload", __name__, url_prefix="/api/v1/redirectdownload"
)


@redirectdownloadBP.route("/<name>")
async def redirectdownloadFunction(name):
    id = flask.request.args.get("id")
    itag = flask.request.args.get("itag")

    config = src.config.readConfig()
    if config.get("kill_switch") == True:
        return

    if (
        datetime.datetime.strptime(
            config.get("token_expiry", datetime.datetime.utcnow()),
            "%Y-%m-%d %H:%M:%S.%f",
        )
        <= datetime.datetime.utcnow()
    ):
        config, drive = src.credentials.refreshCredentials(config)
        with open("config.json", "w+") as w:
            json.dump(obj=config, fp=w, sort_keys=True, indent=4)

    tmp_metadata = src.metadata.jsonExtract(
        src.metadata.readMetadata(config), "id", id, False
    )
    if tmp_metadata:
        name = tmp_metadata.get("name", name)
    args = "?"
    for arg in flask.request.args:
        args += "%s=%s&" % (
            arg,
            urllib.parse.quote(flask.request.args.get(arg, "").encode("utf-8")),
        )
    session = {"access_token": config.get("access_token")}

    session["url"] = "https://www.googleapis.com/drive/v3/files/%s?alt=media" % (id)
    if itag and itag != "" and config.get("transcoded") == True:
        req = requests.get(
            "https://drive.google.com/get_video_info?docid=%s" % (id),
            headers={"Authorization": "Bearer %s" % (config.get("access_token"))},
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
    print(
        "/api/v1/download/%s%ssession=%s&"
        % (urllib.parse.quote(name.encode("utf-8")), args, sessionB64)
    )

    if config.get("cloudflare") and config.get("cloudflare") != "":
        return flask.redirect(
            config.get("cloudflare")
            + "/api/v1/download/%s%ssession=%s&" % (name, args, sessionB64),
            code=302,
        )
    else:
        return flask.redirect(
            "/api/v1/download/%s%ssession=%s&"
            % (urllib.parse.quote(name.encode("utf-8")), args, sessionB64),
            code=302,
        )
