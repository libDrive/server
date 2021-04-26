import datetime
import json
import os
import re
import time

import googleapiclient
import requests

import src.drivetools


def parseMovie(name):
    # (2008) Iron Man.mkv
    reg_1 = r"^[\(\[\{](?P<year>\d{4})[\)\]\}]\s(?P<title>[^.]+).*(?P<extention>\..*)?$"
    # Iron Man (2008).mkv
    reg_2 = r"^(?P<title>.*)\s[\(\[\{](?P<year>\d{4})[\)\]\}].*(?P<extention>\..*)?$"
    # Iron.Man.2008.1080p.WEBRip.DDP5.1.Atmos.x264.mkv
    reg_3 = r"^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*(?P<extention>\..*)?$"
    reg_4 = r"^(?P<year>)(?P<title>.*).*(?P<extention>\..*?$)"  # Iron Man.mkv
    if re.match(reg_1, name):
        match = re.search(reg_1, name)
    elif re.match(reg_2, name):
        match = re.search(reg_2, name)
    elif re.match(reg_3, name):
        match = re.search(reg_3, name)
        return match["title"].replace(".", " "), match["year"]
    elif re.match(reg_4, name):
        match = re.search(reg_4, name)
    else:
        return
    return match["title"], match["year"]


def parseTV(name):
    # (2019) The Mandalorian
    reg_1 = r"^[\(\[\{](?P<year>\d{4})[\)\]\}]\s(?P<title>[^.]+).*$"
    # The Mandalorian (2019)
    reg_2 = r"^(?P<title>.*)\s[\(\[\{](?P<year>\d{4})[\)\]\}].*$"
    # The.Mandalorian.2019.1080p.WEBRip
    reg_3 = r"^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*$"
    reg_4 = r"^(?P<year>)(?P<title>.*)$"  # The Mandalorian
    if re.match(reg_1, name):
        match = re.search(reg_1, name)
    elif re.match(reg_2, name):
        match = re.search(reg_2, name)
    elif re.match(reg_3, name):
        match = re.search(reg_3, name)
        return match["title"].replace(".", " "), match["year"]
    elif re.match(reg_4, name):
        match = re.search(reg_4, name)
    else:
        return
    return match["title"], match["year"]


def mediaIdentifier(
    tmdb_api_key, title, year, backdrop_base_url, poster_base_url, movie=False, tv=False
):
    if movie:
        search_url = (
            "https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s&year=%s"
            % (tmdb_api_key, title, year)
        )
        search_content = json.loads((requests.get(search_url)).content)
        try:
            title = search_content["results"][0]["title"]
        except:
            pass
        try:
            posterPath = poster_base_url + search_content["results"][0]["poster_path"]
        except:
            posterPath = None
        try:
            backdropPath = (
                backdrop_base_url + search_content["results"][0]["backdrop_path"]
            )
        except:
            backdropPath = None
        try:
            releaseDate = search_content["results"][0]["release_date"]
        except:
            releaseDate = "%s-01-01" % (year)
        try:
            overview = search_content["results"][0]["overview"]
        except:
            overview = None
        try:
            popularity = search_content["results"][0]["popularity"]
        except:
            popularity = 0.0
        try:
            voteAverage = search_content["results"][0]["vote_average"]
        except:
            voteAverage = 0.0
        return (
            title,
            posterPath,
            backdropPath,
            releaseDate,
            overview,
            popularity,
            voteAverage,
        )
    elif tv:
        search_url = (
            "https://api.themoviedb.org/3/search/tv?api_key=%s&query=%s&first_air_date_year=%s"
            % (tmdb_api_key, title, year)
        )
        search_content = json.loads((requests.get(search_url)).content)
        try:
            title = search_content["results"][0]["name"]
        except:
            pass
        try:
            posterPath = poster_base_url + search_content["results"][0]["poster_path"]
        except:
            posterPath = None
        try:
            backdropPath = (
                backdrop_base_url + search_content["results"][0]["backdrop_path"]
            )
        except:
            backdropPath = None
        try:
            releaseDate = search_content["results"][0]["first_air_date"]
        except:
            releaseDate = "%s-01-01" % (year)
        try:
            overview = search_content["results"][0]["overview"]
        except:
            overview = None
        try:
            popularity = search_content["results"][0]["popularity"]
        except:
            popularity = 0.0
        try:
            voteAverage = search_content["results"][0]["vote_average"]
        except:
            voteAverage = 0.0

        return (
            title,
            posterPath,
            backdropPath,
            releaseDate,
            overview,
            popularity,
            voteAverage,
        )


def readMetadata(config):
    if os.path.exists("./metadata.json"):
        with open("./metadata.json", "r") as r:
            metadata = json.load(r)
    else:
        metadata = []
        build_interval = config.get("build_interval")
        if not build_interval:
            build_interval = 0
        for category in config["category_list"]:
            tmp = {
                "kind": "drive#file",
                "id": "",
                "name": "",
                "mimeType": "application/vnd.google-apps.folder",
                "teamDriveId": "",
                "driveId": "",
                "type": "directory",
                "children": [],
                "categoryInfo": category,
                "length": 0,
                "buildTime": str(
                    datetime.datetime.utcnow()
                    - datetime.timedelta(minutes=build_interval + 1)
                ),
            }
            metadata.append(tmp)
    return metadata


def writeMetadata(config):
    configuration_url = "https://api.themoviedb.org/3/configuration?api_key=%s" % (
        config.get("tmdb_api_key")
    )
    configuration_content = json.loads(requests.get(configuration_url).content)
    backdrop_base_url = (
        configuration_content["images"]["secure_base_url"]
        + configuration_content["images"]["backdrop_sizes"][3]
    )
    poster_base_url = (
        configuration_content["images"]["secure_base_url"]
        + configuration_content["images"]["poster_sizes"][3]
    )

    placeholder_metadata = []
    count = 0
    for category in config["category_list"]:
        count += 1
        start_time = datetime.datetime.utcnow()
        config, drive = src.credentials.refreshCredentials(config)
        print(
            "\033[91mBUILDING METADATA FOR CATEGORY %s/%s (%s)...\033[0m"
            % (count, len(config["category_list"]), category["name"])
        )
        if category["type"] == "Movies":
            root = (
                drive.files()
                .get(fileId=category["id"], supportsAllDrives=True)
                .execute()
            )
            tree = root
            tree["type"] = "directory"
            tree["children"] = []
            tmp_metadata = src.drivetools.driveWalk(root, drive, root, "video")
            tmp_metadata["categoryInfo"] = category
            tmp_metadata["length"] = len(tmp_metadata["children"])
            tmp_metadata["buildTime"] = str(datetime.datetime.utcnow())
            for item in tmp_metadata["children"]:
                if item["type"] == "file":
                    try:
                        title, year = parseMovie(item["name"])
                        (
                            item["title"],
                            item["posterPath"],
                            item["backdropPath"],
                            item["releaseDate"],
                            item["overview"],
                            item["popularity"],
                            item["voteAverage"],
                        ) = mediaIdentifier(
                            config.get("tmdb_api_key"),
                            title,
                            year,
                            backdrop_base_url,
                            poster_base_url,
                            True,
                            False,
                        )
                    except:
                        (
                            item["title"],
                            item["posterPath"],
                            item["backdropPath"],
                            item["releaseDate"],
                            item["overview"],
                            item["popularity"],
                            item["voteAverage"],
                        ) = (item["name"], None, None, "1900-01-01", None, 0.0, 0.0)

            placeholder_metadata.append(tmp_metadata)
        elif category["type"] == "TV Shows":
            root = (
                drive.files()
                .get(fileId=category["id"], supportsAllDrives=True)
                .execute()
            )
            if root["mimeType"] == "application/vnd.google-apps.folder":
                if config.get("build_type") == "full":
                    root = src.drivetools.driveTree(root, drive, "video")
                elif config.get("build_type") == "live":
                    root["children"] = []
                    pass
                else:
                    root["type"] = "directory"
                    root["children"] = []
                    for item in src.drivetools.driveIter(root, drive, "video"):
                        if root["mimeType"] == "application/vnd.google-apps.folder":
                            item["type"] = "directory"
                            root["children"].append(item)
                        else:
                            root["type"] = "file"
                            root["children"].append(item)
            tmp_metadata = root
            tmp_metadata["categoryInfo"] = category
            tmp_metadata["length"] = len(tmp_metadata["children"])
            tmp_metadata["buildTime"] = str(datetime.datetime.utcnow())
            for item in tmp_metadata["children"]:
                if item["type"] == "directory":
                    try:
                        title, year = parseTV(item["name"])
                        (
                            item["title"],
                            item["posterPath"],
                            item["backdropPath"],
                            item["releaseDate"],
                            item["overview"],
                            item["popularity"],
                            item["voteAverage"],
                        ) = mediaIdentifier(
                            config.get("tmdb_api_key"),
                            title,
                            year,
                            backdrop_base_url,
                            poster_base_url,
                            False,
                            True,
                        )
                    except:
                        (
                            item["title"],
                            item["posterPath"],
                            item["backdropPath"],
                            item["releaseDate"],
                            item["overview"],
                            item["popularity"],
                            item["voteAverage"],
                        ) = (item["name"], None, None, "1900-01-01", None, 0.0, 0.0)

            placeholder_metadata.append(tmp_metadata)
        print("DONE IN %s.\n" % (str(datetime.datetime.utcnow() - start_time)))

    metadata = placeholder_metadata

    with open("./metadata.json", "w+") as w:
        json.dump(obj=metadata, fp=w, sort_keys=True, indent=4)

    if os.getenv("LIBDRIVE_CLOUD"):
        config, drive = src.credentials.refreshCredentials(config)
        params = {
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
            "fields": "files(id,name)",
            "q": "'%s' in parents and trashed = false and mimeType = 'application/json'"
            % (os.getenv("LIBDRIVE_CLOUD")),
        }
        files = drive.files().list(**params).execute()["files"]
        metadata_file = next((i for i in files if i["name"] == "metadata.json"), None)
        file_metadata = {
            "name": "metadata.json",
            "mimeType": "application/json",
            "parents": [os.getenv("LIBDRIVE_CLOUD")],
        }
        media = googleapiclient.http.MediaFileUpload(
            "./metadata.json", mimetype="application/json", resumable=True
        )
        if metadata_file:
            params = {
                "fileId": metadata_file["id"],
                "media_body": media,
                "supportsAllDrives": True,
            }
            drive.files().update(**params).execute()
        else:
            params = {
                "body": file_metadata,
                "media_body": media,
                "supportsAllDrives": True,
            }
            drive.files().create(**params).execute()
    return metadata


def jsonExtract(obj, key, val, multi=False):
    arr = []

    def extract(obj, arr, key, val):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key, val)
                elif key and val:
                    if k == key and v == val:
                        arr.append(obj)
                elif key or val:
                    if k == key or v == val:
                        arr.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key, val)
        return arr

    results = extract(obj, arr, key, val)
    if multi == False and len(results) > 0:
        return results[0]
    elif multi == True and len(results) > 0:
        return results
    else:
        return None