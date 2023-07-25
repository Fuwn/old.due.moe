import time
from due.html import anime_to_html, manga_to_html, page
from due.media import create_collection
from flask import make_response, redirect, request, Blueprint
import json
import os

bp = Blueprint("index", __name__)


@bp.route("/")
def home():
    response = make_response("")

    if request.args.get("hide_message") is not None:
        if request.cookies.get("hide_message") is None:
            response = redirect("/")
            response.set_cookie("hide_message", "1")

    if request.cookies.get("anilist"):
        anilist = json.loads(request.cookies.get("anilist"))
        start = time.time()
        (current_anime, name) = create_collection(anilist, "ANIME")
        anime_time = time.time() - start
        start = time.time()
        (current_manga, _) = create_collection(anilist, "MANGA")
        manga_time = time.time() - start

        releasing_anime = [
            media for media in current_anime if media["media"]["status"] == "RELEASING"
        ]
        releasing_manga = [
            media for media in current_manga if media["media"]["status"] == "RELEASING"
        ]
        releasing_outdated_manga = [
            media
            for media in releasing_manga
            if media["media"]["type"] == "MANGA"
            and int(media["media"]["mediaListEntry"]["progress"])
            >= 1  # Useful when testing
        ]
        releasing_outdated_anime = [
            media
            for media in releasing_anime
            if media["media"]["type"] == "ANIME"
            and int(
                (
                    {"episode": 0}
                    if media["media"]["nextAiringEpisode"] is None
                    else media["media"]["nextAiringEpisode"]
                )["episode"]
            )
            - 1
            != int(media["media"]["mediaListEntry"]["progress"])
        ]
        (anime_html, anime_length) = anime_to_html(releasing_outdated_anime)
        (manga_html, manga_length) = manga_to_html(releasing_outdated_manga)

        response.set_data(
            page(
                f"""<a href="/auth/logout">Logout from AniList ({name})</a>

            <br>""",
                f"""<details open>
                <summary>Anime [{anime_length}] <small style="opacity: 50%">{round(anime_time, 2)}ms</small></summary>
                {anime_html}
            </details>

            <p></p>

            <details closed>
            <summary>Manga [{manga_length}] <small style="opacity: 50%">{round(manga_time, 2)}ms</small></summary>
                {manga_html}
            </details>
            """,
            )
        )
    else:
        response.set_data(
            page(
                f"""<a href="https://anilist.co/api/v2/oauth/authorize?client_id={os.getenv('ANILIST_CLIENT_ID')}&redirect_uri={os.getenv('ANILIST_REDIRECT_URI')}&response_type=code">Login with AniList</a>

            <br>""",
                "Please log in to view due media.",
            )
        )

    return response
