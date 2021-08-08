import datetime

import flask
import src.functions.config

configBP = flask.Blueprint("config", __name__)

import main


@configBP.route("/api/v1/config", methods=["GET", "POST"])
async def configFunction():
    secret = flask.request.args.get("secret")  # SECRET
    config = src.functions.config.readConfig()

    if flask.request.method == "GET":
        if secret == config.get("secret_key"):
            return (
                flask.jsonify(
                    {
                        "code": 200,
                        "content": config,
                        "message": "Config authentication completed successfully.",
                        "success": True,
                    }
                ),
                200,
            )
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
    elif flask.request.method == "POST":
        if secret == None:
            secret = ""
        if secret == config.get("secret_key"):
            data = flask.request.json
            data["token_expiry"] = str(datetime.datetime.utcnow())
            if data.get("category_list") != config.get("category_list"):
                src.functions.config.updateConfig(data)
                main.threaded_metadata()
            else:
                src.functions.config.updateConfig(data)
            return (
                flask.jsonify(
                    {
                        "code": 200,
                        "content": None,
                        "message": "libDrive is updating your config",
                        "success": True,
                    }
                ),
                200,
            )
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
