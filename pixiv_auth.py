import time
import json
import re
import requests

from argparse import ArgumentParser
from base64 import urlsafe_b64encode
from hashlib import sha256
from pprint import pprint
from secrets import token_urlsafe
from sys import exit
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from seleniumwire import webdriver as wired_webdriver
import pickle

# Latest app version can be found using GET /v1/application-info/android
USER_AGENT = "PixivIOSApp/7.13.3 (iOS 14.6; iPhone13,2)"
REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
LOGIN_URL = "https://app-api.pixiv.net/web/v1/login"
AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"
REQUESTS_KWARGS = {
    # 'proxies': {
    #     'https': 'http://127.0.0.1:1087',
    # },
    # 'verify': False
}

def wait_for(browser,locator):
    return WebDriverWait(browser, 10).until(EC.presence_of_element_located((locator)))

def s256(data):
    """S256 transformation method."""

    return urlsafe_b64encode(sha256(data).digest()).rstrip(b"=").decode("ascii")


def oauth_pkce(transform):
    """Proof Key for Code Exchange by OAuth Public Clients (RFC7636)."""

    code_verifier = token_urlsafe(32)
    code_challenge = transform(code_verifier.encode("ascii"))

    return code_verifier, code_challenge


def print_auth_token_response(response):
    data = response.json()

    try:
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
    except KeyError:
        print("error:")
        pprint(data)
        exit(1)

    print("access_token:", access_token)
    print("refresh_token:", refresh_token)
    print("expires_in:", data.get("expires_in", 0))


def login():
    caps = DesiredCapabilities.CHROME.copy()
    caps["goog:loggingPrefs"] = {"performance": "ALL"}  # enable performance logs
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.headless = True
    driver = wired_webdriver.Chrome(service=Service(ChromeDriverManager().install()), desired_capabilities=caps,options=options)
    
    code_verifier, code_challenge = oauth_pkce(s256)
    login_params = {
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "client": "pixiv-android",
    }

    PIXIV_ID = input("Enter Your Pixiv Email or Id : ")
    PIXIV_PASSWORD = input("Enter Your Pixiv Password : ")
    print("Checking...")
    driver.get(f"{LOGIN_URL}?{urlencode(login_params)}")

    try:
        try:
            banner = wait_for(driver,(By.ID, "js-privacy-policy-banner"))
            driver.execute_script("""
            const banner = arguments[0];
            banner.parentElement.removeChild(banner);
            """, banner)
        except:
            pass
        pixiv_id = wait_for(driver,
            (By.CLASS_NAME, "degQSE"))
        pixiv_password = wait_for(driver,
            (By.CLASS_NAME, "hfoSmp"))
        pixiv_login_button = wait_for(driver,
            (By.CLASS_NAME, "pKCsX"))
        pixiv_id.send_keys(PIXIV_ID)
        pixiv_password.send_keys(PIXIV_PASSWORD)
        pixiv_login_button.click()
    except:
        print("Cannot find login page.")

    while True:
        # wait for login
        if driver.current_url[:40] == "https://accounts.pixiv.net/post-redirect":
            break
        time.sleep(1)

    code = None

    # filter code url from performance logs
    print("FINDING CODE AND USER ID...")
    for request in driver.requests:
        if request.response:
            if "callback?" in request.url:
                code = re.search(r'code=([^&]*)', request.response.headers["location"]).groups()[0]
    print("CODE:", code)
    driver.close()


    response = requests.post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "include_policy": "true",
            "redirect_uri": REDIRECT_URI,
        },
        headers={
            "user-agent": USER_AGENT,
            "app-os-version": "14.6",
            "app-os": "ios",
        },
        **REQUESTS_KWARGS
    )
    return response


def refresh(refresh_token):
    response = requests.post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "include_policy": "true",
            "refresh_token": refresh_token,
        },
        headers={
            "user-agent": USER_AGENT,
            "app-os-version": "14.6",
            "app-os": "ios",
        },
        **REQUESTS_KWARGS
    )
    return response


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    parser.set_defaults(func=lambda _: parser.print_usage())
    login_parser = subparsers.add_parser("login")
    login_parser.set_defaults(func=lambda _: login())
    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("refresh_token")
    refresh_parser.set_defaults(func=lambda ns: refresh(ns.refresh_token))
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()