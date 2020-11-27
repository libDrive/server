def driveWalk(top, by_name, drive):
    def iterfiles(name, is_folder, parent, order_by, drive):
        q = []
        if name is not None:
            q.append("name = '%s'" % name.replace("'", "\\'"))
        if is_folder is not None:
            q.append("mimeType %s '%s'" % ('=' if is_folder else '!=',
                                           'application/vnd.google-apps.folder'))
        if parent is not None:
            q.append("'%s' in parents" % parent.replace("'", "\\'"))
        params = {'pageToken': None, 'orderBy': order_by, "supportsAllDrives": True, "includeItemsFromAllDrives": True,
                  "fields": "files(id,name,mimeType,parents,fullFileExtension)"}
        if q:
            params['q'] = ' and '.join(q)
        while True:
            response = drive.files().list(**params).execute()
            for f in response['files']:
                yield f
            try:
                params['pageToken'] = response['nextPageToken']
            except KeyError:
                return
    if by_name:
        top, = iterfiles(top, True, None, 'folder,name,createdTime', drive)
    else:
        top = drive.files().get(fileId=top, supportsAllDrives=True).execute()
        if top['mimeType'] != 'application/vnd.google-apps.folder':
            raise ValueError('not a folder: %r' % top)
    stack = [((top['name'],), top)]
    while stack:
        path, top = stack.pop()
        dirs, files = is_file = [], []
        for f in iterfiles(None, None, top['id'], 'folder,name,createdTime', drive):
            is_file[f['mimeType'] !=
                    'application/vnd.google-apps.folder'].append(f)
        yield path, top, dirs, files
        if dirs:
            stack.extend((path + (d['name'],), d) for d in reversed(dirs))
