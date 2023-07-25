from flask import redirect, Blueprint, request
import requests
import json
import os

bp = Blueprint("oauth", __name__)


@bp.route("/callback")
def oauth_callback():
    response = redirect("/")

    response.set_cookie(
        "anilist",
        json.dumps(
            requests.post(
                "https://anilist.co/api/v2/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": os.getenv("ANILIST_CLIENT_ID"),
                    "client_secret": os.getenv("ANILIST_CLIENT_SECRET"),
                    "redirect_uri": os.getenv("ANILIST_REDIRECT_URI"),
                    "code": request.args.get("code"),
                },
            ).json()
        ),
    )

    return response
