import random

import flask
import src.functions.config
import src.functions.credentials
import src.functions.drivetools
import src.functions.metadata

metadataBP = flask.Blueprint("metadata", __name__)


@metadataBP.route("/api/v1/metadata")
async def metadataFunction():
    a = flask.request.args.get("a")  # AUTH
    c = flask.request.args.get("c")  # CATEGORY
    g = flask.request.args.get("g")  # GENRE
    id = flask.request.args.get("id")  # ID
    q = flask.request.args.get("q")  # QUERY
    r = flask.request.args.get("r")  # RANGE
    s = flask.request.args.get("s")  # SORT-ORDER
    rmdup = flask.request.args.get("rmdup")  # REMOVE DUPLICATES
    rmnobanner = flask.request.args.get("rmnobanner")  # REMOVE NO BANNER
    config = src.functions.config.readConfig()
    tmp_metadata = src.functions.metadata.readMetadata(config)

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        account = next((i for i in config["account_list"] if i["auth"] == a), None)
        whitelisted_categories_metadata = []
        for category in tmp_metadata:
            category_config = next(
                (i for i in config["category_list"] if i["id"] == category["id"]), None
            )
            if category_config:
                if category_config.get("whitelist"):
                    if account["auth"] in category_config.get("whitelist"):
                        whitelisted_categories_metadata.append(category)
                else:
                    whitelisted_categories_metadata.append(category)
            else:
                whitelisted_categories_metadata.append(category)
        tmp_metadata = whitelisted_categories_metadata
        whitelisted_accounts_metadata = []
        if account:
            if account.get("whitelist"):
                for x in tmp_metadata:
                    if any(x["id"] == whitelist for whitelist in account["whitelist"]):
                        whitelisted_accounts_metadata.append(x)
                tmp_metadata = whitelisted_accounts_metadata
        if c:
            tmp_metadata = [
                next((i for i in tmp_metadata if i["categoryInfo"]["name"] == c), None)
            ]
            if tmp_metadata:
                pass
            else:
                return (
                    flask.jsonify(
                        {
                            "code": 400,
                            "content": None,
                            "message": "The category provided could not be found.",
                            "success": False,
                        }
                    ),
                    400,
                )
        if g:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = [
                    item for item in category["children"] if g in item["genres"]
                ]
                index += 1
        if q:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = [
                    item
                    for item in category["children"]
                    if q.lower() in item["title"].lower()
                ]
                index += 1
        if s:
            index = 0
            for category in tmp_metadata:
                if s == "alphabet-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: k["title"]
                        )
                    except:
                        pass
                elif s == "alphabet-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: k["title"], reverse=True
                        )
                    except:
                        pass
                elif s == "date-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: tuple(
                                map(int, k.get("releaseDate", "1900-01-01").split("-"))
                            ),
                        )
                    except:
                        pass
                elif s == "date-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: tuple(
                                map(int, k.get("releaseDate", "1900-01-01").split("-"))
                            ),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "popularity-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: float(k.get("popularity", 0.0)),
                        )
                    except:
                        pass
                elif s == "popularity-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: float(k.get("popularity", 0.0)),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "vote-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: float(k.get("voteAverage", 0.0)),
                        )
                    except:
                        pass
                elif s == "vote-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: float(k.get("voteAverage", 0.0)),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "random":
                    try:
                        random.shuffle(tmp_metadata[index]["children"])
                    except:
                        pass
                else:
                    return (
                        flask.jsonify(
                            {
                                "code": 400,
                                "content": None,
                                "message": "Bad request! Sorting parameter '%s' does not exist."
                                % (s),
                                "success": False,
                            }
                        ),
                        400,
                    )
                index += 1
        if rmnobanner == "true" or config.get("remove_no_poster") == True:
            for category in tmp_metadata:
                tmp_children = []
                for item in category["children"]:
                    try:
                        if item.get("posterPath") not in ["", None]:
                            tmp_children.append(item)
                    except:
                        pass
                category["children"] = tmp_children
        if rmdup == "true" or config.get("remove_duplicates") == True:
            for category in tmp_metadata:
                unique = ["null"]
                tmp_children = []
                for item in category["children"]:
                    try:
                        if item.get("apiId", "null") not in unique:
                            unique.append(item["apiId"])
                            tmp_children.append(item)
                        elif item.get("apiId") == None:
                            tmp_children.append(item)
                    except:
                        pass
                category["children"] = tmp_children
        for x in tmp_metadata:
            x["length"] = len(x["children"])
        if id:
            tmp_metadata = src.functions.metadata.jsonExtract(
                tmp_metadata, "id", id, False
            )
            config, drive = src.functions.credentials.refreshCredentials(config)
            if tmp_metadata:
                if config.get("build_type") == "full":
                    if tmp_metadata.get("type") == "directory":
                        tmp_metadata["parent_children"] = []
                        for item in src.functions.drivetools.driveIter(
                            {"id": tmp_metadata["parents"][0]}, drive, "PLACEHOLDER-X"
                        ):
                            if item["mimeType"] == "application/vnd.google-apps.folder":
                                item["type"] = "directory"
                                tmp_metadata["parent_children"].append(item)
                else:
                    if (
                        tmp_metadata.get("title")
                        and tmp_metadata.get("type") == "directory"
                    ):
                        tmp_metadata["children"] = []
                        for item in src.functions.drivetools.driveIter(
                            tmp_metadata, drive, "video"
                        ):
                            if item["mimeType"] == "application/vnd.google-apps.folder":
                                item["type"] = "directory"
                                tmp_metadata["children"].append(item)
                            else:
                                item["type"] = "file"
                                tmp_metadata["children"].append(item)
                    elif tmp_metadata.get("type") == "directory":
                        tmp_metadata["parent_children"] = []
                        for item in src.functions.drivetools.driveIter(
                            {"id": tmp_metadata["parents"][0]}, drive, "PLACEHOLDER-X"
                        ):
                            if item["mimeType"] == "application/vnd.google-apps.folder":
                                item["type"] = "directory"
                                tmp_metadata["parent_children"].append(item)
                return (
                    flask.jsonify(
                        {
                            "code": 200,
                            "content": tmp_metadata,
                            "message": "Metadata parsed successfully.",
                            "success": True,
                        }
                    ),
                    200,
                )
            tmp_metadata = (
                drive.files()
                .get(
                    fileId=id, supportsAllDrives=True, fields="id,name,mimeType,parents"
                )
                .execute()
            )
            if tmp_metadata["mimeType"] == "application/vnd.google-apps.folder":
                tmp_metadata["type"] = "directory"
                tmp_metadata["children"] = []
                tmp_metadata["parent_children"] = []
                for item in src.functions.drivetools.driveIter(
                    tmp_metadata, drive, "video"
                ):
                    if (
                        tmp_metadata.get("mimeType")
                        == "application/vnd.google-apps.folder"
                    ):
                        tmp_metadata["type"] = "directory"
                        tmp_metadata["children"].append(item)
                    else:
                        tmp_metadata["type"] = "file"
                        tmp_metadata["children"].append(item)
                for item in src.functions.drivetools.driveIter(
                    {"id": tmp_metadata["parents"][0]}, drive, "PLACEHOLDER-X"
                ):
                    if item["mimeType"] == "application/vnd.google-apps.folder":
                        item["type"] = "directory"
                        tmp_metadata["parent_children"].append(item)
        if r:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = eval(
                    "category['children']" + "[" + r + "]"
                )
                index += 1
        return (
            flask.jsonify(
                {
                    "code": 200,
                    "content": tmp_metadata,
                    "message": "Metadata parsed successfully.",
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
