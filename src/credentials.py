from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client


def refreshCredentials(access_token, client_id, client_secret, refresh_token, drive):
    credentials = client.GoogleCredentials(
        access_token, client_id, client_secret, refresh_token, None, "https://accounts.google.com/o/oauth2/token", None)
    http = credentials.authorize(Http())
    credentials.refresh(http)
    access_token = credentials.access_token
    if drive == True:
        drive = build("drive", "v3", credentials=credentials)
        return drive, access_token
    else:
        return access_token
