import ast
import configparser
import datetime
import os
import random
import string

import google_auth_oauthlib


def readConfig():
    confObj = configparser.ConfigParser()
    confObj.read("config.env")
    config = confObj["CONFIG"]
    access_token = config["access_token"]
    account_list = ast.literal_eval(config["account_list"])
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    category_list = ast.literal_eval(config["category_list"])
    refresh_token = config["refresh_token"]
    secret_key = config["secret_key"]
    tmdb_api_key = config["tmdb_api_key"]
    try:
        token_expiry = datetime.datetime.strptime(
            config["token_expiry"], "%Y-%m-%d %H:%M:%S.%f")
    except:
        token_expiry = datetime.datetime.utcnow()
    return access_token, account_list, category_list, client_id, client_secret, refresh_token, secret_key, tmdb_api_key, token_expiry


def updateConfig(environment):
    confObj = configparser.ConfigParser()
    confObj["CONFIG"] = environment

    with open("config.env", "w+") as w:
        confObj.write(w)
