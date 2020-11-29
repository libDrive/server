import json
import os
import re
import time

import requests

from src.walk import driveWalk


def writeMetadata(category_list, drive):
    placeholder_metadata = []
    for category in category_list:
        index = next((i for i, item in enumerate(category_list) if (
            item["name"] == category["name"]) and (item["id"] == category["id"])), None)
        if category["type"] == "movies":
            tmp_metadata = []
            for path, root, dirs, files in driveWalk(category["id"], False, drive):
                root["files"] = files
                root["files"] = [ file for file in files if "video" in file["mimeType"] ]
                root["folders"] = dirs
                stdin = "tmp_metadata"
                for l in range(len(path)-2):
                    stdin = stdin + "[-1]['folders']"
                eval(stdin+".append(root)")
            placeholder_metadata.append({"name": category["name"], "type": category["type"],
                                         "id": category["id"], "driveId": category["driveId"], "files": tmp_metadata[0]["files"], "folders": tmp_metadata[0]["folders"]})
        elif category["type"] == "tv":
            tmp_metadata = []
            for path, root, dirs, files in driveWalk(category["id"], False, drive):
                root["files"] = files
                root["files"] = [ file for file in files if "video" in file["mimeType"] ]
                root["folders"] = dirs
                stdin = "tmp_metadata"
                for l in range(len(path)-2):
                    stdin = stdin + "[-1]['folders']"
                eval(stdin+".append(root)")
            placeholder_metadata.append({"name": category["name"], "type": category["type"],
                                         "id": category["id"], "driveId": category["driveId"], "files": tmp_metadata[0]["files"], "folders": tmp_metadata[0]["folders"]})

    metadata = placeholder_metadata

    if os.path.exists("./metadata"):
        pass
    else:
        os.mkdir("./metadata")
    with open("./metadata/"+time.strftime("%Y%m%d-%H%M%S")+".json", "w+") as w:
        w.write(json.dumps(metadata))

    return metadata
