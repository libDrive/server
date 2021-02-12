import json
import os
import re
import time

import requests

import src.tree
import src.walk


def parseName(name):
    reg_1 = r'^[\(\[\{](?P<year>\d{4})[\)\]\}]\s(?P<title>[^.]+).*(?P<extention>\..*)?$' # (2008) Iron Man.mkv
    reg_2 = r'^(?P<title>.*)\s[\(\[\{](?P<year>\d{4})[\)\]\}].*(?P<extention>\..*)?$' # Iron Man (2008).mkv
    reg_3 = r'^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*(?P<extention>\..*)?$' # Iron.Man.2008.1080p.WEBRip.DDP5.1.Atmos.x264.mkv
    reg_4 = r'^(?P<year>)(.*).*(?P<extention>\..*)?$' # Iron Man.mkv
    if re.match(reg_1, name):
        match = re.search(reg_1, name)
    elif re.match(reg_2, name):
        match = re.search(reg_2, name)
    elif re.match(reg_3, name):
        match = re.search(reg_3, name)
    elif re.match(reg_4, name):
        match = re.search(reg_4, name)
    else:
        return
    return match["title"], match["year"]


def mediaIdentifier(tmdb_api_key, title, year, backdrop_base_url, poster_base_url, movie=False, tv=False):
    if movie:
        search_url = "https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s&year=%s" % (
            tmdb_api_key, title, year)
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
            releaseDate = "%s-01-01" % (year)
        try:
            overview = search_content["results"][0]["overview"]
        except:
            overview = ""
        try:
            popularity = search_content["results"][0]["popularity"]
        except:
            popularity = 0.0
        return title, posterPath, backdropPath, releaseDate, overview, popularity
    elif tv:
        search_url = "https://api.themoviedb.org/3/search/tv?api_key=%s&query=%s&year=%s" % (
            tmdb_api_key, title, year)
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
            releaseDate = "%s-01-01" % (year)
        try:
            overview = search_content["results"][0]["overview"]
        except:
            overview = ""
        try:
            popularity = search_content["results"][0]["popularity"]
        except:
            popularity = 0.0

        return title, posterPath, backdropPath, releaseDate, overview, popularity


def readMetadata(category_list):
    try:
        os.mkdir("metadata")
    except:
        pass
    metadata_dir = os.listdir("metadata")
    if len(metadata_dir) == 0:
        metadata = []
        for category in category_list:
            tmp = category
            tmp["children"] = []
            metadata.append(tmp)
    elif len(metadata_dir) <= 5:
        metadata_file = max(metadata_dir)
        with open("metadata/%s" % (metadata_file), "r") as r:
            metadata = json.load(r)
    elif len(metadata_dir) > 5:
        os.remove("metadata/%s" % (min(metadata_dir)))
        metadata_file = max(metadata_dir)
        with open("metadata/%s" % (metadata_file), "r") as r:
            metadata = json.load(r)
    else:
        pass
    return metadata


def writeMetadata(category_list, drive, tmdb_api_key, backdrop_base_url, poster_base_url):
    placeholder_metadata = []
    for category in category_list:
        if category["type"] == "Movies":
            root = drive.files().get(
                fileId=category["id"], supportsAllDrives=True).execute()
            tree = root
            tree["type"] = "directory"
            tree["children"] = []
            tmp_metadata = src.walk.driveWalk(root, tree, [], drive)
            tmp_metadata["children"] = [x for x in tmp_metadata["children"]
                                        if x["mimeType"] != "application/vnd.google-apps.folder"]
            tmp_metadata["categoryInfo"] = category
            tmp_metadata["length"] = len(tmp_metadata["children"])
            for item in tmp_metadata["children"]:
                if item["type"] == "file":
                    try:
                        title, year = parseName(item["name"])
                        item["title"], item["posterPath"], item["backdropPath"], item["releaseDate"], item["overview"], item["popularity"] = mediaIdentifier(
                            tmdb_api_key, title, year, backdrop_base_url, poster_base_url, True, False)
                    except:
                        item["title"], item["posterPath"], item["backdropPath"], item[
                            "releaseDate"], item["overview"] = item["name"], "", "", "1900-01-01", ""

            placeholder_metadata.append(tmp_metadata)
        elif category["type"] == "TV Shows":
            root = drive.files().get(
                fileId=category["id"], supportsAllDrives=True).execute()
            tmp_metadata = src.tree.driveTree(root, drive)
            tmp_metadata["categoryInfo"] = category
            tmp_metadata["length"] = len(tmp_metadata["children"])
            for item in tmp_metadata["children"]:
                if item["type"] == "directory":
                    try:
                        title, year = parseName(item["name"])
                        item["title"], item["posterPath"], item["backdropPath"], item["releaseDate"], item["overview"], item["popularity"] = mediaIdentifier(
                            tmdb_api_key, title, year, backdrop_base_url, poster_base_url, False, True)
                    except:
                        item["title"], item["posterPath"], item["backdropPath"], item[
                            "releaseDate"], item["overview"] = item["name"], "", "", "1900-01-01", ""

            placeholder_metadata.append(tmp_metadata)

    metadata = placeholder_metadata

    if os.path.exists("./metadata"):
        pass
    else:
        os.mkdir("./metadata")
    metadata_file_name = "metadata/%s.json" % (time.strftime("%Y%m%d-%H%M%S"))
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
