import json
import logging
import locale
import os
import random
import string
from datetime import datetime
from slack import WebClient
from slack.errors import SlackApiError

from base64 import b64encode
from subprocess import run


import requests
from dotenv import load_dotenv

locale.setlocale( locale.LC_ALL, 'en_GB.UTF-8')

load_dotenv("./.env")

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%d-%m-%Y-%H:%M:%S', level=logging.INFO)

day_of_year = datetime.today().timetuple().tm_yday

userID = os.getenv("USERID")
token = os.getenv("ACCESSTOKEN")
now = datetime.today()
date = now.strftime("%b-%d-%Y")
clientID = os.getenv("CLIENTID")
clientSecret = os.getenv("CLIENTSECRET")
ownerID = os.getenv("OWNERID")
refreshToken = os.getenv("REFRESHTOKEN")
accessToken = os.getenv("ACCESSTOKEN")


def send_slack_message(amount):
    client = WebClient(token=os.environ['SLACKTOKEN'])
    deposit_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f":pound: {locale.currency(amount/100)} has been deposited"
            ,
        },
    }
    try:
        response = client.chat_postMessage(
            channel='#random',
            text= "Deposit Made",
            blocks=[deposit_block]
        )
        assert response["message"]["blocks"][0]["text"]["text"] == f":pound: " \
                                                                   f"{locale.currency(amount/100)} has been deposited"
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        logging.error(f"Got an error: {e.response['error']}")

def b64encodestr(key):
    return b64encode(key.encode("utf-8")).decode()


def refresh_token():
    global refreshToken
    url = "https://api.monzo.com/oauth2/token"

    payload = {'grant_type': 'refresh_token',
               'client_id': 'oauth2client_00009zaxmD668jOqvejEBd',
               'client_secret': f'{clientSecret}',
               'refresh_token': f'{refreshToken}'}
    files = [

    ]
    authheader = {
        'Authorization': f'token {accessToken}',
    }
    response = requests.request("POST", url, headers=authheader, data=payload, files=files)
    logging.info(f"{response.status_code}-{response.text}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(logging.error(e))
    response_content = json.loads(response.text)
    refreshToken = response_content['refresh_token']
    b64valrefresh = b64encodestr(refreshToken)
    b64valaccess = b64encodestr(response_content['access_token'])
    cmd = f"""kubectl patch secret njord -p='{{"data":{{"REFRESHTOKEN": "{b64valrefresh}"}}}}'"""
    cmd2 = f"""kubectl patch secret njord -p='{{"data":{{"ACCESSTOKEN": "{b64valaccess}"}}}}'"""
    run(cmd, shell=True)
    run(cmd2, shell=True)
    return response_content['access_token']


access_token = refresh_token()

headers = {"Authorization": f"Bearer {access_token}"}


def get_account_id():
    params = {"account_type": "uk_retail_joint"}
    response = requests.get('https://api.monzo.com/accounts', headers=headers, params=params)
    logging.info(f"{response.status_code}-{response.text}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(logging.error(e))
    response_content = json.loads(response.text)
    account_id = response_content['accounts'][0]['id']
    return account_id


def get_pots():
    params = {"current_account_id": f"{get_account_id()}"}
    response = requests.get('https://api.monzo.com/pots', headers=headers, params=params)
    logging.info(f"{response.status_code}-{response.text}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(logging.error(e))
    response_contents = json.loads(response.text)
    return response_contents['pots']


def get_saving_pot(pot_name):
    for i in get_pots():
        if i['name'] == "Wedding" and i['deleted'] is False:
            return i['id']


def get_balance():
    params = {"account_id": f"{get_account_id()}"}
    response = requests.get('https://api.monzo.com/balance', headers=headers, params=params)
    logging.info(f"{response.status_code}-{response.text}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(logging.error(e))
    response_contents = json.loads(response.text)
    return response_contents['balance']


def make_deposit(amount):
    params = {
        "source_account_id": get_account_id(),
        "amount": amount,
        "dedupe_id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=25))
    }
    response = requests.put(f"https://api.monzo.com/pots/{get_saving_pot('Wedding')}/deposit",
                            headers=headers,
                            data=params)
    logging.info(f"requesting-{response.request.body}")
    logging.info(f"{response.status_code}-{response.text}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise SystemExit(logging.error(e))
    return response


def print_balance(balance):
    outfile = open("outputs/balance.txt", "a")
    outfile.write(f"{balance}\n")
    outfile.close()


def total_failed():
    total = 0
    try:
        with open('outputs/balance.txt', 'r') as inp:
            for line in inp:
                try:
                    num = float(line)
                    total += num
                except ValueError:
                    print(f"{line} is not a number!")
    except FileNotFoundError as fnf_error:
        raise SystemExit(logging.error(fnf_error))

    logging.error(f"Total unable to be processed: £{locale.currency(total/100)}")


def balance_check():
    if get_balance() < day_of_year:
        logging.warning("Current balance lower than required")
        print_balance(day_of_year)
        total_failed()
    else:
        logging.info(make_deposit(day_of_year).text)
        logging.info(f"Deposit of £{locale.currency(day_of_year/100)} made")
        send_slack_message(day_of_year)
        open(f'outputs/complete-{date}.txt', 'w').close()


def main():
    if os.path.isfile(f"outputs/complete-{date}.txt"):
        logging.warning("Script ran today already")
    else:
        balance_check()


if __name__ == "__main__":
    main()

