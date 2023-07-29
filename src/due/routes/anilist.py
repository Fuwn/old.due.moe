from flask import redirect, Blueprint, request
import requests
import json

bp = Blueprint("anilist", __name__)


@bp.route("/increment")
def increment_media():
    if request.cookies.get("anilist"):
        anilist = json.loads(request.cookies.get("anilist"))

        return requests.post(
            "https://graphql.anilist.co",
            json={
                "query": f"""mutation {{ SaveMediaListEntry(mediaId: {request.args.get('id') or 30013}, progress: {request.args.get('progress') or 1}) {{
                id
            }} }}"""
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": anilist["token_type"] + " " + anilist["access_token"],
            },
        ).json()

    return redirect(request.headers.get("Referer") or "/")
