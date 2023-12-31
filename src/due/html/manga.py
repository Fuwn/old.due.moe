import requests
import joblib
from due.cache import cache
import math
import os
from .utilities import seen
from flask import request


def rerequest(manga, year):
    mangadex_data = requests.get(
        "https://api.mangadex.org/manga",
        params={"title": manga["title"]["native"], "year": year},
    ).json()["data"]

    # This is very stupid. It should never get this far, anyway.
    if len(mangadex_data) == 0:
        mangadex_data = requests.get(
            "https://api.mangadex.org/manga",
            params={
                "title": manga["title"]["romaji"],
                "year": year,
            },
        ).json()["data"]

        if len(mangadex_data) == 0:
            mangadex_data = requests.get(
                "https://api.mangadex.org/manga",
                params={
                    "title": manga["title"]["romaji"],
                    "year": year,
                },
            ).json()["data"]

    return mangadex_data


def manga_to_html(releasing_outdated_manga, show_missing):
    current_html = []
    ids = []
    disable_outbound_links = request.args.get("outbound_links") is None

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
            mangadex_data = rerequest(manga, manga["startDate"]["year"])

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

        if show_missing is None and str(available)[0] == "?":
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
            if mangadex_id is None or disable_outbound_links
            else f'<a href="https://mangadex.org/title/{mangadex_id}">{available}</a>'
        )

        current_html.append(
            f'<li><a href="https://anilist.co/manga/{id}" target="_blank">{manga["title"]["english"] or manga["title"]["romaji"] or title}</a> {progress} <a href="/anilist/increment?id={id}&progress={progress + 1}">+</a> [{available_link}]</li>'
        )

    joblib.Parallel(n_jobs=int(os.getenv("CONCURRENT_JOBS")) or 4, require="sharedmem")(
        joblib.delayed(process)(media) for media in releasing_outdated_manga
    )

    current_html = sorted(current_html, key=lambda x: seen(x, manga=True))

    current_html.insert(0, "<ul>")
    current_html.append("</ul>")

    return ("".join(current_html), len(ids))
