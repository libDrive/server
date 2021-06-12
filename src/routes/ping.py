import datetime

import flask

pingBP = flask.Blueprint("ping", __name__)


@pingBP.route("/api/v1/ping")
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
