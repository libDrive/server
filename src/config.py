import ast
import configparser
import os
import random
import string

import google_auth_oauthlib


def readConfig():
    if os.path.exists("config.env"):
        confObj = configparser.ConfigParser()
        confObj.read("config.env")
        config = confObj["CONFIG"]
        account_list = ast.literal_eval(config["account_list"])
        client_id = config["client_id"]
        client_secret = config["client_secret"]
        category_list = ast.literal_eval(config["category_list"])
        refresh_token = config["refresh_token"]
        secret_key = config["secret_key"]
        tmdb_api_key = config["tmdb_api_key"]
        return account_list, client_id, client_secret, category_list, refresh_token, secret_key, tmdb_api_key, config
    else:
        return None


def writeConfig():
    confObj = configparser.ConfigParser()
    confObj["CONFIG"] = {}

    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            "credentials.json", ["https://www.googleapis.com/auth/drive"])
    except:
        raise FileNotFoundError(
            "There is no 'credentials.json' file in the current directory.")
    credentials = flow.run_local_server()

    account_list = []
    n = 1
    while True:
        stop = ""
        username = input("\nEnter the username for accont "+str(n)+":\n")
        password = input("\nEnter the password for account "+str(n)+":\n")
        auth = "".join(random.choice(string.ascii_letters) for i in range(32))
        account_list.append(
            {"username": username, "password": password, "auth": auth, "pic": ""})
        n = n + 1
        while stop not in ["y", "n"]:
            stop = input(
                "\n- Would you like to add another account? - (y/n):\n")
        if stop == "n":
            break

    category_list = []
    n = 1
    while True:
        stop = ""
        folder_name = input("\nEnter a custom name for folder "+str(n)+":\n")
        folder_choice = 0
        folder_type = ""
        while folder_choice not in [1, 2, 3]:
            folder_choice = int(input("\nChoose a type for folder " +
                                      str(n)+":\n"+"(1) Movies\n(2) TV Shows\n(3) Other\n"))
            if folder_choice == 1:
                folder_type = "movies"
            elif folder_choice == 2:
                folder_type = "tv"
            elif folder_choice == 3:
                folder_type = "other"
        folder_id = input(
            "\nEnter the Google Drive folder ID for folder "+str(n)+":\n")
        drive_id = input(
            "\nEnter the Google Drive Shared Drive ID for folder "+str(n)+":\n")
        category_list.append({"name": folder_name, "type": folder_type,
                              "id": folder_id, "driveId": drive_id})
        while stop not in ["y", "n"]:
            stop = input(
                "\n- Would you like to add another folder? - (y/n):\n")
        if stop == "n":
            break

    tmdb_api_key = input("\nEnter your TMDB API key:\n")

    secret_key = input("\nEnter a secret key:\n")

    confObj["CONFIG"]["access_token"] = str(credentials.token)
    confObj["CONFIG"]["account_list"] = str(account_list)
    confObj["CONFIG"]["client_id"] = str(credentials.client_id)
    confObj["CONFIG"]["client_secret"] = str(credentials.client_secret)
    confObj["CONFIG"]["refresh_token"] = str(credentials.refresh_token)
    confObj["CONFIG"]["category_list"] = str(category_list)
    confObj["CONFIG"]["secret_key"] = str(secret_key)
    confObj["CONFIG"]["tmdb_api_key"] = str(tmdb_api_key)
    with open("config.env", "w+") as w:
        confObj.write(w)

def updateConfig(access_token, account_list, client_id, client_secret, refresh_token, category_list, secret_key, tmdb_api_key):
    confObj = configparser.ConfigParser()
    confObj["CONFIG"] = {}
    
    confObj["CONFIG"]["access_token"] = str(access_token)
    confObj["CONFIG"]["account_list"] = str(account_list)
    confObj["CONFIG"]["client_id"] = str(client_id)
    confObj["CONFIG"]["client_secret"] = str(client_secret)
    confObj["CONFIG"]["refresh_token"] = str(refresh_token)
    confObj["CONFIG"]["category_list"] = str(category_list)
    confObj["CONFIG"]["secret_key"] = str(secret_key)
    confObj["CONFIG"]["tmdb_api_key"] = str(tmdb_api_key)

    with open("config.env", "w") as w:
        confObj.write(w)
