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
                "https://api.themoviedb.org/3/%s/%s/videos?api_key=%s&language=%s"
                % (t, id, config.get("tmdb_api_key"), config.get("language", "en"))
            ).json()
            if trailers:
                if len(trailers.get("results", [])) > 0:
                    trailer = next(
                        (
                            i
                            for i in trailers["results"]
                            if i["official"] == True
                            and i["type"] == "Trailer"
                            and i["site"] == "YouTube"
                        ),
                        next(
                            (
                                i
                                for i in trailers["results"]
                                if i["type"] == "Trailer" and i["site"] == "YouTube"
                            ),
                            trailers["results"][0],
                        ),
                    )
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
        elif api == "anilist":
            query = """
                query ($id: Int) {
                    Media(id: $id, type: ANIME) {
                        trailer {
                            id
                            site
                        }
                    }
                }
            """
            variables = {"id": id}
            response = requests.post(
                "https://graphql.anilist.co",
                json={"query": query, "variables": variables},
            ).json()
            if response != None:
                if response.get("data", {}).get("Media", {}).get("trailer"):
                    trailer = response["data"]["Media"]["trailer"]
                    if trailer.get("site") == "youtube":
                        trailer = {
                            "type": "trailer",
                            "site": "YouTube",
                            "key": trailer.get("id"),
                        }
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
