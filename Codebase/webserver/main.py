from datetime import timedelta

import redis
from flask import Flask
from flask_session import Session # type: ignore[reportMissingTypeStubs]

from  Codebase.models.model import UserID

from .services.auth import AuthService

from .routes.admin import bp as admin_bp


admin_users = {UserID("admin")} # Replace with loading from environment
users_list = {UserID("admin"): ("admin", "admin")} # Replace with loading from environment

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "dVb9gu(W*q85Fa#eAfNI&GTl2tPXjzKBZ$1%^0OicMCRnLU@ms34pvhSYryDwEo!"  # Replace with loading from environment
    app.permanent_session_lifetime = timedelta(minutes=5)

    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_REDIS"] = redis.StrictRedis(host="localhost", port=6379, db=0)
    Session(app)

    redis_database = redis.StrictRedis(host="localhost", port=6379, db=1)
    redis_database.flushdb() # type: ignore[reportUnknownMemberType]

    auth = AuthService(admin_users, users_list)

    app.extensions = getattr(app, "extensions", {})
    app.extensions["auth_service"]      = auth

    app.register_blueprint(admin_bp)

    return app

if __name__ == "__main__":
    create_app().run(host="localhost", port=5000)
