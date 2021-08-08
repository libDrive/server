import os
import sys

import flask
import src.functions.config

restartBP = flask.Blueprint("restart", __name__)


@restartBP.route("/api/v1/restart")
def restartFunction():
    config = src.functions.config.readConfig()
    secret = flask.request.args.get("secret")
    if secret == config.get("secret_key"):
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        return (
            flask.jsonify(
                {
                    "code": 401,
                    "content": None,
                    "message": "The secret key provided was incorrect.",
                    "success": False,
                }
            ),
            401,
        )
