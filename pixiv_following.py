from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from pixivpy3 import *
from math import ceil
import chromedriver_autoinstaller
import os
import sys
import pickle

path = chromedriver_autoinstaller.install()

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--ignore-certificate-errors")
options.headless = True
browser = webdriver.Chrome(path, options=options)

api = AppPixivAPI()

LINK = "https://www.pixiv.net"

following_users = {}

artworks = {}

following_id = "11"

base = ""
try:
    syscheck = sys._MEIPASS
    base = os.path.abspath(os.path.join("..", ".."))
except Exception:
    base = os.path.abspath(".")
base_path = os.path.join(base, "pixiv_image")


def unique_str(str):
    str = str.replace("\\", "＼")
    str = str.replace("/", "／")
    str = str.replace(":", "：")
    str = str.replace("*", "＊")
    str = str.replace("?", "？")
    str = str.replace("\"", "＂")
    str = str.replace("<", "＜")
    str = str.replace(">", "＞")
    str = str.replace("|", "｜")
    return str


def wait_for(locator):
    return WebDriverWait(browser, 5).until(EC.presence_of_element_located((locator)))


def get_following_users(user_id):
    following_url = f"{LINK}/users/{user_id}/following"
    browser.get(following_url)
    user_number = 0
    try:
        user_number = wait_for(
            (By.XPATH, "/html/body/div[1]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div/section/div[1]/div/div/div/div/span")).text
    except Exception:
        print("Cannot load following page.")
        return
    n = ceil(int(user_number) / 24)
    if n == 0:
        return
    for i in range(n):
        print(f"Getting following page: {i+1} of {n}...")
        browser.get(f"{following_url}?p={i+1}")
        wait_for(
            (By.XPATH, "/html/body/div[1]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div/section/div[1]/div/div/div/div/span"))
        bs = BeautifulSoup(browser.page_source, "lxml")
        box_list = bs.find_all("div", {"class": "sc-1y4z60g-6 itSEaW"})
        if (not box_list):
            break
        for box in box_list:
            artist_id = (box.find("a")["data-gtm-value"])
            following_users[artist_id] = box.find(
                "a", {"class": "bfyjep"}).text


def get_illust_api(art_id):
    art_info = {}
    art_info["data"] = []
    json_result = api.illust_detail(art_id)
    illust = json_result.illust
    art_info["name"] = illust.title
    art_info["create_date"] = illust.create_date[:10]
    single = illust.meta_single_page
    if single:
        art_info["data"].append(single.original_image_url)
    else:
        for page in illust.meta_pages:
            art_info["data"].append(page.image_urls.original)
    return art_info


def get_illustrations(artist_id):
    artworks[artist_id] = {}
    artist_url = f"{LINK}/users/{artist_id}/artworks"
    browser.get(artist_url)
    illust_number = "0"
    try:
        illust_number = wait_for(
            (By.XPATH, "/html/body/div[1]/div[2]/div[2]/div/div[2]/div[3]/div/div/section/div[1]/div[1]/div/div/div/span")).text
        illust_number = illust_number.replace(",", "")
    except Exception:
        print("\nCannot find Artworks")
        return
    n = ceil(int(illust_number) / 48)
    if n == 0:
        print("\nCannot find Artworks")
        return
    for i in range(n):
        print(
            f"Getting Artwork Page of {following_users[artist_id]} : {i+1} of {n}...")
        browser.get(f"{artist_url}?p={i+1}")
        wait_for(
            (By.XPATH, "/html/body/div[1]/div[2]/div[2]/div/div[2]/div[3]/div/div/section/div[1]/div[1]/div/div/div/span"))
        bs = BeautifulSoup(browser.page_source, "lxml")
        box_list = bs.find_all("li", {"class": "kFAPOq"})
        if (not box_list):
            break
        for box in box_list:
            illust_id = box.find("a")["data-gtm-value"]
            artworks[artist_id][illust_id] = get_illust_api(illust_id)


def pixiv_logout():
    res = input("Want Logout? (y/n) : ")
    if res == 'y':
        os.remove("cookies.pkl")
        browser.get("https://www.pixiv.net/logout.php")
        pixiv_login()
        return
    elif res == 'n':
        return
    else:
        print("Wrong Input")
        pixiv_logout()
        return


def pixiv_login():
    try:
        browser.get(LINK)
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            browser.add_cookie(cookie)
        browser.get(LINK)
        print("Login Success!")
        pixiv_logout()
        return
    except Exception:
        PIXIV_ID = input("Enter Your Pixiv Email or Id : ")
        PIXIV_PASSWORD = input("Enter Your Pixiv Password : ")
        print("Checking...")
        browser.get(f"{LINK}/login.php")
        try:
            try:
                banner = wait_for((By.ID, "js-privacy-policy-banner"))
                browser.execute_script("""
                const banner = arguments[0];
                banner.parentElement.removeChild(banner);
                """, banner)
            except Exception:
                pass
            pixiv_id = wait_for(
                (By.XPATH, "/html/body/div[3]/div[2]/div/form/div[1]/div[1]/input"))
            pixiv_password = wait_for(
                (By.XPATH, "/html/body/div[3]/div[2]/div/form/div[1]/div[2]/input"))
            pixiv_login_button = wait_for(
                (By.XPATH, "/html/body/div[3]/div[2]/div/form/button"))
            pixiv_id.send_keys(PIXIV_ID)
            pixiv_password.send_keys(PIXIV_PASSWORD)
            pixiv_login_button.click()
        except Exception:
            print("Cannot find login page.")
            pixiv_login()
            return
        try:
            wait_for(
                (By.XPATH, "/html/body/div[1]/div[2]/div[1]/div[1]/div[1]/div/div[3]/div[1]/div[5]/div/button"))
            print("Login Success!")
            pickle.dump(browser.get_cookies(), open("cookies.pkl", "wb"))
            pixiv_logout()
            return
        except Exception:
            print("Wrong Id or Password")
            pixiv_login()
            return


def api_auth():
    try:
        REFRESH_TOKEN = pickle.load(open("refresh_token.pkl", "rb"))
        api.auth(refresh_token=REFRESH_TOKEN)
    except Exception:
        try:
            REFRESH_TOKEN = input("Enter your refresh token : ")
            api.auth(refresh_token=REFRESH_TOKEN)
            pickle.dump(REFRESH_TOKEN, open("refresh_token.pkl", "wb"))
        except Exception:
            print("AUTH ERROR\n")
            api_auth()
            return
    print("API Authentication SUCCESS!")


def init():
    print("Initializing...")
    print(f"Download on : {base_path}")
    if not os.path.exists(base_path):
        os.mkdir(base_path)
    api_auth()
    pixiv_login()
    get_following_users(get_my_id())
    print_following()
    select_following()
    browser.quit()


def print_following():
    for i, user_id in enumerate(following_users):
        print(f"\n{i} : {following_users[user_id]}")


def download_by_artist_id(artist_id):
    artist_name = following_users[artist_id]
    artist_works = artworks[artist_id]
    if not artist_works:
        return
    for art in artist_works:
        art_info = artist_works[art]
        art_name = art_info["name"]
        DIR = os.path.join(
            base_path, artist_name, f"{art_info['create_date']}_{unique_str(art_name)}", "")
        if not os.path.exists(DIR):
            os.mkdir(DIR)
        else:
            continue
        print(
            f"Getting NAME : {art_info['name']} of ARTIST : {artist_name}...")
        for url in art_info["data"]:
            api.download(url, DIR)
    print(f"Download of ARTIST : {artist_name} Complete!")


def select_following():
    sel = input(
        "\nSelect Artist to download by Number('h' to help) : ")
    if sel == 'h':
        print("\n'p' : PRINT LIST AGAIN")
        print("'r' : RELOAD FOLLOWING USERS")
        print("'q' : EXIT")
        select_following()
        return
    if sel == 'q':
        print("\nExit")
        return
    if sel == 'p':
        print_following()
        select_following()
        return
    if sel == 'r':
        get_following_users(get_my_id())
        print_following()
        select_following()
        return
    try:
        following_id = list(following_users.keys())[int(sel)]
        DIR = os.path.join(base_path, following_users[following_id])
        if not os.path.exists(DIR):
            os.mkdir(DIR)
        get_illustrations(following_id)
        download_by_artist_id(following_id)
        select_following()
        return
    except ValueError:
        print("\nWrong Input")
        select_following()
        return


def get_my_id():
    browser.get(LINK)
    user_button = wait_for(
        (By.XPATH, "/html/body/div[1]/div[2]/div[1]/div[1]/div[1]/div/div[3]/div[1]/div[5]/div/button"))
    user_button.click()
    bs = BeautifulSoup(browser.page_source, "lxml")
    my_id = bs.find(
        "a", {"class": "gtm-user-menu-profile"})["data-gtm-value"]
    return my_id
