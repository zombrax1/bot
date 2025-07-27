import os
import sqlite3
from flask import Flask, render_template

ALLIANCE_DB_PATH = "db/alliance.sqlite"
GIFT_DB_PATH = "db/giftcode.sqlite"
NOTIFICATION_DB_PATH = "db/beartime.sqlite"


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
        with _get_connection(ALLIANCE_DB_PATH) as conn:
            rows = conn.execute("SELECT * FROM alliance_list").fetchall()
            data = [dict(row) for row in rows]
        return render_template(
            "table.html", title="Alliances", rows=data, columns=data[0].keys() if data else []
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
        with _get_connection(NOTIFICATION_DB_PATH) as conn:
            rows = conn.execute(
                "SELECT id, guild_id, channel_id, hour, minute, timezone, description, next_notification FROM bear_notifications"
            ).fetchall()
            data = [dict(row) for row in rows]
        return render_template(
            "notifications.html",
            title="Notifications",
            rows=data,
            columns=data[0].keys() if data else [],
        )

    return app
