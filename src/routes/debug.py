import io
import os
import zipfile

import flask
import src.config

debugBP = flask.Blueprint("debug", __name__)


@debugBP.route("/api/v1/debug/<path:req_path>")
async def debugFunction(req_path):
    secret = flask.request.args.get("secret")  # SECRET
    config = src.config.readConfig()

    if secret == config.get("secret_key"):
        req_path = "./" + req_path
        if os.path.exists(req_path):
            if os.path.isdir(req_path):
                fileName = "%s.zip" % (os.path.basename(os.path.realpath(req_path)))
                memory_file = io.BytesIO()
                with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(req_path):
                        for file in files:
                            zipf.write(os.path.join(root, file))
                memory_file.seek(0)
                return flask.send_file(
                    memory_file, attachment_filename=fileName, as_attachment=True
                )
            elif os.path.isfile(req_path):
                return flask.send_file(req_path, as_attachment=True)
        return (
            flask.jsonify(
                {
                    "code": 404,
                    "message": "The file/folder doesn't exist.",
                    "success": False,
                }
            ),
            200,
        )
    else:
        return (
            flask.jsonify(
                {
                    "code": 401,
                    "message": "The secret key provided was incorrect.",
                    "success": False,
                }
            ),
            401,
        )
