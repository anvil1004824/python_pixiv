from flask import Flask, render_template
from main import main,download,api, illust_filter

app=Flask(__name__)

@app.route("/")
def htmlshow():
    my_id = main()
    bookmark_illusts=[]
    res = api.user_bookmarks_illust(my_id)
    for illust in res["illusts"]:
        bookmark_illusts.append(illust_filter(illust))
    links = []
    for illust in bookmark_illusts:
        links.append(illust["urls"][0])
    data=list(download(link) for link in links)
    return render_template("index.html", data=data,length=len(bookmark_illusts))

app.run()