import io
import re

import flask
import src.functions.config
from PIL import Image, ImageDraw, ImageFont

imageBP = flask.Blueprint("image", __name__)


@imageBP.route("/api/v1/image/<image_type>")
async def imageFunction(image_type):
    text = flask.request.args.get("text")  # TEXT
    extention = flask.request.args.get("extention")  # EXTENTION
    if image_type == "poster":
        img = Image.new("RGB", (342, 513), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_size = 1
        font = ImageFont.truetype(
            font="./build/fonts/Roboto-Regular.ttf", size=font_size
        )
        img_fraction = 0.9
        breakpoint = img_fraction * img.size[0]
        jumpsize = 75
        while True:
            if font.getsize(text)[0] < breakpoint:
                font_size += jumpsize
            else:
                jumpsize = jumpsize // 2
                font_size -= jumpsize
            font = ImageFont.truetype(
                font="./build/fonts/Roboto-Regular.ttf", size=font_size
            )
            if jumpsize <= 1:
                break

        width, height = draw.textsize(text, font=font)
        draw.text(
            ((342 - width) / 2, (513 - height) / 2), text, fill="black", font=font
        )
        output = io.BytesIO()
        img.save(output, format=extention)
        output.seek(0, 0)
        return flask.send_file(
            output, mimetype="image/%s" % (extention), as_attachment=False
        )
    elif image_type == "backdrop":
        img = Image.new("RGB", (1280, 720), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_size = 1
        font = ImageFont.truetype(
            font="./build/fonts/Roboto-Regular.ttf", size=font_size
        )
        img_fraction = 0.9
        breakpoint = img_fraction * img.size[0]
        jumpsize = 75
        while True:
            if font.getsize(text)[0] < breakpoint:
                font_size += jumpsize
            else:
                jumpsize = jumpsize // 2
                font_size -= jumpsize
            font = ImageFont.truetype(
                font="./build/fonts/Roboto-Regular.ttf", size=font_size
            )
            if jumpsize <= 1:
                break

        width, height = draw.textsize(text, font=font)
        draw.text(
            ((1280 - width) / 2, (720 - height) / 2), text, fill="black", font=font
        )
        output = io.BytesIO()
        img.save(output, format=extention)
        output.seek(0, 0)
        return flask.send_file(
            output, mimetype="image/%s" % (extention), as_attachment=False
        )
    elif image_type == "thumbnail":
        id = flask.request.args.get("id")
        config, drive = src.functions.credentials.refreshCredentials(
            src.functions.config.readConfig()
        )
        params = {
            "fileId": id,
            "fields": "thumbnailLink",
            "supportsAllDrives": True,
        }
        res = drive.files().get(**params).execute()
        if res.get("thumbnailLink"):
            thumbnail = re.sub(r"(s[^s]*)$", "s3840", res["thumbnailLink"])
            return flask.redirect(thumbnail, code=302)
        else:
            return (
                flask.jsonify(
                    {
                        "code": 500,
                        "content": None,
                        "message": "The thumbnail does not exist on Google's servers.",
                        "success": False,
                    }
                ),
                500,
            )
