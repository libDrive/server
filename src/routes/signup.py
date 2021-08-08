import random

import flask
import src.functions.config

signupBP = flask.Blueprint("signup", __name__)


@signupBP.route("/api/v1/signup")
async def signupFunction():
    config = src.functions.config.readConfig()
    u = flask.request.args.get("u")  # USERNAME
    p = flask.request.args.get("p")  # PASSWORD

    if config.get("signup"):
        if any(u == account["username"] for account in config["account_list"]):
            return (
                flask.jsonify(
                    {
                        "code": 409,
                        "content": None,
                        "message": "An account with this username already exists.",
                        "success": False,
                    }
                ),
                409,
            )
        else:
            auth = "".join(
                random.choices("abcdefghijklmnopqrstuvwxyz" + "0123456789", k=50)
            )
            account = {"username": u, "password": p, "pic": "", "auth": auth}
            config["account_list"].append(account)
            src.functions.config.updateConfig(config)
            return (
                flask.jsonify(
                    {
                        "code": 200,
                        "content": account,
                        "message": "Registration successful.",
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
                    "content": True,
                    "message": "This server has disabled user sign up.",
                    "success": False,
                }
            ),
            401,
        )
