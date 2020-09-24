import json
import os
from datetime import datetime
from random import randint
from random import seed

import requests
from dotenv import load_dotenv

load_dotenv()

day_of_year = datetime.today().timetuple().tm_yday
userID = os.getenv("USERID")
token = os.getenv("ACCESSTOKEN")
headers = {"Authorization": f"Bearer {token}"}
seed(1)


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


def get_saving_pot():
    for i in get_pots():
        if i['name'] == 'Wedding' and i['deleted'] == False:
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
    response = requests.put(f"https://api.monzo.com/pots/{get_saving_pot()}/deposit", headers=headers, data=params)
    return response.text


def balance_check():
    if get_balance() < day_of_year:
        print("Current balance lower than required")
    else:
        print(make_deposit(day_of_year))


balance_check()
