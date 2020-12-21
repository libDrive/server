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
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, config = src.config.readConfig()
else:
    src.config.writeConfig()
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, config = src.config.readConfig()

drive, access_token = src.credentials.refreshCredentials(
    "", client_id, client_secret, refresh_token, True)

configuration_url = "http://api.themoviedb.org/3/configuration?api_key=" + tmdb_api_key
configuration_content = json.loads(requests.get(configuration_url).content)
backdrop_base_url = configuration_content["images"]["base_url"] + \
    configuration_content["images"]["backdrop_sizes"][3]
poster_base_url = configuration_content["images"]["base_url"] + \
    configuration_content["images"]["poster_sizes"][3]

metadata = src.metadata.readMetadata(category_list)
metadata = src.metadata.writeMetadata(
    category_list, drive, tmdb_api_key, backdrop_base_url, poster_base_url)

app = flask.Flask(__name__, static_folder=os.path.dirname(
    __file__) + "./build", static_url_path="")
flask_cors.CORS(app)
app.secret_key = secret_key


@app.errorhandler(404)
def not_found(e):
    if flask.request.path.startswith("/api"):
        return flask.Response("Page not found", status=404)
    elif flask.request.path.startswith("/null"):
        return flask.Response("Page not found", status=404)
    else:
        return app.send_static_file("index.html")


@app.route("/api/v1/auth")
def authAPI():
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, config = src.config.readConfig()
    u = flask.request.args.get("u")  # USERNAME
    p = flask.request.args.get("p")  # PASSWORD
    a = flask.request.args.get("a")  # AUTH
    if any(u == account["username"] for account in account_list) and any(p == account["password"] for account in account_list):
        account = next((i for i in account_list if i["username"] == u), None)
        return flask.jsonify(account)
    elif any(a == account["auth"] for account in account_list):
        account = next((i for i in account_list if i["auth"] == a), None)
        return flask.jsonify(account)
    else:
        return flask.Response("The username and/or password provided was incorrect.", status=401)


@app.route("/api/v1/environment")
def environmentAPI():
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, config = src.config.readConfig()
    a = flask.request.args.get("a")  # AUTH
    if any(a == account["auth"] for account in account_list):
        account = next((i for i in account_list if i["auth"] == a), None)
        tmp_environment = {"account_list": account,
                           "category_list": category_list}
        return flask.jsonify(tmp_environment)


@app.route("/api/v1/metadata")
def metadataAPI():
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, config = src.config.readConfig()
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
                tmp_metadata[index]["children"] = [
                    item for item in category["children"] if q.lower() in item["title"].lower()]
                index = index + 1
        if s:
            index = 0
            for category in tmp_metadata:
                if s == "alphabet-asc":
                    tmp_metadata[index]["children"] = sorted(
                        category["children"], key=lambda k: k["title"])
                elif s == "alphabet-des":
                    tmp_metadata[index]["children"] = sorted(
                        category["children"], key=lambda k: k["title"], reverse=True)
                elif s == "date-asc":
                    tmp_metadata[index]["children"] = sorted(
                        category["children"], key=lambda k: tuple(map(int, k["releaseDate"].split('-'))))
                elif s == "date-des":
                    tmp_metadata[index]["children"] = sorted(category["children"], key=lambda k: tuple(
                        map(int, k["releaseDate"].split('-'))), reverse=True)
                elif s == "popularity-asc":
                    tmp_metadata[index]["children"] = sorted(
                        category["children"], key=lambda k: float(k["popularity"]))
                elif s == "popularity-des":
                    tmp_metadata[index]["children"] = sorted(
                        category["children"], key=lambda k: float(k["popularity"]), reverse=True)
                elif s == "random":
                    random.shuffle(tmp_metadata[index]["children"])
                else:
                    return None
                index = index + 1
        if r:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = eval(
                    "category['children']" + "[" + r + "]")
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
def downloadRedirectAPI():
    tmp_metadata = metadata
    id = flask.request.args.get("id")
    ids = src.metadata.jsonExtract(obj=tmp_metadata, key="id", getObj=True)
    name = ""
    for item in ids:
        if item["id"] == id:
            name = item["name"]
    keys = [i for i in flask.request.args.keys()]
    values = [i for i in flask.request.args.values()]

    args = "?"
    for i in range(len(keys)):
        args += keys[i] + "=" + values[i] + "&"
    args = args[:-1]

    return flask.redirect("/api/v1/download/"+name+args)


@app.route("/api/v1/download/<name>")
def downloadAPI(name):
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
        excluded_headers = ["content-encoding",
                            "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in resp.raw.headers.items(
        ) if name.lower() not in excluded_headers]
        return flask.Response(download_file(resp), resp.status_code, headers)
    else:
        return flask.Response("The auth code or id provided was incorrect.", status=401)


@app.route("/api/v1/config", methods=['GET', 'POST'])
def configAPI():
    account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, config = src.config.readConfig()
    if flask.request.method == "GET":
        secret = flask.request.args.get("secret")
        if secret == secret_key:
            environment = {"account_list": account_list, "category_list": category_list,
                           "secret_key": secret_key, "tmdb_api_key": tmdb_api_key}
            return flask.jsonify(environment)
        else:
            return flask.Response("The secret key provided was incorrect", status=401)
    elif flask.request.method == "POST":
        secret = flask.request.args.get("secret")
        if secret == secret_key:
            data = flask.request.json
            src.config.updateConfig(access_token, data["account_list"], client_id, client_secret,
                                    refresh_token, data["category_list"], data["secret_key"], tmdb_api_key)
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        else:
            return flask.Response("The secret key provided was incorrect", status=401)


if __name__ == "__main__":
    app.run(port=31145)
