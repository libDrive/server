def driveWalk(root, tree1, tree2, drive):
    def iterDrive(root, drive):
        params = {"pageToken": None, "supportsAllDrives": True, "includeItemsFromAllDrives": True,
                  "fields": "files(id,name,mimeType), incompleteSearch, nextPageToken", "q": "'%s' in parents and trashed = false and (mimeType = 'application/vnd.google-apps.folder' or mimeType contains 'video')" % (root["id"]), "orderBy": "name"}
        while True:
            response = drive.files().list(**params).execute()
            for file in response["files"]:
                yield file
            try:
                params["pageToken"] = response["nextPageToken"]
            except KeyError:
                return
    if root["mimeType"] == "application/vnd.google-apps.folder":
        for item in iterDrive(root, drive):
            tree1["children"].append(item)
            tree2.append(driveWalk(item, tree1, tree2, drive))
    elif "video" in root["mimeType"]:
        tree = root
        tree["type"] = "file"
    else:
        return

    return tree1
