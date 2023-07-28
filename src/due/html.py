import requests
import joblib
from due.cache import cache
from flask import request
import math
import re
import os


def seen(element, manga=False):
    read = 0

    if manga:
        available_matches = re.search(r"\[<a.*?>(\d+)<\/a>\]", element)
        read_matches = re.search(r"\[<a.*?>(?=\d+)<\/a>\]", element)

        if read_matches:
            read = int(read_matches.group())
            print(read)

        if available_matches:
            return int(available_matches.group(1)) - read
        else:
            return 0

    available_matches = re.findall(r"\d+\]|\[\d+", element)
    seen_matches = re.search(
        r"\s(\d+)*?(<span style=\"opacity: 50%\">/(\d+)</span>)*\s", element
    )

    if seen_matches:
        read = int(seen_matches.group(1))

    if len(available_matches) > 1:
        return int(available_matches[1].strip("[]")) - read
    elif len(available_matches) == 1:
        return int(available_matches[0].strip("[]")) - read
    else:
        return 0


def anime_to_html(releasing_outdated_anime):
    current_html = []
    ids = []

    for media in releasing_outdated_anime:
        anime = media["media"]
        title = anime["title"]["english"]
        id = anime["id"]

        if id in ids:
            continue
        else:
            ids.append(id)

        progress = (anime["mediaListEntry"] or {"progress": 0})["progress"]
        available = (
            {"episode": 0}
            if media["media"]["nextAiringEpisode"] is None
            else media["media"]["nextAiringEpisode"]
        )["episode"] - 1

        if available <= 0:
            available = "?"

        if title is None:
            title = anime["title"]["romaji"]

        if request.cookies.get("show_missing") is not None and str(available)[0] == "?":
            ids.pop()

            continue

        episodes = anime["episodes"]
        total_html = (
            "" if episodes is None else f'<span style="opacity: 50%">/{episodes}</span>'
        )

        current_html.append(
            f'<li><a href="https://anilist.co/anime/{id}" target="_blank">{title}</a> {progress}{total_html} [{available}]</li>'
        )

    current_html = sorted(current_html, key=seen)

    current_html.insert(0, "<ul>")
    current_html.append("</ul>")

    return ("".join(current_html), len(ids))


def manga_to_html(releasing_outdated_manga, show_missing):
    current_html = []
    ids = []

    def process(media):
        manga = media["media"]
        title = manga["title"]["native"]
        id = manga["id"]
        previous_volume_largest_chapter = 0

        if id in ids:
            return
        else:
            ids.append(id)

        progress = manga["mediaListEntry"]["progress"]
        available = (
            {"episode": 0}
            if media["media"]["nextAiringEpisode"] is None
            else media["media"]["nextAiringEpisode"]
        )["episode"] - 1

        if available <= 0:
            available = "?"

        mangadex_data = cache.get(str(manga["id"]) + "id")
        mangadex_id = None

        if mangadex_data is None:
            mangadex_data = requests.get(
                "https://api.mangadex.org/manga",
                params={"title": title, "year": manga["startDate"]["year"]},
            ).json()["data"]

            # This is very stupid. It should never get this far, anyway.
            if len(mangadex_data) == 0:
                mangadex_data = requests.get(
                    "https://api.mangadex.org/manga",
                    params={
                        "title": manga["title"]["romaji"],
                        "year": manga["startDate"]["year"],
                    },
                ).json()["data"]

                if len(mangadex_data) == 0:
                    mangadex_data = requests.get(
                        "https://api.mangadex.org/manga",
                        params={
                            "title": manga["title"]["romaji"],
                            "year": manga["startDate"]["year"],
                        },
                    ).json()["data"]

            cache.set(str(manga["id"]) + "id", mangadex_data)

        if len(mangadex_data) == 0:
            available = "?"
        else:
            mangadex_id = mangadex_data[0]["id"]
            manga_chapter_aggregate = cache.get(str(manga["id"]) + "ag")

            if manga_chapter_aggregate is None:
                manga_chapter_aggregate = requests.get(
                    f"https://api.mangadex.org/manga/{mangadex_id}/aggregate",
                ).json()

                cache.set(str(manga["id"]) + "ag", manga_chapter_aggregate)

            if "none" in manga_chapter_aggregate["volumes"]:
                previous_volume_largest_chapter = list(
                    manga_chapter_aggregate["volumes"][
                        str(
                            dict(enumerate(manga_chapter_aggregate["volumes"])).get(1)
                            or "none"
                        )
                    ]["chapters"]
                )[0]
                available = list(
                    manga_chapter_aggregate["volumes"]["none"]["chapters"]
                )[0]

                if str(available) == "none":
                    available = list(
                        manga_chapter_aggregate["volumes"]["none"]["chapters"]
                    )[1]
            else:
                try:
                    available = list(
                        manga_chapter_aggregate["volumes"][
                            str(list(manga_chapter_aggregate["volumes"])[0])
                        ]["chapters"]
                    )[0]
                except Exception:
                    available = "?"

                if not str(available)[0].isdigit():
                    if len(manga_chapter_aggregate["volumes"]) == 0:
                        ids.pop()

                        return

                    available = math.floor(
                        float(
                            list(manga_chapter_aggregate["volumes"]["1"]["chapters"])[0]
                        )
                    )

        if show_missing is not None and str(available)[0] == "?":
            ids.pop()

            return

        # Useful when debugging
        # if str(available)[0] != "?":
        #     ids.pop()

        #     return

        if str(available)[0] == "{":
            ids.pop()

            return

        if str(available)[0].isdigit():
            available = math.floor(float(available))

            if math.floor(float(previous_volume_largest_chapter)) > available:
                available = math.floor(float(previous_volume_largest_chapter))

        if str(available) != "?" and int(progress) >= int(available):
            ids.pop()

            return

        available_link = (
            available
            if mangadex_id is None
            else f'<a href="https://mangadex.org/title/{mangadex_id}">{available}</a>'
        )

        current_html.append(
            f'<li><a href="https://anilist.co/manga/{id}" target="_blank">{manga["title"]["english"] or manga["title"]["romaji"] or title}</a> {progress} [{available_link}]</li>'
        )

    joblib.Parallel(n_jobs=int(os.getenv("CONCURRENT_JOBS")) or 4, require="sharedmem")(
        joblib.delayed(process)(media) for media in releasing_outdated_manga
    )

    current_html = sorted(current_html, key=lambda x: seen(x, manga=True))

    current_html.insert(0, "<ul>")
    current_html.append("</ul>")

    return ("".join(current_html), len(ids))


def page(main_content, footer):
    message = '<blockquote>Slow loads? If your media hasn\'t been cached in a while, the first load will take a couple seconds longer than the rest. Subsequent requests on cached media should be faster. <a href="/?hide_message">Hide <i>forever</i></a></blockquote>'

    if request.cookies.get("hide_message") == "1":
        message = ""

    return f"""
<!DOCTYPE html>
<html>
    <head>
        <title>期限</title>

        <link rel="stylesheet" type="text/css" href="https://latex.now.sh/style.css">
        <link rel="stylesheet" type="text/css" href="https://skybox.sh/css/palettes/base16-light.css">
        <link rel="stylesheet" type="text/css" href="https://skybox.sh/css/risotto.css">
        <!-- <link rel="stylesheet" type="text/css" href="https://skybox.sh/css/custom.css"> -->
        <link rel="shortcut icon" type="image/x-icon" href="https://ps.fuwn.me/-tePaWtKW2y/angry-miku-nakano.ico">
    </head>

    <body>
        <style>text-align: center;</style>

        <h1><a href="/">期限</a></h1>

        {main_content}

        <p></p>

        <hr>

        <p>{footer}</p>

        {message}
    </body>
</html>
"""
