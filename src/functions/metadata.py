import datetime
import json
import logging
import os
import re
import time
import urllib

import googleapiclient
import requests
import src.functions.drivetools

LOGGER = logging.getLogger()


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
        return None, None
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
        return None, None
    return match["title"], match["year"]


def mediaIdentifier(
    tmdb_api_key,
    title,
    year,
    backdrop_base_url,
    poster_base_url,
    movie_genre_ids,
    tv_genre_ids,
    language,
    movie=False,
    tv=False,
    anime=False,
):
    if year == None or year == "":
        tmp_year = "1900"
    else:
        tmp_year = year
    if movie == True and anime == False:
        search_url = (
            "https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s&primary_release_year=%s&language=%s"
            % (tmdb_api_key, urllib.parse.quote(title.encode("utf-8")), year, language)
        )
        search_content = {"total_results": 0}
        for n in range(3):
            try:
                search_content = json.loads((requests.get(search_url)).content)
                break
            except Exception as e:
                n += 1
                LOGGER.error(
                    "\033[31mERROR RETRIEVING TMDB DATA FOR '%s'! RETRYING %s/%s...\033[0m"
                    % (title, n, 3),
                )
                LOGGER.error(str(e))
                time.sleep(0.5)
        if search_content.get("total_results") > 0:
            data = search_content["results"][0]
            if data.get("backdrop_path"):
                data["backdrop_path"] = backdrop_base_url + data.get("backdrop_path")
            else:
                data["backdrop_path"] = None
            if data.get("poster_path"):
                data["poster_path"] = poster_base_url + data.get("poster_path")
            else:
                data["poster_path"] = None
        else:
            data = dict(
                {
                    "adult": False,
                    "backdrop_path": None,
                    "genre_ids": [],
                    "original_language": None,
                    "overview": None,
                    "popularity": 70.412,
                    "poster_path": None,
                    "release_date": "%s-01-01" % (tmp_year),
                    "title": title,
                    "vote_average": 0.0,
                },
            )

        adult = data.get("adult", False)
        backdropPath = data.get("backdrop_path", None)
        genres = data.get("genre_ids", [])
        tmp_genres = []
        for genre in genres:
            for item in movie_genre_ids["genres"]:
                if item["id"] == genre:
                    tmp_genres.append(item["name"])
                    break
        genres = tmp_genres
        language = data.get("original_language", None)
        overview = data.get("overview", None)
        popularity = data.get("popularity", 0.0)
        posterPath = data.get("poster_path", None)
        releaseDate = data.get("release_date", "%s-01-01" % (tmp_year))
        title = data.get("title", title)
        voteAverage = data.get("vote_average", 0.0)
        return (
            adult,
            backdropPath,
            genres,
            language,
            overview,
            popularity,
            posterPath,
            releaseDate,
            title,
            voteAverage,
        )
    elif tv == True and anime == False:
        search_url = (
            "https://api.themoviedb.org/3/search/tv?api_key=%s&query=%s&first_air_date_year=%s&language=%s"
            % (tmdb_api_key, urllib.parse.quote(title.encode("utf-8")), year, language)
        )
        search_content = {"total_results": 0}
        for n in range(3):
            try:
                search_content = json.loads((requests.get(search_url)).content)
                break
            except Exception as e:
                n += 1
                LOGGER.error(
                    "\033[31mERROR RETRIEVING TMDB DATA FOR '%s'! RETRYING %s/%s...\033[0m"
                    % (title, n, 3),
                )
                LOGGER.error(str(e))
                time.sleep(0.5)
        if search_content.get("total_results") > 0:
            data = search_content["results"][0]
            if data.get("backdrop_path"):
                data["backdrop_path"] = backdrop_base_url + data.get("backdrop_path")
            else:
                data["backdrop_path"] = None
            if data.get("poster_path"):
                data["poster_path"] = poster_base_url + data.get("poster_path")
            else:
                data["poster_path"] = None
        else:
            data = dict(
                {
                    "backdrop_path": None,
                    "first_air_date": "%s-01-01" % (tmp_year),
                    "genre_ids": [],
                    "name": title,
                    "original_language": None,
                    "overview": None,
                    "popularity": 0.0,
                    "poster_path": None,
                    "vote_average": 0.0,
                },
            )
        backdropPath = data.get("backdrop_path", None)
        genres = data.get("genre_ids", [])
        tmp_genres = []
        for genre in genres:
            for item in tv_genre_ids["genres"]:
                if item["id"] == genre:
                    tmp_genres.append(item["name"])
                    break
        genres = tmp_genres
        language = data.get("original_language", None)
        overview = data.get("overview", None)
        popularity = data.get("popularity", 0.0)
        posterPath = data.get("poster_path", None)
        releaseDate = data.get("first_air_date", "%s-01-01" % (tmp_year))
        title = data.get("name", title)
        voteAverage = data.get("vote_average", 0.0)
        return (
            backdropPath,
            genres,
            language,
            overview,
            popularity,
            posterPath,
            releaseDate,
            title,
            voteAverage,
        )
    elif movie == True and anime == True:
        query = """
            query ($search: String, $seasonYear: Int) {
                Media(search: $search, seasonYear: $seasonYear, type: ANIME) {
                    title {
                        english
                        romaji
                        native
                    }
                    description
                    genres
                    isAdult
                    averageScore
                    popularity
                    startDate {
                        year
                        month
                        day
                    }
                    bannerImage
                    coverImage {
                        large
                    }
                }
            }
        """
        variables = {"search": title}
        if year != None and year != "":
            variables["seasonYear"] = year
        for n in range(3):
            try:
                response = requests.post(
                    "https://graphql.anilist.co",
                    json={"query": query, "variables": variables},
                ).json()
                break
            except Exception as e:
                n += 1
                LOGGER.error(
                    "\033[31mERROR RETRIEVING ANILIST DATA FOR '%s'! RETRYING %s/%s...\033[0m"
                    % (title, n, 3),
                )
                LOGGER.error(str(e))
                time.sleep(0.5)
        data = dict(
            {
                "isAdult": False,
                "title": {"english": title},
                "startDate": {"year": tmp_year, "month": "01", "day": "01"},
                "genres": [],
                "original_language": None,
                "description": None,
                "popularity": 0.0,
                "bannerImage": "",
                "coverImage": {"large": None},
                "averageScore": 0.0,
            },
        )
        if response != None:
            if response.get("data", {}).get("Media", None):
                data = response["data"]["Media"]
        if data.get("title", {}).get("english") == None:
            if data.get("title", {}).get("romaji") == None:
                if data.get("title", {}).get("native") == None:
                    data["title"] = title
                else:
                    data["title"] = data["title"]["native"]
            else:
                data["title"] = data["title"]["romaji"]
        else:
            data["title"] = data["title"]["english"]
        startDate = data.get("startDate", {})
        releases_date = "%s-%s-%s" % (
            startDate.get("year", tmp_year),
            startDate.get("month", "01"),
            startDate.get("day", "01"),
        )
        genres = []
        for genre in data.get("genres", []):
            genres.append(genre)
        if data.get("bannerImage") != None and data.get("bannerImage") != "":
            data["bannerImage"] = data["bannerImage"].replace("/small/", "/large/")
        if data.get("description") != None and data.get("description") != "":
            data["description"] = re.sub(re.compile("<.*?>"), "", data["description"])
        return (
            data.get("isAdult", False),
            data.get("bannerImage"),
            genres,
            data.get("original_language"),
            data.get("description"),
            data.get("popularity", 0.0),
            data.get("coverImage", {}).get("large"),
            releases_date,
            data.get("title", title),
            data.get("averageScore", 0.0),
        )
    elif tv == True and anime == True:
        query = """
            query ($search: String, $seasonYear: Int) {
                Media(search: $search, seasonYear: $seasonYear, type: ANIME) {
                    title {
                        english
                        romaji
                        native
                    }
                    description
                    genres
                    isAdult
                    averageScore
                    popularity
                    startDate {
                        year
                        month
                        day
                    }
                    bannerImage
                    coverImage {
                        large
                    }
                }
            }
        """
        variables = {"search": title}
        if year != None and year != "":
            variables["seasonYear"] = year
        for n in range(3):
            try:
                response = requests.post(
                    "https://graphql.anilist.co",
                    json={"query": query, "variables": variables},
                ).json()
                break
            except Exception as e:
                n += 1
                LOGGER.error(
                    "\033[31mERROR RETRIEVING ANILIST DATA FOR '%s'! RETRYING %s/%s...\033[0m"
                    % (title, n, 3),
                )
                LOGGER.error(str(e))
                time.sleep(0.5)
        data = dict(
            {
                "isAdult": False,
                "title": {"english": title},
                "startDate": {"year": tmp_year, "month": "01", "day": "01"},
                "genres": [],
                "original_language": None,
                "description": None,
                "popularity": 0.0,
                "bannerImage": "",
                "coverImage": {"large": None},
                "averageScore": 0.0,
            },
        )
        if response != None:
            if response.get("data", {}).get("Media", None):
                data = response["data"]["Media"]
        if data.get("title", {}).get("english") == None:
            if data.get("title", {}).get("romaji") == None:
                if data.get("title", {}).get("native") == None:
                    data["title"] = title
                else:
                    data["title"] = data["title"]["native"]
            else:
                data["title"] = data["title"]["romaji"]
        else:
            data["title"] = data["title"]["english"]
        startDate = data.get("startDate", {})
        releases_date = "%s-%s-%s" % (
            startDate.get("year", tmp_year),
            startDate.get("month", "01"),
            startDate.get("day", "01"),
        )
        genres = []
        for genre in data.get("genres", []):
            genres.append(genre)
        if data.get("bannerImage") != None and data.get("bannerImage") != "":
            data["bannerImage"] = data["bannerImage"].replace("/small/", "/large/")
        if data.get("description") != None and data.get("description") != "":
            data["description"] = re.sub(re.compile("<.*?>"), "", data["description"])
        return (
            data.get("isAdult", False),
            data.get("bannerImage"),
            genres,
            data.get("original_language"),
            data.get("description"),
            data.get("popularity", 0.0),
            data.get("coverImage", {}).get("large"),
            releases_date,
            data.get("title", title),
            data.get("averageScore", 0.0),
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
    configuration_content = json.loads(
        requests.get(
            "https://api.themoviedb.org/3/configuration?api_key=%s"
            % (config.get("tmdb_api_key"))
        ).content
    )
    backdrop_base_url = (
        configuration_content["images"]["secure_base_url"]
        + configuration_content["images"]["backdrop_sizes"][3]
    )
    poster_base_url = (
        configuration_content["images"]["secure_base_url"]
        + configuration_content["images"]["poster_sizes"][3]
    )

    movie_genre_ids = json.loads(
        requests.get(
            "https://api.themoviedb.org/3/genre/movie/list?api_key=%s"
            % (config.get("tmdb_api_key"))
        ).content
    )
    tv_genre_ids = json.loads(
        requests.get(
            "https://api.themoviedb.org/3/genre/tv/list?api_key=%s"
            % (config.get("tmdb_api_key"))
        ).content
    )

    placeholder_metadata = []
    count = 0
    for category in config["category_list"]:
        count += 1
        start_time = datetime.datetime.utcnow()
        config, drive = src.functions.credentials.refreshCredentials(config)
        LOGGER.info(
            "\033[32mBUILDING METADATA FOR CATEGORY %s/%s %s...\033[0m\n"
            % (count, len(config["category_list"]), category["name"])
        )
        for n in range(3):
            try:
                root = (
                    drive.files()
                    .get(fileId=category["id"], supportsAllDrives=True)
                    .execute()
                )
                break
            except Exception as e:
                n += 1
                LOGGER.error(
                    "\033[31mERROR RETRIEVING FOLDER '%s'! RETRYING %s/%s...\033[0m"
                    % (category["name"], n, 3),
                )
                LOGGER.error(str(e))
                time.sleep(0.5)
        if category["type"] == "Movies":
            tree = root
            tree["type"] = "directory"
            tree["children"] = []
            tmp_metadata = src.functions.drivetools.driveWalk(
                root, drive, root, "video"
            )
            tmp_metadata["categoryInfo"] = category
            tmp_metadata["length"] = len(tmp_metadata["children"])
            tmp_metadata["buildTime"] = str(datetime.datetime.utcnow())
            if category.get("anilist") == True:
                items_count = 0
                items_length = len(tmp_metadata["children"])
                for item in tmp_metadata["children"]:
                    items_count += 1
                    LOGGER.info(
                        "\033[93mSCRAPING %s/%s %s...\033[0m"
                        % (items_count, items_length, item["name"]),
                    )
                    if item["type"] == "file":
                        title, year = parseMovie(item["name"])
                        if title == None:
                            title = item["name"]
                        if year == None:
                            year = ""
                        (
                            item["adult"],
                            item["backdropPath"],
                            item["genres"],
                            item["language"],
                            item["overview"],
                            item["popularity"],
                            item["posterPath"],
                            item["releaseDate"],
                            item["title"],
                            item["voteAverage"],
                        ) = mediaIdentifier(
                            config.get("tmdb_api_key"),
                            title,
                            year,
                            backdrop_base_url,
                            poster_base_url,
                            movie_genre_ids,
                            tv_genre_ids,
                            category.get("language"),
                            True,
                            False,
                            True,
                        )
            else:
                items_count = 0
                items_length = len(tmp_metadata["children"])
                for item in tmp_metadata["children"]:
                    items_count += 1
                    LOGGER.info(
                        "\033[93mSCRAPING %s/%s %s...\033[0m"
                        % (items_count, items_length, item["name"])
                    )
                    if item["type"] == "file":
                        title, year = parseMovie(item["name"])
                        if title == None:
                            title = item["name"]
                        if year == None:
                            year = ""
                        (
                            item["adult"],
                            item["backdropPath"],
                            item["genres"],
                            item["language"],
                            item["overview"],
                            item["popularity"],
                            item["posterPath"],
                            item["releaseDate"],
                            item["title"],
                            item["voteAverage"],
                        ) = mediaIdentifier(
                            config.get("tmdb_api_key"),
                            title,
                            year,
                            backdrop_base_url,
                            poster_base_url,
                            movie_genre_ids,
                            tv_genre_ids,
                            category.get("language"),
                            True,
                            False,
                            False,
                        )

            placeholder_metadata.append(tmp_metadata)
        elif category["type"] == "TV Shows":
            if root["mimeType"] == "application/vnd.google-apps.folder":
                if config.get("build_type") == "full":
                    root["type"] = "directory"
                    root["children"] = []
                    for item in src.functions.drivetools.driveIter(
                        root, drive, "video"
                    ):
                        if root["mimeType"] == "application/vnd.google-apps.folder":
                            item["children"] = []
                            for x in src.functions.drivetools.driveIter(
                                item, drive, "video"
                            ):
                                if (
                                    x["mimeType"]
                                    == "application/vnd.google-apps.folder"
                                ):
                                    x["children"] = []
                                    for y in src.functions.drivetools.driveIter(
                                        x, drive, "video"
                                    ):
                                        if "video" in y["mimeType"]:
                                            x["children"].append(y)
                                    item["children"].append(x)
                            root["children"].append(item)
                else:
                    root["type"] = "directory"
                    root["children"] = []
                    for item in src.functions.drivetools.driveIter(
                        root, drive, "video"
                    ):
                        if root["mimeType"] == "application/vnd.google-apps.folder":
                            root["children"].append(item)
            tmp_metadata = root
            tmp_metadata["categoryInfo"] = category
            tmp_metadata["length"] = len(tmp_metadata["children"])
            tmp_metadata["buildTime"] = str(datetime.datetime.utcnow())
            if category.get("anilist") == True:
                items_count = 0
                items_length = len(tmp_metadata["children"])
                for item in tmp_metadata["children"]:
                    items_count += 1
                    LOGGER.info(
                        "\033[93mSCRAPING %s/%s %s...\033[0m"
                        % (items_count, items_length, item["name"]),
                    )
                    if item["type"] == "directory":
                        title, year = parseTV(item["name"])
                        if title == None:
                            title = item["name"]
                        if year == None:
                            year = ""
                        (
                            item["adult"],
                            item["backdropPath"],
                            item["genres"],
                            item["language"],
                            item["overview"],
                            item["popularity"],
                            item["posterPath"],
                            item["releaseDate"],
                            item["title"],
                            item["voteAverage"],
                        ) = mediaIdentifier(
                            config.get("tmdb_api_key"),
                            title,
                            year,
                            backdrop_base_url,
                            poster_base_url,
                            movie_genre_ids,
                            tv_genre_ids,
                            category.get("language"),
                            False,
                            True,
                            True,
                        )
            else:
                items_count = 0
                items_length = len(tmp_metadata["children"])
                for item in tmp_metadata["children"]:
                    items_count += 1
                    LOGGER.info(
                        "\033[93mSCRAPING %s/%s %s...\033[0m"
                        % (items_count, items_length, item["name"]),
                    )
                    if item["type"] == "directory":
                        title, year = parseTV(item["name"])
                        if title == None:
                            title = item["name"]
                        if year == None:
                            year = ""
                        (
                            item["backdropPath"],
                            item["genres"],
                            item["language"],
                            item["overview"],
                            item["popularity"],
                            item["posterPath"],
                            item["releaseDate"],
                            item["title"],
                            item["voteAverage"],
                        ) = mediaIdentifier(
                            config.get("tmdb_api_key"),
                            title,
                            year,
                            backdrop_base_url,
                            poster_base_url,
                            movie_genre_ids,
                            tv_genre_ids,
                            category.get("language"),
                            False,
                            True,
                            False,
                        )

            placeholder_metadata.append(tmp_metadata)
        LOGGER.info("\nDONE IN %s.\n" % (str(datetime.datetime.utcnow() - start_time)))

    metadata = placeholder_metadata

    with open("./metadata.json", "w+") as w:
        json.dump(obj=metadata, fp=w, sort_keys=True, indent=4)

    if os.getenv("LIBDRIVE_CLOUD"):
        config, drive = src.functions.credentials.refreshCredentials(config)
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
