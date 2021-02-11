import datetime
import json


def readConfig():
    with open("config.json") as r:
        config = json.load(r)
    try:
        datetime.datetime.strptime(config["token_expiry"], "%Y-%m-%d %H:%M:%S.%f")
    except:
        config["token_expiry"] = str(datetime.datetime.utcnow())
    return config


def updateConfig(config):
    with open("config.json", "w+") as w:
        json.dump(config, w)
