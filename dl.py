import os
import re
import requests
import pprint
import json
from pathlib import Path
import urllib.request
from urllib.parse import quote
import sys

# Queries
MAX = 500
BASE_URL = "https://dragalialost.gamepedia.com/api.php?action=cargoquery&format=json&limit={}".format(
    MAX
)

# regex stuff
alphafy_re = re.compile("[^a-zA-Z_]")


def snakey(name):
    s = name.replace("ñ", "n")
    s = s.replace("&amp;", "and")
    s = s.replace(" ", "_")
    s = alphafy_re.sub("", s)
    return s.lower()


def get_api_request(offset, **kwargs):
    q = "{}&offset={}".format(BASE_URL, offset)
    for key, value in kwargs.items():
        q += "&{}={}".format(key, quote(value))
    return q


def get_data(**kwargs):
    offset = 0
    data = []
    while offset % MAX == 0:
        url = get_api_request(offset, **kwargs)
        r = requests.get(url).json()
        try:
            data += r["cargoquery"]
            offset += len(data)
        except:
            raise Exception(url)
    return data


def download_images(file_name, new_content=[]):
    pattern = {
        "adventurer": r"\d{6}_\d{2,3}_r0[345].png",
        "dragon": r"\d{6}_01.png",
        "weapon": r"\d{6}_01_\d{5}.png",
        "wyrmprint": r"\d{6}_0[12].png",
        "material": r"\d{9}.png",
    }

    start = {
        "adventurer": "100001_01_r04.png",
        "dragon": "210001_01.png",
        "weapon": "301001_01_19901.png",
        "wyrmprint": "400001_01.png",
        "material": "104001011.png",
    }

    end = {
        "adventurer": "2",
        "dragon": "3",
        "weapon": "4",
        "wyrmprint": "A",
        "material": "4",
    }

    chara = {
        "{}_{:02d}_r0{}.png".format(
            d["title"]["Id"], int(d["title"]["VariationId"]), int(d["title"]["Rarity"])
        ): d["title"]["FullName"]
        for d in get_data(tables="Adventurers", fields="Id,VariationId,FullName,Rarity")
    }
    drag = {
        "{}_{:02d}.png".format(d["title"]["BaseId"], int(d["title"]["VariationId"])): d[
            "title"
        ]["FullName"]
        for d in get_data(tables="Dragons", fields="BaseId,VariationId,FullName")
    }
    wp = {
        "{}_02.png".format(d["title"]["BaseId"]): d["title"]["Name"]
        for d in get_data(tables="Wyrmprints", fields="BaseId,Name")
    }
    w = {
        "{}_01_{}.png".format(d["title"]["BaseId"], d["title"]["FormId"]): d["title"][
            "WeaponName"
        ]
        for d in get_data(tables="Weapons", fields="BaseId,FormId,WeaponName")
    }

    download = {}
    aifrom = start[file_name]
    keep = True
    while keep:
        url = "https://dragalialost.gamepedia.com/api.php?action=query&format=json&list=allimages&aifrom={}&ailimit=max".format(
            aifrom
        )

        response = requests.get(url).json()
        try:
            data = response["query"]["allimages"]

            for i in data:
                name = i["name"]
                if name[0] == end[file_name]:
                    keep = False
                    break
                r = re.search(pattern[file_name], name)
                if r:
                    download[name] = i["url"]

            con = response.get("continue", None)
            if con and con.get("aicontinue", None):
                aifrom = con["aicontinue"]
            else:
                keep = False
                break

        except:
            raise Exception

    for k, v in download.items():
        fn = k
        if file_name == "adventurer":
            if fn in chara:
                fn = snakey(chara[k]) + ".png"
                path = Path(__file__).resolve().parent / "img/{}/{}".format("adv", fn)
                urllib.request.urlretrieve(v, path)
                print("download image: {}".format(fn))
        if file_name == "dragon":
            if fn in drag:
                fn = snakey(drag[k]) + ".png"
                path = Path(__file__).resolve().parent / "img/{}/{}".format("d", fn)
                urllib.request.urlretrieve(v, path)
                print("download image: {}".format(fn))
        if file_name == "weapon":
            if fn in w:
                fn = snakey(w[k]) + ".png"
                path = Path(__file__).resolve().parent / "img/{}/{}".format("w", fn)
                urllib.request.urlretrieve(v, path)
                print("download image: {}".format(fn))
        if file_name == "wyrmprint":
            if fn in wp:
                print(fn, wp[k])
                fn = snakey(wp[k]) + ".png"
                path = Path(__file__).resolve().parent / "img/{}/{}".format("wp", fn)
                urllib.request.urlretrieve(v, path)
                print("download image: {}".format(fn))


if __name__ == "__main__":
    download_images(sys.argv[1])

