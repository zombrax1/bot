import sqlite3
from flask import Flask, jsonify

HOME_ROUTES = ["/alliances", "/giftcodes/stats", "/notifications"]

ALLIANCE_DB_PATH = "db/alliance.sqlite"
GIFT_DB_PATH = "db/giftcode.sqlite"
NOTIFICATION_DB_PATH = "db/beartime.sqlite"


def _get_connection(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        """Simple JSON message listing available routes."""
        return jsonify({"message": "Dashboard is running", "routes": HOME_ROUTES})

    @app.route("/alliances")
    def list_alliances():
        with _get_connection(ALLIANCE_DB_PATH) as conn:
            rows = conn.execute("SELECT * FROM alliance_list").fetchall()
            return jsonify([dict(row) for row in rows])

    @app.route("/giftcodes/stats")
    def giftcode_stats():
        with _get_connection(GIFT_DB_PATH) as conn:
            total_codes = conn.execute("SELECT COUNT(*) FROM gift_codes").fetchone()[0]
            total_claims = conn.execute("SELECT COUNT(*) FROM user_giftcodes").fetchone()[0]
            unique_users = conn.execute("SELECT COUNT(DISTINCT fid) FROM user_giftcodes").fetchone()[0]
        return jsonify({
            "total_codes": total_codes,
            "total_claims": total_claims,
            "unique_users": unique_users,
        })

    @app.route("/notifications")
    def notifications():
        with _get_connection(NOTIFICATION_DB_PATH) as conn:
            rows = conn.execute(
                "SELECT id, guild_id, channel_id, hour, minute, timezone, description, next_notification FROM bear_notifications"
            ).fetchall()
            return jsonify([dict(row) for row in rows])

    return app
