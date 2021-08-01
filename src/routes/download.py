import base64
import json

import flask
import flask_cors
import requests
import src.config

downloadBP = flask.Blueprint("download", __name__, url_prefix="/api/v1/download")
flask_cors.CORS(downloadBP)


@downloadBP.route("/<name>")
async def downloadFunction(name):
    a = flask.request.args.get("a")  # AUTH
    config = src.config.readConfig()

    def download_file(streamable):
        with streamable as stream:
            stream.raise_for_status()
            for chunk in stream.iter_content(chunk_size=4096):
                yield chunk

    session = json.loads(
        base64.b64decode(flask.request.args.get("session").encode("ascii")).decode(
            "ascii"
        )
    )

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        config, drive = src.credentials.refreshCredentials(src.config.readConfig())
        headers = {
            key: value for (key, value) in flask.request.headers if key != "Host"
        }
        headers["Authorization"] = "Bearer %s" % (session.get("access_token"))
        if session.get("transcoded") == True and session.get("cookie"):
            headers.update(
                {"cookie": session.get("cookie"), "content-disposition": "inline"}
            )
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
            headers.append(("content-disposition", "inline"))
            headers.append(("cache-control", "no-cache, no-store, must-revalidate"))
            headers.append(("pragma", "no-cache"))
            return flask.Response(
                flask.stream_with_context(download_file(resp)),
                resp.status_code,
                headers,
            )
        else:
            resp = requests.request(
                method=flask.request.method,
                url=session.get("url"),
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
            headers.append(("cache-control", "no-cache, no-store, must-revalidate"))
            headers.append(("pragma", "no-cache"))
            return flask.Response(
                flask.stream_with_context(download_file(resp)),
                resp.status_code,
                headers,
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
