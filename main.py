import json
import os
from datetime import datetime
from random import randint
from random import seed
from slack import WebClient
from slack.errors import SlackApiError

from base64 import b64encode
from subprocess import run


import requests
from dotenv import load_dotenv

load_dotenv()

# DEPOSIT_BLOCK = {
#         "type": "section",
#         "text": {
#             "type": "mrkdwn",
#             "text": (
#                 "Welcome to Slack! :wave: We're so glad you're here. :blush:\n\n"
#                 "*Get started by completing the steps below:*"
#             ),
#         },
#     }

day_of_year = datetime.today().timetuple().tm_yday
userID = os.getenv("USERID")
token = os.getenv("ACCESSTOKEN")
now = datetime.today()
date = now.strftime("%b-%d-%Y")
clientID = os.getenv("CLIENTID")
clientSecret = os.getenv("CLIENTSECRET")
ownerID = os.getenv("OWNERID")
refreshToken = os.getenv("REFRESHTOKEN")



def b64encodestr(string):
    return b64encode(string.encode("utf-8")).decode()


def refresh_token():
    global refreshToken
    url = "https://api.monzo.com/oauth2/token"

    payload = {'grant_type': 'refresh_token',
               'client_id': 'oauth2client_00009zaxmD668jOqvejEBd',
               'client_secret': f'{clientSecret}',
               'refresh_token': f'{refreshToken}'}
    files = [

    ]
    headers = {
        'Authorization': 'token eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJlYiI6IlBNdFUzcnBYVllQc2N2RVRnOFVNIiwianRpIjoiYWNjdG9rXzAwMDA5emI0aVJzeHVuaUhKWWp0ZFIiLCJ0eXAiOiJhdCIsInYiOiI2In0.o_m6wqMl2IZ-akMEz-6Yd_xtcYg5TRr9mQDqCLJYp-vUtNsIAAM-QjGNWEyhgyNcbU5oOZwixdiQEwIBx8Phbw',
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    response_content = json.loads(response.text)
    print(response_content)
    refreshToken = response_content['refresh_token']
    b64val = b64encodestr(refreshToken)
    cmd = f"""kubectl patch secret njord -p='{{"data":{{"REFRESHTOKEN": "{b64val}"}}}}'"""
    run(cmd, shell=True)

    return response_content['access_token']


access_token = refresh_token()

headers = {"Authorization": f"Bearer {access_token}"}





def send_slack_message(amount):
    client = WebClient(token=os.environ['SLACKTOKEN'])
    try:
        response = client.chat_postMessage(
            channel='#random',
            text=f":pound: £{amount/100} has been deposited")
        assert response["message"]["text"] == f":pound: £{amount/100} has been deposited"
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")


def get_account_id():
    params = {"account_type": "uk_retail_joint"}
    response = requests.get('https://api.monzo.com/accounts', headers=headers, params=params)
    response_content = json.loads(response.text)
    account_id = response_content['accounts'][0]['id']
    return account_id


def get_pots():
    params = {"current_account_id": f"{get_account_id()}"}
    response = requests.get('https://api.monzo.com/pots', headers=headers, params=params)
    response_contents = json.loads(response.text)
    return response_contents['pots']


def get_saving_pot(pot_name):
    for i in get_pots():
        if i['name'] == "Wedding" and i['deleted'] is False:
            return i['id']


def get_balance():
    params = {"account_id": f"{get_account_id()}"}
    response = requests.get('https://api.monzo.com/balance', headers=headers, params=params)
    response_contents = json.loads(response.text)
    return response_contents['balance']


def make_deposit(amount):
    params = {
        "source_account_id": get_account_id(),
        "amount": amount,
        "dedupe_id": randint(1000000, 9999999)
    }
    seed(1)
    response = requests.put(f"https://api.monzo.com/pots/{get_saving_pot('Wedding')}/deposit",
                            headers=headers,
                            data=params)
    return response


def print_balance(balance):
    outfile = open("outputs/balance.txt", "a")
    outfile.write(f"{balance}\n")
    outfile.close()


def total_failed():
    total = 0
    with open('outputs/balance.txt', 'r') as inp:
        for line in inp:
            try:
                num = float(line)
                total += num
            except ValueError:
                print(f"{line} is not a number!")
    print(f"Total unable to be processed: £{total/100}")


def balance_check():
    if get_balance() < day_of_year:
        print("Current balance lower than required")
        print_balance(day_of_year)
        total_failed()
    else:
        print(make_deposit(day_of_year).text)
        print(f"Deposit of £{day_of_year/100} made")
        send_slack_message(day_of_year)
        open(f'outputs/complete-{date}.txt', 'w').close()
        # open('outputs/balance.txt', 'w').close()


def main():
    if os.path.isfile(f"outputs/complete-{date}.txt"):
        print("Script ran today already")
    else:
        balance_check()


if __name__ == "__main__":
    main()

