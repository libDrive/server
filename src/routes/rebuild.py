import flask
import src.functions.config

rebuildBP = flask.Blueprint("rebuild", __name__)

import main


@rebuildBP.route("/api/v1/rebuild")
def rebuildFunction():
    secret = flask.request.args.get("secret")  # SECRET
    config = src.functions.config.readConfig()

    if secret == config.get("secret_key"):
        res, code = main.threaded_metadata()
        return flask.jsonify(res), code
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
