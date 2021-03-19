def driveIter(root, drive, mimeType):
    params = {
        "pageToken": None,
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
        "fields": "files(id,name,mimeType), incompleteSearch, nextPageToken",
        "q": "'%s' in parents and trashed = false and (mimeType = 'application/vnd.google-apps.folder' or mimeType contains '%s')"
        % (root["id"], mimeType),
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


def driveWalk(root, drive, walk, mimeType):
    if root.get("mimeType") == "application/vnd.google-apps.folder":
        for item in driveIter(root, drive, mimeType):
            driveWalk(item, drive, walk, mimeType)
    elif mimeType in root.get("mimeType"):
        root["type"] = "file"
        walk["children"].append(root)
    else:
        return
    return walk


def driveTree(root, drive, mimeType):
    if root.get("mimeType") == "application/vnd.google-apps.folder":
        tree = root
        tree["type"] = "directory"
        tree["children"] = [driveTree(item, drive, mimeType) for item in driveIter(root, drive, mimeType)]
    elif mimeType in root.get("mimeType"):
        tree = root
        tree["type"] = "file"
    else:
        return
    return tree
