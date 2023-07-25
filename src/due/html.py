import requests
import joblib
from due.cache import cache
from flask import request


def anime_to_html(releasing_outdated_anime):
    current_html = "<ul>"
    titles = []

    for media in releasing_outdated_anime:
        anime = media["media"]
        title = anime["title"]["english"]

        if title in titles:
            continue
        else:
            titles.append(title)

        id = anime["id"]
        progress = anime["mediaListEntry"]["progress"]
        available = (
            {"episode": 0}
            if media["media"]["nextAiringEpisode"] is None
            else media["media"]["nextAiringEpisode"]
        )["episode"] - 1

        if available <= 0:
            available = "?"

        if title is None:
            title = anime["title"]["romaji"]

        current_html += f'<li><a href="https://anilist.co/anime/{id}" target="_blank">{title}</a> {progress} [{available}]</li>'

    return (current_html + "</ul>", len(titles))


def manga_to_html(releasing_outdated_manga):
    current_html = ["<ul>"]
    titles = []

    def process(media):
        manga = media["media"]
        title = manga["title"]["english"]

        if title in titles:
            return
        else:
            titles.append(title)

        id = manga["id"]
        progress = manga["mediaListEntry"]["progress"]
        available = (
            {"episode": 0}
            if media["media"]["nextAiringEpisode"] is None
            else media["media"]["nextAiringEpisode"]
        )["episode"] - 1

        if available <= 0:
            available = "?"

        if title is None:
            title = manga["title"]["romaji"]

        mangadex_data = cache.get(str(manga["id"]) + "id")
        mangadex_id = None

        if mangadex_data is None:
            mangadex_data = requests.get(
                "https://api.mangadex.org/manga",
                params={"title": title, "year": manga["startDate"]["year"]},
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
                            str(len(list(manga_chapter_aggregate["volumes"])) - 1)
                        ]["chapters"]
                    )[0]
                except Exception:
                    available = "?"

            if str(progress) == str(available):
                titles.pop()

                return

        if str(available)[0] == "{":
            return

        available_link = (
            available
            if mangadex_id is None
            else f'<a href="https://mangadex.org/title/{mangadex_id}">{available}</a>'
        )

        current_html.append(
            f'<li><a href="https://anilist.co/manga/{id}" target="_blank">{title}</a> {progress} [{available_link}]</li>'
        )

    # 80
    joblib.Parallel(n_jobs=4, require="sharedmem")(
        joblib.delayed(process)(media) for media in releasing_outdated_manga
    )

    current_html.append("</ul>")

    return ("".join(current_html), len(titles))


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

        <h1>期限</h1>

        {main_content}

        <p></p>

        <hr>

        <p>{footer}</p>

        {message}
    </body>
</html>
"""
