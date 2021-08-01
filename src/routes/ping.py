import datetime

import flask
import flask_cors

pingBP = flask.Blueprint("ping", __name__, url_prefix="/api/v1/ping")
flask_cors.CORS(pingBP)


@pingBP.route("/")
async def pingFunction():
    date = flask.request.args.get("date")
    if date:
        send = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
        receive = datetime.datetime.utcnow()
        diff = receive - send
        return {
            "code": 200,
            "content": {
                "ping": diff.total_seconds(),
                "send_time": send.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "receive_time": receive.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            },
            "message": "You have a one way ping of %s seconds" % (diff.total_seconds()),
        }
    else:
        return (
            {
                "code": 200,
                "content": "Pong",
                "message": "Ping received.",
                "success": True,
            },
            200,
        )
