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
        open('outputs/complete.txt', 'w').close()
        # open('outputs/balance.txt', 'w').close()

if os.path.isfile('outputs/complete.txt'):
    print("Script ran today already")
    balance_check()
