import json
import requests
import time
import os
from slacker import Slacker

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
HAR_EMAIL = os.environ["HAR_EMAIL"]
HAR_PASS = os.environ["HAR_PASS"]

slack = Slacker(token=None,incoming_webhook_url=SLACK_WEBHOOK)

class NoSessionIdException(Exception): pass

sign_in_url = "https://app.harmoney.com/accounts/sign_in"
loans_url = "https://app.harmoney.com/api/v1/investor/marketplace/loans"
loans_querystring = {"limit":"100","offset":"0"}

sign_in_payload = '{"branch": "NZ", "account": { "email": "'+HAR_EMAIL+'", "password": "'+HAR_PASS+'" }}'
sign_in_headers = {
    "Host": "app.harmoney.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0",
    "Accept": "application/json",
    "Accept-Language": "en-NZ,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.harmoney.co.nz/sign-in",
    "content-type": "application/json",
    "Origin": "https://www.harmoney.co.nz",
    "DNT": "1",
    "Connection": "keep-alive"
    }

def lambda_handler(event, context):
    response = requests.request("POST", sign_in_url, data=sign_in_payload, headers=sign_in_headers)

    session_id = None
    for cookie in response.cookies:
        if cookie.name == "_harmoney_session_id":
            session_id = cookie.value
    if session_id is None:
        raise NoSessionIdException("There's no session_id in the cookie")

    loans_cookie = "_harmoney_session_id="+session_id
    loans_headers = {"Cookie": loans_cookie}
    response = requests.request("GET", loans_url, params=loans_querystring, headers=loans_headers)

    loans = json.loads(response.text)
    loans_to_invest = None
    if "total_count" in loans and loans["total_count"]>0:
        loans_to_invest = sum(loan["already_invested_amount"] != 0 for loan in loans["items"])

    slack_message = """
{} Loan(s) to invest!
https://www.harmoney.co.nz/lender/portal/invest/marketplace/browse"
""".format(loans_to_invest)

    if loans_to_invest is not None:
        slack.incomingwebhook.post({"text": slack_message})

    print(response.text)
    return {
        "statusCode": 200,
        "body": response.text
    }

if __name__ == "__main__":
    event = {}
    context = {}
    print(lambda_handler(event, context))