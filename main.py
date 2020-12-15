import json
import os
import random

import flask
import flask_cors
import requests

import src.config
import src.credentials
import src.metadata

if os.path.exists("config.env"):
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key = src.config.readConfig()
else:
    src.config.writeConfig()
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key = src.config.readConfig()

drive, access_token = src.credentials.refreshCredentials(
    "", client_id, client_secret, refresh_token, True)

configuration_url = "http://api.themoviedb.org/3/configuration?api_key=" + tmdb_api_key
configuration_content = json.loads(
    (requests.get(configuration_url)).content)
backdrop_base_url = configuration_content["images"]["base_url"] + \
    configuration_content["images"]["backdrop_sizes"][3]
poster_base_url = configuration_content["images"]["base_url"] + \
    configuration_content["images"]["poster_sizes"][3]

metadata = src.metadata.readMetadata(category_list)
metadata = src.metadata.writeMetadata(category_list, drive, tmdb_api_key,
                                      backdrop_base_url, poster_base_url)

app = flask.Flask(__name__)
flask_cors.CORS(app)
app.secret_key = secret_key


@app.route("/api/v1/auth")
def authAPI():
    u = flask.request.args.get("u")  # USERNAME
    p = flask.request.args.get("p")  # PASSWORD
    if any(u == account["username"] for account in account_list) and any(p == account["password"] for account in account_list):
        account = next((i for i in account_list if i["username"] == u), None)
        return flask.jsonify(account)
    else:
        return flask.Response("The username and/or password provided was incorrect.", status=401)


@app.route("/api/v1/environment")
def environmentAPI():
    a = flask.request.args.get("a")  # AUTH
    if any(a == account["auth"] for account in account_list):
        account = next((i for i in account_list if i["auth"] == a), None)
        tmp_environment = {"account_list": account,
                           "category_list": category_list}
        return flask.jsonify(tmp_environment)


@app.route("/api/v1/metadata")
def metadataAPI():
    tmp_metadata = src.metadata.readMetadata(category_list)
    a = flask.request.args.get("a")  # AUTH
    c = flask.request.args.get("c")  # CATEGORY
    q = flask.request.args.get("q")  # SEARCH-QUERY
    s = flask.request.args.get("s")  # SORT-ORDER
    r = flask.request.args.get("r")  # RANGE
    id = flask.request.args.get("id")  # ID
    if any(a == account["auth"] for account in account_list):
        if c:
            tmp_metadata = [
                next((i for i in tmp_metadata if i["name"] == c), None)]
            if tmp_metadata:
                pass
            else:
                return flask.Response("The category provided could not be found.", status=400)
        if q:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["files"] = [
                    item for item in category["files"] if q.lower() in item["title"].lower()]
                tmp_metadata[index]["folders"] = [
                    item for item in category["folders"] if q.lower() in item["title"].lower()]
                index = index + 1
        if s:
            index = 0
            for category in tmp_metadata:
                if s == "alphabet-asc":
                    tmp_metadata[index]["files"] = sorted(
                        category["files"], key=lambda k: k["title"])
                    tmp_metadata[index]["folders"] = sorted(
                        category["folders"], key=lambda k: k["title"])
                elif s == "alphabet-des":
                    tmp_metadata[index]["files"] = sorted(
                        category["files"], key=lambda k: k["title"], reverse=True)
                    tmp_metadata[index]["folders"] = sorted(
                        category["folders"], key=lambda k: k["title"], reverse=True)
                elif s == "date-asc":
                    tmp_metadata[index]["files"] = sorted(
                        category["files"], key=lambda k: tuple(map(int, k["releaseDate"].split('-'))))
                    tmp_metadata[index]["folders"] = sorted(
                        category["folders"], key=lambda k: tuple(map(int, k["releaseDate"].split('-'))))
                elif s == "date-des":
                    tmp_metadata[index]["files"] = sorted(category["files"], key=lambda k: tuple(
                        map(int, k["releaseDate"].split('-'))), reverse=True)
                    tmp_metadata[index]["folders"] = sorted(category["folders"], key=lambda k: tuple(
                        map(int, k["releaseDate"].split('-'))), reverse=True)
                elif s == "popularity-asc":
                    tmp_metadata[index]["files"] = sorted(
                        category["files"], key=lambda k: float(k["popularity"]))
                    tmp_metadata[index]["folders"] = sorted(
                        category["folders"], key=lambda k: float(k["popularity"]))
                elif s == "popularity-des":
                    tmp_metadata[index]["files"] = sorted(
                        category["files"], key=lambda k: float(k["popularity"]), reverse=True)
                    tmp_metadata[index]["folders"] = sorted(
                        category["folders"], key=lambda k: float(k["popularity"]), reverse=True)
                elif s == "random":
                    random.shuffle(tmp_metadata[index]["files"])
                    random.shuffle(tmp_metadata[index]["folders"])
                else:
                    return None
                index = index + 1
        if r:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["files"] = eval(
                    "category['files']" + "[" + r + "]")
                tmp_metadata[index]["folders"] = eval(
                    "category['folders']" + "[" + r + "]")
                index = index + 1
        if id:
            ids = src.metadata.jsonExtract(
                obj=tmp_metadata, key="id", getObj=True)
            for item in ids:
                if item["id"] == id:
                    tmp_metadata = item

        return flask.jsonify(tmp_metadata)
    else:
        return flask.Response("The auth code provided was incorrect.", status=401)


@app.route("/api/v1/download")
def downloadAPI():
    def download_file(streamable):
        with streamable as stream:
            stream.raise_for_status()
            for chunk in stream.iter_content(chunk_size=512):
                yield chunk

    a = flask.request.args.get("a")
    id = flask.request.args.get("id")
    if any(a == account["auth"] for account in account_list) and id:
        headers = {key: value for (
            key, value) in flask.request.headers if key != 'Host'}
        headers["Authorization"] = "Bearer "+access_token
        resp = requests.request(
            method=flask.request.method,
            url="https://www.googleapis.com/drive/v3/files/"+id+"?alt=media",
            headers=headers,
            data=flask.request.get_data(),
            cookies=flask.request.cookies,
            allow_redirects=False,
            stream=True)
        excluded_headers = ['content-encoding',
                            'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        return flask.Response(download_file(resp), resp.status_code, headers)


if __name__ == "__main__":
    app.run(port=31145)
