import time
import logging

LOGGER = logging.getLogger()


def driveIter(root, drive, mimeType):
    params = {
        "pageToken": None,
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
        "fields": "files(id,name,mimeType,parents), incompleteSearch, nextPageToken",
        "q": "'%s' in parents and trashed = false and (mimeType = 'application/vnd.google-apps.folder' or mimeType contains '%s')"
        % (root["id"], mimeType),
        "orderBy": "name",
    }
    while True:
        for n in range(3):
            try:
                response = drive.files().list(**params).execute()
                break
            except Exception as e:
                n += 1
                LOGGER.error(
                    "\033[31mERROR RETRIEVING FILE '%s'! RETRYING %s/%s...\033[0m"
                    % (root["id"], n, 3),
                )
                LOGGER.error(str(e))
                time.sleep(0.5)
        for file in response["files"]:
            if file["mimeType"] == "application/vnd.google-apps.folder":
                file["type"] = "directory"
            else:
                file["type"] = "file"
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
        walk["children"].append(root)
    else:
        return
    return walk


def driveTree(root, drive, mimeType):
    if root.get("mimeType") == "application/vnd.google-apps.folder":
        tree = root
        tree["children"] = [
            driveTree(item, drive, mimeType)
            for item in driveIter(root, drive, mimeType)
        ]
    elif mimeType in root.get("mimeType"):
        tree = root
    else:
        return
    return tree
