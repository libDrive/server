import os
import pathlib

import flask
import src.config

debugBP = flask.Blueprint("debug", __name__)

root_path = pathlib.Path(os.getcwd())


def files_list(path):
    return [x for x in path.iterdir() if x.is_file()]


def folders_list(path):
    return [x for x in path.iterdir() if x.is_dir()]


@debugBP.route("/api/v1/debug/<path:path>")
def browse(path):
    config = src.config.readConfig()
    secret = flask.request.args.get("secret")

    if secret == config.get("secret_key"):
        full_path = pathlib.Path(os.path.join(os.getcwd(), path))
        if path == "*":
            full_path = root_path
        if os.path.isfile(full_path):
            return flask.send_file(full_path)
        if root_path in full_path.parents or full_path == root_path:
            return flask.render_template(
                "debug_browser.html",
                path=full_path,
                folder_directory=folders_list(full_path),
                files_directory=files_list(full_path),
                secret=secret,
            )
        else:
            return flask.redirect("/api/v1/debug/*")
    else:
        return (
            flask.jsonify(
                {
                    "code": 401,
                    "message": "The secret key provided was incorrect.",
                    "success": False,
                }
            ),
            401,
        )
