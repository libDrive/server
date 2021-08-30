import flask
import src.functions.config

environmentBP = flask.Blueprint("environment", __name__)


@environmentBP.route("/api/v1/environment")
async def environmentFunction():
    a = flask.request.args.get("a")  # AUTH
    config = src.functions.config.readConfig()

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        account = next((i for i in config["account_list"] if i["auth"] == a), None)
        if account:
            if account.get("whitelist"):
                category_list = []
                for category in config["category_list"]:
                    if any(
                        category["id"] == whitelist
                        for whitelist in account["whitelist"]
                    ):
                        category_list.append(category)
                    else:
                        pass
                tmp_environment = {
                    "account_list": account,
                    "category_list": category_list,
                    "ui_config": config.get("ui_config"),
                }
                return (
                    flask.jsonify(
                        {
                            "code": 200,
                            "content": tmp_environment,
                            "message": "Environment permissions sent successfully.",
                            "success": True,
                        }
                    ),
                    200,
                )
            else:
                tmp_environment = {
                    "account_list": account,
                    "category_list": config["category_list"],
                    "ui_config": config.get("ui_config"),
                }
                return (
                    flask.jsonify(
                        {
                            "code": 200,
                            "content": tmp_environment,
                            "message": "Environment permissions sent successfully.",
                            "success": True,
                        }
                    ),
                    200,
                )
        else:
            tmp_environment = {
                "account_list": {"pic": "k"},
                "category_list": config["category_list"],
                "ui_config": config.get("ui_config"),
            }
            return (
                flask.jsonify(
                    {
                        "code": 200,
                        "content": tmp_environment,
                        "message": "Environment permissions sent successfully.",
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
                    "message": "Your credentials are invalid.",
                    "success": False,
                }
            ),
            401,
        )
