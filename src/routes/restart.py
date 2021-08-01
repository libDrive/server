import os
import sys

import flask
import flask_cors
import src.config

restartBP = flask.Blueprint("restart", __name__, url_prefix="/api/v1/restart")
flask_cors.CORS(restartBP)


@restartBP.route("/")
def restartFunction():
    config = src.config.readConfig()
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
