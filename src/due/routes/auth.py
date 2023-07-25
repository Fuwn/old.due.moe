from flask import redirect, Blueprint

bp = Blueprint("auth", __name__)


@bp.route("/logout")
def auth_logout():
    response = redirect("/")

    response.delete_cookie("anilist")

    return response
