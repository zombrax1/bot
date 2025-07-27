import os
import sqlite3
from flask import Flask, render_template

HOME_ROUTES = [
    "/alliances",
    "/giftcodes/stats",
    "/notifications",
    "/users",
    "/changes/furnace",
    "/changes/nickname",
    "/id-channels",
]

ALLIANCE_DB_PATH = "db/alliance.sqlite"
GIFT_DB_PATH = "db/giftcode.sqlite"
NOTIFICATION_DB_PATH = "db/beartime.sqlite"
USERS_DB_PATH = "db/users.sqlite"
CHANGES_DB_PATH = "db/changes.sqlite"
ID_CHANNEL_DB_PATH = "db/id_channel.sqlite"
CHANGE_TABLES = {
    "furnace": "furnace_changes",
    "nickname": "nickname_changes",
}


def _fetch_rows(path: str, query: str) -> list[dict]:
    """Return query results as a list of dictionaries."""
    with _get_connection(path) as conn:
        rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]


def _get_connection(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def create_app() -> Flask:
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    app = Flask(__name__, template_folder=template_dir)

    @app.route("/")
    def index():
        return render_template("index.html", title="Dashboard")

    @app.route("/alliances")
    def list_alliances():
        rows = _fetch_rows(ALLIANCE_DB_PATH, "SELECT * FROM alliance_list")
        return render_template(
            "alliances.html",
            title="Alliances",
            rows=rows,
            columns=rows[0].keys() if rows else [],
        )

    @app.route("/giftcodes/stats")
    def giftcode_stats():
        with _get_connection(GIFT_DB_PATH) as conn:
            total_codes = conn.execute("SELECT COUNT(*) FROM gift_codes").fetchone()[0]
            total_claims = conn.execute("SELECT COUNT(*) FROM user_giftcodes").fetchone()[0]
            unique_users = conn.execute("SELECT COUNT(DISTINCT fid) FROM user_giftcodes").fetchone()[0]
        stats = {
            "total_codes": total_codes,
            "total_claims": total_claims,
            "unique_users": unique_users,
        }
        return render_template("giftcodes.html", title="Gift Code Stats", stats=stats)

    @app.route("/notifications")
    def notifications():
        query = (
            "SELECT id, guild_id, channel_id, hour, minute, timezone, description, "
            "next_notification FROM bear_notifications"
        )
        rows = _fetch_rows(NOTIFICATION_DB_PATH, query)
        return render_template(
            "notifications.html",
            title="Notifications",
            rows=rows,
            columns=rows[0].keys() if rows else [],
        )

    @app.route("/users")
    def users():
        rows = _fetch_rows(USERS_DB_PATH, "SELECT * FROM users")
        return render_template(
            "users.html",
            title="Users",
            rows=rows,
            columns=rows[0].keys() if rows else [],
        )

    @app.route("/changes/<change_type>")
    def list_changes(change_type: str):
        table = CHANGE_TABLES.get(change_type)
        if not table:
            return render_template(
                "table.html",
                title="Unknown Change Type",
                rows=[],
                columns=[],
            )
        rows = _fetch_rows(CHANGES_DB_PATH, f"SELECT * FROM {table}")
        template = f"{change_type}_changes.html"
        return render_template(
            template,
            title=f"{change_type.capitalize()} Changes",
            rows=rows,
            columns=rows[0].keys() if rows else [],
        )

    @app.route("/id-channels")
    def id_channels():
        rows = _fetch_rows(ID_CHANNEL_DB_PATH, "SELECT * FROM id_channels")
        return render_template(
            "id_channels.html",
            title="ID Channels",
            rows=rows,
            columns=rows[0].keys() if rows else [],
        )

    return app