import json
import os
import re
import time

import requests

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
            tmdbId = search_content["results"][0]["id"]
        except:
            tmdbId = ""
        try:
            popularity = search_content["results"][0]["popularity"]
        except:
            popularity = 0.0
        return title, posterPath, backdropPath, releaseDate, tmdbId, popularity
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
            tmdbId = search_content["results"][0]["id"]
        except:
            tmdbId = ""
        try:
            popularity = search_content["results"][0]["popularity"]
        except:
            popularity = 0.0

        return title, posterPath, backdropPath, releaseDate, tmdbId, popularity


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
            tmp["files"] = []
            metadata.append(tmp)
    return metadata


def writeMetadata(category_list, drive, tmdb_api_key, backdrop_base_url, poster_base_url):
    placeholder_metadata = []
    for category in category_list:
        index = next((i for i, item in enumerate(category_list) if (
            item["name"] == category["name"]) and (item["id"] == category["id"])), None)
        if category["type"] == "movies":
            tmp_metadata = []
            for path, root, dirs, files in src.walk.driveWalk(category["id"], False, drive):
                root["path"] = path
                deleteList = []
                processNo = 0
                for file in files:
                    if "video" in file["mimeType"]:
                        file["path"] = path
                        try:
                            title, year = parseName(
                                file["name"])
                            file["title"], file["posterPath"], file["backdropPath"], file["releaseDate"], file["tmdbId"], file["popularity"] = mediaIdentifier(
                                tmdb_api_key, title, year, backdrop_base_url, poster_base_url, True, False)
                        except:
                            file["title"], file["posterPath"], file["backdropPath"], file["releaseDate"], file["tmdbId"] = file["name"][:-len(
                                file["fullFileExtention"])], "", "", "1900-01-01", ""
                    else:
                        deleteList.insert(0, processNo)
                    processNo += 1    
                if len(deleteList) > 0:
                    for item in deleteList:
                        del files[item]   
  
                for dir in dirs:
                    dir["path"] = path

                root["files"] = files
                root["folders"] = dirs

                stdin = "tmp_metadata"
                for l in range(len(path)-2):
                    stdin = stdin + "[-1]['folders']"
                eval(stdin+".append(root)")
            placeholder_metadata.append({"name": category["name"], "type": category["type"],
                                         "id": category["id"], "driveId": category["driveId"], "length": (len(tmp_metadata[0]["files"])+len(tmp_metadata[0]["folders"])), "files": tmp_metadata[0]["files"], "folders": tmp_metadata[0]["folders"]})
        elif category["type"] == "tv":
            tmp_metadata = []
            for path, root, dirs, files in src.walk.driveWalk(category["id"], False, drive):
                root["path"] = path
                deleteList = []
                processNo = 0
                for file in files:
                    if "video" in file["mimeType"]:
                        file["path"] = path
                    else:
                        deleteList.insert(0, processNo)
                    processNo += 1
                if len(deleteList) > 0:
                    for item in deleteList:
                        del files[item]

                for dir in dirs:
                    dir["path"] = path
                    try:
                        title, year = parseName(
                            dir["name"])
                        dir["title"], dir["posterPath"], dir["backdropPath"], dir["releaseDate"], dir["tmdbId"], dir["popularity"] = mediaIdentifier(
                            tmdb_api_key, title, year, backdrop_base_url, poster_base_url, False, True)
                    except:
                        dir["title"], dir["posterPath"], dir["backdropPath"], dir["releaseDate"], dir["tmdbId"] = dir["name"], "", "", "1900-01-01", ""

                root["files"] = files
                root["folders"] = dirs
                stdin = "tmp_metadata"
                for l in range(len(path)-2):
                    stdin = stdin + "[-1]['folders']"
                eval(stdin+".append(root)")
            placeholder_metadata.append({"name": category["name"], "type": category["type"],
                                         "id": category["id"], "driveId": category["driveId"], "length": (len(tmp_metadata[0]["files"])+len(tmp_metadata[0]["folders"])), "files": tmp_metadata[0]["files"], "folders": tmp_metadata[0]["folders"]})

    metadata = placeholder_metadata

    if os.path.exists("./metadata"):
        pass
    else:
        os.mkdir("./metadata")
    with open("./metadata/"+time.strftime("%Y%m%d-%H%M%S")+".json", "w+") as w:
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
