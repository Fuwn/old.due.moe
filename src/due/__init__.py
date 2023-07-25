from flask import Flask
from due.routes import auth, oauth, index
from flask_cors import CORS
from dotenv import load_dotenv
from due.cache import cache

load_dotenv()

app = Flask(__name__)

CORS(app)

app.register_blueprint(auth.bp, url_prefix="/auth")
app.register_blueprint(oauth.bp, url_prefix="/oauth")
app.register_blueprint(index.bp)
app.secret_key = "due.moe"

cache.init_app(app)
