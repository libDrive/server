def driveIter(root, drive):
    params = {
        "pageToken": None,
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
        "fields": "files(id,name,mimeType), incompleteSearch, nextPageToken",
        "q": "'%s' in parents and trashed = false and (mimeType = 'application/vnd.google-apps.folder' or mimeType contains 'video')"
        % (root["id"]),
        "orderBy": "name",
    }
    while True:
        response = drive.files().list(**params).execute()
        for file in response["files"]:
            yield file
        try:
            params["pageToken"] = response["nextPageToken"]
        except KeyError:
            return


def driveWalk(root, drive, walk):
    if root["mimeType"] == "application/vnd.google-apps.folder":
        for item in driveIter(root, drive):
            driveWalk(item, drive, walk)
    elif "video" in root["mimeType"]:
        root["type"] = "file"
        walk["children"].append(root)
    else:
        return
    return walk


def driveTree(root, drive):
    if root["mimeType"] == "application/vnd.google-apps.folder":
        tree = root
        tree["type"] = "directory"
        tree["children"] = [driveTree(item, drive) for item in driveIter(root, drive)]
    elif "video" in root["mimeType"]:
        tree = root
        tree["type"] = "file"
    else:
        return
    return tree
