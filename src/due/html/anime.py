from flask import request
from .utilities import seen


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

        if request.cookies.get("show_missing") is None and str(available)[0] == "?":
            ids.pop()

            continue

        episodes = anime["episodes"]
        airing_at = (media["media"]["nextAiringEpisode"] or {"timeUntilAiring": None})["timeUntilAiring"]

        if airing_at is not None:
            hours = airing_at / 3600

            if hours >= 24:
                weeks = (hours // 24) // 7

                if weeks >= 1:
                    available = (
                        str(available)
                        + f'] <span style="opacity: 50%">{available + 1} in {int(round(weeks, 0))} week{"" if weeks == 1 else "s"}'
                    )
                else:
                    available = (
                        str(available)
                        + f'] <span style="opacity: 50%">{available + 1} in {int(round(hours // 24, 0))} day{"" if hours // 24 == 1 else "s"}'
                    )
            else:
                available = (
                    str(available)
                    + f'] <span style="opacity: 50%">{available + 1} in {int(round(hours, 0))} hour{"" if hours // 24 == 1 else "s"}'
                )

            available = str(available) + "</span>"
        else:
            available = str(available) + "]"

        total_html = (
            "" if episodes is None else f'<span style="opacity: 50%">/{episodes}</span>'
        )

        current_html.append(
            f'<li><a href="https://anilist.co/anime/{id}" target="_blank">{title}</a> {progress}{total_html} <a href="/anilist/increment?id={id}&progress={progress + 1}">+</a> [{available}</li>'
        )

    current_html = sorted(current_html, key=seen)

    current_html.insert(0, "<ul>")
    current_html.append("</ul>")

    return ("".join(current_html), len(ids))
