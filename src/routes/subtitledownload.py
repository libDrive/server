import re

import chardet
import flask
import requests
import src.functions.config

subtitledownloadBP = flask.Blueprint("subtitledownload", __name__)


@subtitledownloadBP.route("/api/v1/subtitledownload/<name>")
async def subtitledownloadFunction(name):
    a = flask.request.args.get("a")  # AUTH
    id = flask.request.args.get("id")  # ID
    config = src.functions.config.readConfig()

    def download_file(streamable):
        with streamable as stream:
            stream.raise_for_status()
            for chunk in stream.iter_content(chunk_size=4096):
                if name.endswith("srt"):
                    encoding = chardet.detect(chunk).get("encoding")
                    replacement = "WEBVTT FILE\r\n\r\n" + str(chunk, encoding)
                    replacement = re.sub(
                        r"(\d\d:\d\d:\d\d),(\d\d\d)", r"\1.\2", replacement
                    )
                    lines = replacement.split("\n")
                    i = 0
                    output = ""
                    for line in lines:
                        if "-->" in line:
                            lines[i - 1] = ""
                        elif i == 0:
                            pass
                        else:
                            output += lines[i - 1] + "\n"
                        i += 1
                    chunk = output.encode(encoding)
                yield chunk

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        config, drive = src.functions.credentials.refreshCredentials(
            src.functions.config.readConfig()
        )
        headers = {
            key: value for (key, value) in flask.request.headers if key != "Host"
        }
        headers["Authorization"] = "Bearer %s" % (config.get("access_token"))
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
        headers.append(("cache-control", "no-cache, no-store, must-revalidate"))
        headers.append(("pragma", "no-cache"))
        return flask.Response(
            flask.stream_with_context(download_file(resp)),
            resp.status_code,
            headers,
        )
