import datetime
import json
import mimetypes
import os
import re
import stat

import flask
import flask.views
import humanize
import pathlib2
import src.functions.config
import werkzeug.utils

debugBP = flask.Blueprint("debug", __name__)

root = os.getcwd()

config = src.functions.config.readConfig()

ignored = [
    ".bzr",
    "$RECYCLE.BIN",
    ".DAV",
    ".DS_Store",
    ".git",
    ".hg",
    ".htaccess",
    ".htpasswd",
    ".Spotlight-V100",
    ".svn",
    "__MACOSX",
    "ehthumbs.db",
    "robots.txt",
    "Thumbs.db",
    "thumbs.tps",
]
datatypes = {
    "audio": "m4a,mp3,oga,ogg,webma,wav",
    "archive": "7z,zip,rar,gz,tar",
    "image": "gif,ico,jpe,jpeg,jpg,png,svg,webp",
    "pdf": "pdf",
    "quicktime": "3g2,3gp,3gp2,3gpp,mov,qt",
    "source": "atom,bat,bash,c,cmd,coffee,css,hml,js,json,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml,plist,log,conf,env",
    "text": "txt",
    "video": "mp4,m4v,ogv,webm",
    "website": "htm,html,mhtm,mhtml,xhtm,xhtml",
}
icontypes = {
    "fa-music": "m4a,mp3,oga,ogg,webma,wav",
    "fa-archive": "7z,zip,rar,gz,tar",
    "fa-picture-o": "gif,ico,jpe,jpeg,jpg,png,svg,webp",
    "fa-file-text": "pdf",
    "fa-film": "3g2,3gp,3gp2,3gpp,mov,qt",
    "fa-code": "atom,plist,bat,bash,c,cmd,coffee,css,hml,js,json,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml",
    "fa-file-text-o": "txt",
    "fa-film": "mp4,m4v,ogv,webm",
    "fa-globe": "htm,html,mhtm,mhtml,xhtm,xhtml",
}


@debugBP.app_template_filter("size_fmt")
def size_fmt(size):
    return humanize.naturalsize(size)


@debugBP.app_template_filter("time_fmt")
def time_desc(timestamp):
    mdate = datetime.datetime.fromtimestamp(timestamp)
    str = mdate.strftime("%Y-%m-%d %H:%M:%S")
    return str


@debugBP.app_template_filter("data_fmt")
def data_fmt(filename):
    t = "unknown"
    for type, exts in datatypes.items():
        if filename.split(".")[-1] in exts:
            t = type
    return t


@debugBP.app_template_filter("icon_fmt")
def icon_fmt(filename):
    i = "fa-file-o"
    for icon, exts in icontypes.items():
        if filename.split(".")[-1] in exts:
            i = icon
    return i


@debugBP.app_template_filter("humanize")
def time_humanize(timestamp):
    mdate = datetime.datetime.utcfromtimestamp(timestamp)
    return humanize.naturaltime(mdate)


def get_type(mode):
    if stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        type = "dir"
    else:
        type = "file"
    return type


def partial_response(path, start, end=None):
    file_size = os.path.getsize(path)

    if end is None:
        end = file_size - start - 1
    end = min(end, file_size - 1)
    length = end - start + 1

    with open(path, "rb") as fd:
        fd.seek(start)
        bytes = fd.read(length)
    assert len(bytes) == length

    response = flask.Response(
        bytes,
        206,
        mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True,
    )
    response.headers.add(
        "Content-Range",
        "bytes {0}-{1}/{2}".format(
            start,
            end,
            file_size,
        ),
    )
    response.headers.add("Accept-Ranges", "bytes")
    return response


def get_range(request):
    range = request.headers.get("Range")
    m = re.match("bytes=(?P<start>\d+)-(?P<end>\d+)?", range)
    if m:
        start = m.group("start")
        end = m.group("end")
        start = int(start)
        if end is not None:
            end = int(end)
        return start, end
    else:
        return 0, None


class PathView(flask.views.MethodView):
    def get(self, p=""):
        if flask.request.args.get("secret") == config.get("secret_key"):
            hide_dotfile = flask.request.args.get(
                "hide-dotfile", flask.request.cookies.get("hide-dotfile", "no")
            )

            path = os.path.join(root, p)

            if os.path.isdir(path):
                contents = []
                total = {"size": 0, "dir": 0, "file": 0}
                for filename in os.listdir(path):
                    if filename in ignored:
                        continue
                    if hide_dotfile == "yes" and filename[0] == ".":
                        continue
                    filepath = os.path.join(path, filename)
                    relativepath = os.path.join(p, filename)
                    stat_res = os.stat(filepath)
                    info = {}
                    info["name"] = filename
                    info["path"] = relativepath
                    info["mtime"] = stat_res.st_mtime
                    ft = get_type(stat_res.st_mode)
                    info["type"] = ft
                    total[ft] += 1
                    sz = stat_res.st_size
                    info["size"] = sz
                    total["size"] += sz
                    contents.append(info)
                page = flask.render_template(
                    "browser.html",
                    path=p,
                    secret=flask.request.args.get("secret"),
                    contents=contents,
                    total=total,
                    hide_dotfile=hide_dotfile,
                )
                res = flask.make_response(page, 200)
                res.set_cookie("hide-dotfile", hide_dotfile, max_age=16070400)
            elif os.path.isfile(path):
                if "Range" in flask.request.headers:
                    start, end = get_range(flask.request)
                    res = partial_response(path, start, end)
                else:
                    res = flask.send_file(path)
            else:
                res = flask.make_response("Not found", 404)
            return res
        else:
            return "The secret key provided was incorrect. You do not have permission to access this page."

    def put(self, p=""):
        if flask.request.args.get("secret") == config.get("secret_key"):
            path = os.path.join(root, p)
            dir_path = os.path.dirname(path)
            pathlib2.Path(dir_path).mkdir(parents=True, exist_ok=True)

            info = {}
            if os.path.isdir(dir_path):
                try:
                    filename = werkzeug.utils.secure_filename(os.path.basename(path))
                    with open(os.path.join(dir_path, filename), "wb") as f:
                        f.write(flask.request.stream.read())
                except Exception as e:
                    info["status"] = "error"
                    info["msg"] = str(e)
                else:
                    info["status"] = "success"
                    info["msg"] = "File Saved"
            else:
                info["status"] = "error"
                info["msg"] = "Invalid Operation"
            res = flask.make_response(json.JSONEncoder().encode(info), 201)
            res.headers.add("Content-type", "application/json")
            return res
        else:
            return "The secret key provided was incorrect. You do not have permission to access this page."

    def post(self, p=""):
        if flask.request.args.get("secret") == config.get("secret_key"):
            path = os.path.join(root, p)
            pathlib2.Path(path).mkdir(parents=True, exist_ok=True)

            info = {}
            if os.path.isdir(path):
                files = flask.request.files.getlist("files[]")
                for file in files:
                    try:
                        filename = werkzeug.utils.secure_filename(file.filename)
                        file.save(os.path.join(path, filename))
                    except Exception as e:
                        info["status"] = "error"
                        info["msg"] = str(e)
                    else:
                        info["status"] = "success"
                        info["msg"] = "File Saved"
            else:
                info["status"] = "error"
                info["msg"] = "Invalid Operation"
            res = flask.make_response(json.JSONEncoder().encode(info), 200)
            res.headers.add("Content-type", "application/json")
            return res
        else:
            return "The secret key provided was incorrect. You do not have permission to access this page."

    def delete(self, p=""):
        if flask.request.args.get("secret") == config.get("secret_key"):
            path = os.path.join(root, p)
            dir_path = os.path.dirname(path)
            pathlib2.Path(dir_path).mkdir(parents=True, exist_ok=True)

            info = {}
            if os.path.isdir(dir_path):
                try:
                    filename = werkzeug.utils.secure_filename(os.path.basename(path))
                    os.remove(os.path.join(dir_path, filename))
                    os.rmdir(dir_path)
                except Exception as e:
                    info["status"] = "error"
                    info["msg"] = str(e)
                else:
                    info["status"] = "success"
                    info["msg"] = "File Deleted"
            else:
                info["status"] = "error"
                info["msg"] = "Invalid Operation"
            res = flask.make_response(json.JSONEncoder().encode(info), 204)
            res.headers.add("Content-type", "application/json")
            return res
        else:
            return "The secret key provided was incorrect. You do not have permission to access this page."


path_view = PathView.as_view("path_view")
debugBP.add_url_rule("/api/v1/debug/", view_func=path_view)
debugBP.add_url_rule("/api/v1/debug/<path:p>", view_func=path_view)
