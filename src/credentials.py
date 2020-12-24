import configparser

import googleapiclient.discovery
import httplib2
import oauth2client


def refreshCredentials(access_token, client_id, client_secret, refresh_token):
    credentials = oauth2client.client.GoogleCredentials(
        access_token, client_id, client_secret, refresh_token, None, "https://accounts.google.com/o/oauth2/token", None)
    http = credentials.authorize(httplib2.Http())
    credentials.refresh(http)
    access_token = credentials.access_token
    token_expiry = credentials.token_expiry
    drive = googleapiclient.discovery.build(
        "drive", "v3", credentials=credentials)
    
    confObj = configparser.ConfigParser()
    confObj.read("config.env")
    confObj["CONFIG"]["access_token"] = str(access_token)
    confObj["CONFIG"]["token_expiry"] = str(token_expiry)
    with open("config.env", "w+") as w:
        confObj.write(w)
    return access_token, drive, token_expiry
