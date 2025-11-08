from typing import cast, Set
from flask import Blueprint, current_app, session, redirect, url_for, render_template
import redis

from ...models.model import UserID

from ..services.auth import AuthService

bp = Blueprint("admin", __name__, static_folder="static", template_folder="template", url_prefix="/admin")

@bp.route("/dashboard")
def admin():

    if "user" not in session:
        return redirect(url_for("auth.login", session_expired=True))
    
    user = cast(UserID, session["user"])
    auth   : AuthService = current_app.extensions["auth_service"]

    if not auth.is_admin(user):
        return render_template("forbidden.html")

    db : redis.StrictRedis = current_app.extensions["redis_database"]


    raw_users = cast(Set[bytes], db.smembers("active_users")) # type: ignore[reportUnknownMemberType]
    active_users = [user.decode("utf-8") for user in raw_users]

    return render_template(
        "dashboard.html",
        active_users=active_users,
        admin_status=True,
    )
