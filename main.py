from pixivpy3 import *
import pickle
import pixiv_auth
import base64


api = AppPixivAPI()

def auth_login():
    try:
        with open("auth.pickle","rb") as f:
            refresh_token = pickle.load(f)
        try:
            api.auth(refresh_token=refresh_token)
        except:
            try:
                refresh_token = print_auth_token_response(pixiv_auth.refresh(refresh_token))
                api.auth(refresh_token=refresh_token[1])
                with open("auth.pickle","wb") as f:
                    pickle.dump(refresh_token[1],f)
            except:
                print("TOKEN ERROR")
                get_refresh()
                return
    except:
        get_refresh()
        return

def get_refresh():
    pixiv_auth.main()
    res = print_auth_token_response(pixiv_auth.login())
    with open("auth.pickle","wb") as f:
        pickle.dump(res[1],f)
    api.auth(refresh_token=res[1])
    return

def print_auth_token_response(response):
    data = response.json()

    try:
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
    except KeyError:
        print("error:")
        print(data)
        exit(1)

    return [access_token,refresh_token,data.get("expires_in", 0)]
    
def illust_filter(res):
    illust_id = if_exist(res["id"])
    title = if_exist(res["title"])
    artist_id = if_exist(res["user"]["id"])
    date = if_exist(res["create_date"])
    desc = if_exist(res["caption"])
    tags = []
    urls = []
    is_deleted = False
    for tag in res["tags"]:
        if tag:
            tmp = tag["name"] + (f'({tag["translated_name"]})' if tag["translated_name"] else "")
            if tmp in tags:
                pass
            else:
                tags.append(tmp)
        else:
            pass
    if res["meta_single_page"]:
        urls.append(res["meta_single_page"]["original_image_url"])
    elif res["meta_pages"]:
        for page in res["meta_pages"]:
            urls.append(image_url_filer(page["image_urls"]))
    for url in urls:
        if "limit_unknown" in url:
            is_deleted = True
    else:
        pass
    return {"id":illust_id,"title":title,"artist_id":artist_id,"tags":tags,"urls":urls,"date":date,"desc":desc, "deleted":is_deleted}

def if_exist(a):
    return a if a else None

def image_url_filer(json):
    if json["original"]:
        return json["original"]
    elif json["large"]:
        return json["large"]
    else:
        return None

def download(
    url: str,
    referer: str = "https://app-api.pixiv.net/",
) -> bool:
    with api.requests_call(
        "GET", url, headers={"Referer": referer}, stream=True
    ) as response:
        return base64.b64encode(response.content).decode('utf-8')

def main():
    auth_login()
    return api.user_id

if __name__ == "__main__":
    my_id = main()
    bookmark_illusts=[]
    res = api.user_bookmarks_illust(my_id)
    for illust in res["illusts"]:
        bookmark_illusts.append(illust_filter(illust))
    # while True:
    #     if res["next_url"]:
    #         res = api.user_bookmarks_illust(**api.parse_qs(res["next_url"]))
    #         for illust in res["illusts"]:
    #             bookmark_illusts.append(illust_filter(illust))
    #     else:
    #         break
    with open("json.txt","w", encoding='utf-8') as f:
        f.write(str(bookmark_illusts))
