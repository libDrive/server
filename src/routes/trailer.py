import flask
import requests
import src.functions.config

trailerBP = flask.Blueprint("trailer", __name__)


@trailerBP.route("/api/v1/trailer/<id>")
async def trailerFunction(id):
    a = flask.request.args.get("a")  # AUTH
    t = flask.request.args.get("t")  # TYPE
    api = flask.request.args.get("api")  # API
    config = src.functions.config.readConfig()

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        if api == "tmdb":
            trailers = requests.get(
                "https://api.themoviedb.org/3/%s/%s/videos?api_key=%s"
                % (t, id, config.get("tmdb_api_key"))
            ).json()
            if trailers:
                if len(trailers.get("results", [])) > 0:
                    trailer = next(
                        (
                            i
                            for i in trailers["results"]
                            if i["official"] == True
                            and i["type"] == "trailer"
                            and i["site"] == "YouTube"
                        ),
                        None,
                    )
                    if not trailer:
                        trailer = trailers["results"][0]
                    return (
                        {
                            "code": 200,
                            "content": trailer,
                            "message": "Trailer found successfully.",
                            "success": True,
                        },
                        200,
                    )
            return (
                {
                    "code": 404,
                    "content": None,
                    "message": "Trailer could not be found.",
                    "success": False,
                },
                404,
            )
