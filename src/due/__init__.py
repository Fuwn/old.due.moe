from flask import Flask
from due.routes import auth, oauth, index
from due.html import page
from flask_cors import CORS
from dotenv import load_dotenv
from due.cache import cache
import os
import logging

load_dotenv()

app = Flask(__name__)
log = logging.getLogger("werkzeug")

CORS(app)

log.setLevel(logging.ERROR)
app.register_blueprint(auth.bp, url_prefix="/auth")
app.register_blueprint(oauth.bp, url_prefix="/oauth")
app.register_blueprint(index.bp)
app.secret_key = os.getenv("SECRET_KEY")


@app.errorhandler(Exception)
def error_handler(e):
    return page(
        """<p>You have encountered a critcal application error. This means that one or more media entries on your lists have resolved abnormaly.</p>
        <p></p>
        <p>Contact <a href="https://anilist.co/user/fuwn">Fuwn</a> on AniList for help; please, attach the error code below.</p>""",
        f"<pre>{e}</pre>",
    )


cache.init_app(app)
