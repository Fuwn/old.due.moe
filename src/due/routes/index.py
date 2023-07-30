import time
from due.html.utilities import page
from due.html.anime import anime_to_html
from due.html.manga import manga_to_html
from due.anilist.collection import create_collection
from due.anilist.utilities import last_activity, user_id, user_name_to_id
from flask import make_response, redirect, request, Blueprint
import json
import os
import datetime

bp = Blueprint("index", __name__)


@bp.route("/<username>")
def user(username):
    return home(username)


@bp.route("/", defaults={"username": None})
def home(username):
    response = make_response("")
    disable_manga = True

    if request.args.get("show_manga") is not None:
        disable_manga = False

    if request.args.get("hide_message") is not None:
        if request.cookies.get("hide_message") is None:
            response = redirect("/")

            response.set_cookie("hide_message", "1")

    if request.args.get("toggle_missing") is not None:
        response = redirect(
            f"/{'?show_manga' if request.args.get('show_manga') is not None else ''}"
        )

        if request.cookies.get("show_missing") is None:
            response.set_cookie("show_missing", "1")
        else:
            response.delete_cookie("show_missing")

    # print(
    #     requests.post(
    #         "https://anilist.co/api/v2/oauth/token",
    #         data={
    #             "grant_type": "refresh_token",
    #             "client_id": os.getenv("ANILIST_CLIENT_ID"),
    #             "client_secret": os.getenv("ANILIST_CLIENT_SECRET"),
    #             "refresh_token": json.loads(request.cookies.get("anilist"))[
    #                 "refresh_token"
    #             ],
    #         },
    #     ).json()
    # )

    if request.cookies.get("anilist"):
        anilist = json.loads(request.cookies.get("anilist"))

        if user_id(anilist) == -1:
            response = redirect("/")

            response.delete_cookie("anilist")

            return response

        start = time.time()
        (current_anime, name) = create_collection(
            anilist, "ANIME", request.args.get("username") or username
        )

        print(name)

        releasing_anime = [
            media for media in current_anime if media["media"]["status"] == "RELEASING"
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
            != int((media["media"]["mediaListEntry"] or {"progress": 0})["progress"])
        ]
        (anime_html, anime_length) = anime_to_html(releasing_outdated_anime)
        anime_time = time.time() - start
        start = time.time()
        manga_body = '<a href="/?show_manga">Show manga</a>'

        if not disable_manga:
            (current_manga, _) = create_collection(
                anilist, "MANGA", request.args.get("username")
            )
            releasing_manga = [
                media
                for media in current_manga
                if media["media"]["status"] == "RELEASING"
            ]
            releasing_outdated_manga = [
                media
                for media in releasing_manga
                if media["media"]["type"] == "MANGA"
                and int(
                    (media["media"]["mediaListEntry"] or {"progress": 0})["progress"]
                )
                >= 1  # Useful when testing
            ]
            (manga_html, manga_length) = manga_to_html(
                releasing_outdated_manga, request.cookies.get("show_missing")
            )
            manga_time = time.time() - start
            manga_body = f"""
            <p></p>

            <details closed>
            <summary>Manga [{manga_length}] <small style="opacity: 50%">{round(manga_time, 2)}s</small></summary>
                {manga_html}
            </details>
            """

        response.set_data(
            page(
                f"""<a href="/auth/logout">Log out from AniList ({name})</a>
                {"<p></p><p>You don't have any new activity statuses from the past day! Create one to keep your streak!</p>" if datetime.datetime.fromtimestamp(last_activity(user_name_to_id(name))).date()
            != datetime.date.today() else "<p></p>"}""",
                f"""<a href=\"/?toggle_missing{'&show_manga' if request.args.get('show_manga') is not None else ''}\">{'Hide' if request.cookies.get('show_missing') else 'Show'} unresolved</a><p></p><details open>
                <summary>Anime [{anime_length}] <small style="opacity: 50%">{round(anime_time, 2)}s</small></summary>
                {anime_html}
            </details>

            {manga_body}""",
            )
        )
    else:
        response.set_data(
            page(
                f"""<a href="https://anilist.co/api/v2/oauth/authorize?client_id={os.getenv('ANILIST_CLIENT_ID')}&redirect_uri={os.getenv('ANILIST_REDIRECT_URI')}&response_type=code">Log in with AniList</a>

            <br>""",
                "Please log in to view due media.",
            )
        )

    return response
