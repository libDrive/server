import flask
import src.functions.config

authBP = flask.Blueprint("auth", __name__)


@authBP.route("/api/v1/auth")
async def authFunction():
    a = flask.request.args.get("a")  # AUTH
    p = flask.request.args.get("p")  # PASSWORD
    u = flask.request.args.get("u")  # USERNAME
    config = src.functions.config.readConfig()

    rules = flask.request.args.get("rules")  # RULES
    if config.get("auth") == False:
        return (
            flask.jsonify(
                {
                    "code": 200,
                    "content": {"ui_config": config.get("ui_config", {})},
                    "message": "Authentication completed successfully.",
                    "success": True,
                }
            ),
            200,
        )
    elif rules == "signup":
        if config.get("signup") == True:
            return (
                flask.jsonify(
                    {
                        "code": 202,
                        "content": True,
                        "message": "Signup is available on this server.",
                        "success": True,
                    }
                ),
                202,
            )
        else:
            return (
                flask.jsonify(
                    {
                        "code": 202,
                        "content": False,
                        "message": "Signup is not available on this server.",
                        "success": True,
                    }
                ),
                202,
            )
    elif any(u == account["username"] for account in config["account_list"]) and any(
        p == account["password"] for account in config["account_list"]
    ):
        account = next(
            (
                i
                for i in config["account_list"]
                if i["username"] == u and i["password"] == p
            ),
            None,
        )
        return (
            flask.jsonify(
                {
                    "code": 200,
                    "content": {"auth": account["auth"], "ui_config": config.get("ui_config", {})},
                    "message": "Authentication was successful.",
                    "success": True,
                }
            ),
            200,
        )
    elif any(a == account["auth"] for account in config["account_list"]):
        account = next((i for i in config["account_list"] if i["auth"] == a), None)
        return (
            flask.jsonify(
                {
                    "code": 200,
                    "content": account,
                    "message": "Authentication was successful.",
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
                    "message": "The username and/or password provided was incorrect.",
                    "success": False,
                }
            ),
            401,
        )
