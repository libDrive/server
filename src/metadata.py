import json
import os
import re
import time

import requests

import src.tree
import src.walk


def parseName(name):
    match_1 = re.search(
        r'''^\(([1-2][0-9]{3})\)([^\.]*)''', name)  # Example: (2008) Iron Man.mkv
    match_2 = re.search(
        r'''^([^\.]{1,}?)\(([1-2][0-9]{3})\)''', name)  # Example: Iron Man (2008).mkv
    match_3 = re.search(r'''^([^\*]{1,}?)([1-2][0-9]{3})[^\*]''',
                        name)  # Example: Iron.Man.2008.REMASTERED.1080p.BluRay.x265-RARBG.mkv
    if match_1:
        try:
            title = match_1.group(2)
            year = match_1.group(1)
            return title, year
        except:
            pass
    elif match_2:
        try:
            title = match_2.group(1)[:-1]
            year = match_2.group(2)
            return title, year
        except:
            pass
    elif match_3:
        try:
            if match_3.group(1) != "(":
                title = match_3.group(1).replace(".", " ")[:-1]
                year = match_3.group(2)
                return title, year
        except:
            pass


def mediaIdentifier(tmdb_api_key, title, year, backdrop_base_url, poster_base_url, movie=False, tv=False):
    if movie:
        search_url = "http://api.themoviedb.org/3/search/movie?api_key=" + \
            tmdb_api_key+"&query=" + title + "&year=" + year
        search_content = json.loads((requests.get(search_url)).content)
        try:
            title = search_content["results"][0]["title"]
        except:
            pass
        try:
            posterPath = poster_base_url + \
                search_content["results"][0]["poster_path"]
        except:
            posterPath = ""
        try:
            backdropPath = backdrop_base_url + \
                search_content["results"][0]["backdrop_path"]
        except:
            backdropPath = ""
        try:
            releaseDate = search_content["results"][0]["release_date"]
        except:
            releaseDate = year + "-01-01"
        try:
            overview = search_content["results"][0]["overview"]
        except:
            overview = ""
        try:
            tmdbId = search_content["results"][0]["id"]
        except:
            tmdbId = ""
        try:
            popularity = search_content["results"][0]["popularity"]
        except:
            popularity = 0.0
        return title, posterPath, backdropPath, releaseDate, overview, tmdbId, popularity
    elif tv:
        search_url = "http://api.themoviedb.org/3/search/tv?api_key=" + \
            tmdb_api_key+"&query=" + title + "&year=" + year
        search_content = json.loads((requests.get(search_url)).content)
        try:
            title = search_content["results"][0]["name"]
        except:
            pass
        try:
            posterPath = poster_base_url + \
                search_content["results"][0]["poster_path"]
        except:
            posterPath = ""
        try:
            backdropPath = backdrop_base_url + \
                search_content["results"][0]["backdrop_path"]
        except:
            backdropPath = ""
        try:
            releaseDate = search_content["results"][0]["first_air_date"]
        except:
            releaseDate = year + "-01-01"
        try:
            overview = search_content["results"][0]["overview"]
        except:
            overview = ""
        try:
            tmdbId = search_content["results"][0]["id"]
        except:
            tmdbId = ""
        try:
            popularity = search_content["results"][0]["popularity"]
        except:
            popularity = 0.0

        return title, posterPath, backdropPath, releaseDate, overview, tmdbId, popularity


def readMetadata(category_list):
    if os.path.exists("metadata"):
        pass
    else:
        os.mkdir("metadata")
    metadata_dir = os.listdir("metadata")
    if len(metadata_dir) > 4:
        os.remove("metadata/"+min(metadata_dir))
        metadata_file = max(metadata_dir)
        with open("metadata/"+metadata_file, "r") as r:
            metadata = json.load(r)
    elif 0 < len(metadata_dir) < 6:
        metadata_file = max(metadata_dir)
        with open("metadata/"+metadata_file, "r") as r:
            metadata = json.load(r)
    else:
        metadata = []
        for category in category_list:
            tmp = category
            tmp["children"] = []
            metadata.append(tmp)
    return metadata


def writeMetadata(category_list, drive, tmdb_api_key, backdrop_base_url, poster_base_url):
    placeholder_metadata = []
    for category in category_list:
        if category["type"] == "movies":
            root = drive.files().get(
                fileId=category["id"], supportsAllDrives=True).execute()
            tmp_metadata = src.tree.driveTree(root, drive)
            tmp_metadata["categoryInfo"] = category
            tmp_metadata["length"] = len(tmp_metadata["children"])
            for item in tmp_metadata["children"]:
                if item["type"] == "file":
                    try:
                        title, year = parseName(item["name"])
                        item["title"], item["posterPath"], item["backdropPath"], item["releaseDate"], item["overview"], item["tmdbId"], item["popularity"] = mediaIdentifier(
                            tmdb_api_key, title, year, backdrop_base_url, poster_base_url, True, False)
                    except:
                        item["title"], item["posterPath"], item["backdropPath"], item["releaseDate"], item["overview"], item[
                            "tmdbId"] = item["name"][:-len(item["fullFileExtention"])], "", "", "1900-01-01", ""

            placeholder_metadata.append(tmp_metadata)
        elif category["type"] == "tv":
            root = drive.files().get(
                fileId=category["id"], supportsAllDrives=True).execute()
            tmp_metadata = src.tree.driveTree(root, drive)
            tmp_metadata["categoryInfo"] = category
            tmp_metadata["length"] = len(tmp_metadata["children"])
            for item in tmp_metadata["children"]:
                if item["type"] == "directory":
                    try:
                        title, year = parseName(item["name"])
                        item["title"], item["posterPath"], item["backdropPath"], item["releaseDate"], item["overview"], item["tmdbId"], item["popularity"] = mediaIdentifier(
                            tmdb_api_key, title, year, backdrop_base_url, poster_base_url, False, True)
                    except:
                        item["title"], item["posterPath"], item["backdropPath"], item["releaseDate"], item["overview"], item[
                            "tmdbId"] = item["name"][:-len(item["fullFileExtention"])], "", "", "1900-01-01", ""

            placeholder_metadata.append(tmp_metadata)

    metadata = placeholder_metadata

    if os.path.exists("./metadata"):
        pass
    else:
        os.mkdir("./metadata")
    metadata_file_name = "metadata/"+time.strftime("%Y%m%d-%H%M%S")+".json"
    with open(metadata_file_name, "w+") as w:
        w.write(json.dumps(metadata))

    return metadata


def jsonExtract(obj=list(), key="", getObj=True):
    arr = []
    arr2 = []

    def extract(obj, arr, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
                    arr2.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr, arr2

    values, values2 = extract(obj, arr, key)
    if getObj == True:
        return values2
    else:
        return values
