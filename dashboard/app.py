import os
import sqlite3
from flask import Flask, render_template, request, jsonify

if __name__ == "__main__" or __package__ is None:
    import db
else:
    from . import db


def _db_path(env: str) -> str:
    return os.getenv(env, db.DEFAULT_PATHS[env])


ALLIANCE_DB = _db_path(db.ALLIANCE_DB_ENV)
USERS_DB = _db_path(db.USERS_DB_ENV)
GIFTCODE_DB = _db_path(db.GIFTCODE_DB_ENV)
BEARTIME_DB = _db_path(db.BEARTIME_DB_ENV)
SETTINGS_DB = _db_path(db.SETTINGS_DB_ENV)
ID_CHANNEL_DB = _db_path(db.ID_CHANNEL_DB_ENV)
BACKUP_DB = _db_path(db.BACKUP_DB_ENV)


TABLE_CONFIGS = {
    "alliances": {
        "title": "Alliances",
        "db": ALLIANCE_DB,
        "table": "alliance_list",
        "columns": ["alliance_id", "name", "discord_server_id"],
        "search": ["name", "discord_server_id"],
        "default_sort": "name ASC",
        "api": "/api/alliances",
    },
    "users": {
        "title": "Users",
        "db": USERS_DB,
        "table": "users",
        "columns": [
            "fid",
            "nickname",
            "furnace_lv",
            "kid",
            "stove_lv_content",
            "alliance",
        ],
        "search": ["fid", "nickname", "alliance"],
        "default_sort": "fid ASC",
        "api": "/api/users",
    },
    "gift-codes": {
        "title": "Gift Codes",
        "db": GIFTCODE_DB,
        "table": "gift_codes",
        "columns": ["giftcode", "date", "validation_status"],
        "search": ["giftcode", "validation_status"],
        "default_sort": "date DESC",
        "api": "/api/gift-codes",
    },
    "gift-claims": {
        "title": "Gift Claim Logs",
        "db": GIFTCODE_DB,
        "table": "claim_logs",
        "columns": ["id", "fid", "giftcode", "claim_time"],
        "search": ["fid", "giftcode"],
        "default_sort": "claim_time DESC",
        "api": "/api/gift-claims",
    },
    "user-giftcodes": {
        "title": "User Gift Codes",
        "db": GIFTCODE_DB,
        "table": "user_giftcodes",
        "columns": ["fid", "giftcode", "status"],
        "search": ["fid", "giftcode", "status"],
        "default_sort": "fid ASC",
        "api": "/api/user-giftcodes",
    },
    "notifications": {
        "title": "Notification Schedules",
        "db": BEARTIME_DB,
        "table": "bear_notifications",
        "columns": [
            "id",
            "guild_id",
            "channel_id",
            "hour",
            "minute",
            "timezone",
            "description",
            "notification_type",
            "mention_type",
            "repeat_enabled",
            "repeat_minutes",
            "is_enabled",
            "next_notification",
        ],
        "search": ["guild_id", "channel_id", "description"],
        "default_sort": "next_notification ASC",
        "api": "/api/notifications",
        "final_columns": [
            "id",
            "guild_id",
            "channel_id",
            "time",
            "timezone",
            "description",
            "notification_type",
            "mention_type",
            "repeat_enabled",
            "repeat_minutes",
            "is_enabled",
            "next_notification",
            "embed_count",
            "days",
        ],
    },
    "notifications/history": {
        "title": "Notification History",
        "db": BEARTIME_DB,
        "table": "notification_history",
        "columns": ["id", "notification_id", "notification_time", "sent_at"],
        "search": ["notification_id"],
        "default_sort": "sent_at DESC",
        "api": "/api/notifications/history",
    },
    "id-channels": {
        "title": "ID Channels",
        "db": ID_CHANNEL_DB,
        "table": "id_channels",
        "columns": [
            "guild_id",
            "alliance_id",
            "channel_id",
            "created_at",
            "created_by",
        ],
        "search": ["guild_id", "alliance_id", "channel_id"],
        "default_sort": "created_at DESC",
        "api": "/api/id-channels",
    },
    "settings": {
        "title": "Bot Settings",
        "db": SETTINGS_DB,
        "table": "botsettings",
        "columns": ["id", "channelid", "giftcodestatus"],
        "search": ["channelid", "giftcodestatus"],
        "default_sort": "id ASC",
        "api": "/api/settings/bot",
    },
    "settings-ocr": {
        "title": "OCR Settings",
        "db": SETTINGS_DB,
        "table": "ocr_settings",
        "columns": ["id", "enabled", "save_images"],
        "search": ["enabled"],
        "default_sort": "id ASC",
        "api": "/api/settings/ocr",
    },
    "backups": {
        "title": "Backup Passwords",
        "db": BACKUP_DB,
        "table": "backup_passwords",
        "columns": ["discord_id", "backup_password", "created_at"],
        "search": ["discord_id"],
        "default_sort": "created_at DESC",
        "api": "/api/backups",
    },
}


def create_app() -> Flask:
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))

    @app.route("/")
    def overview():
        alliances_conn = db.get_connection(ALLIANCE_DB)
        users_conn = db.get_connection(USERS_DB)
        gift_conn = db.get_connection(GIFTCODE_DB)
        bear_conn = db.get_connection(BEARTIME_DB)
        try:
            alliances = alliances_conn.execute("SELECT COUNT(*) FROM alliance_list").fetchone()[0]
        except sqlite3.Error:
            alliances = 0
        try:
            members = users_conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        except sqlite3.Error:
            members = 0
        try:
            total_codes = gift_conn.execute("SELECT COUNT(*) FROM user_giftcodes").fetchone()[0]
            success_codes = gift_conn.execute(
                "SELECT COUNT(*) FROM user_giftcodes WHERE status='success'"
            ).fetchone()[0]
        except sqlite3.Error:
            total_codes = success_codes = 0
        success_pct = round((success_codes / total_codes * 100) if total_codes else 0, 2)
        try:
            next_run = bear_conn.execute(
                "SELECT MIN(next_notification) FROM bear_notifications WHERE is_enabled=1"
            ).fetchone()[0]
        except sqlite3.Error:
            next_run = None
        chart = db.redemptions_last_7_days(GIFTCODE_DB)
        kpis = {
            "alliances": alliances,
            "members": members,
            "success_pct": success_pct,
            "next_run": next_run or "N/A",
        }
        return render_template("index.html", title="Overview", kpis=kpis, chart=chart)

    def register_table_routes(name: str, cfg: dict) -> None:
        route = f"/{name.replace('_', '-') if '_' in name else name}"
        api_route = cfg["api"]

        def table_page(cfg=cfg):
            columns = cfg.get("final_columns", cfg["columns"])
            return render_template(
                "table.html", title=cfg["title"], columns=columns, data_url=api_route
            )

        def table_api(cfg=cfg):
            page = int(request.args.get("page", 1))
            size = int(request.args.get("size", 10))
            sort = request.args.get("sort", "")
            search = request.args.get("search", "")
            rows, total = db.fetch_paginated(
                cfg["db"],
                cfg["table"],
                cfg["columns"],
                cfg["search"],
                page,
                size,
                sort,
                cfg["default_sort"],
                search,
            )
            if name == "notifications":
                conn = db.get_connection(cfg["db"])
                rows = db.derive_notifications_rows(rows, conn)
                final_cols = cfg["final_columns"]
                rows = [{col: r.get(col) for col in final_cols} for r in rows]
            if name == "backups":
                for r in rows:
                    r["backup_password"] = db.mask_password(r.get("backup_password", ""))
            return jsonify({"items": rows, "total": total})

        page_endpoint = name.replace("/", "_").replace("-", "_")
        api_endpoint = f"api_{page_endpoint}"
        app.add_url_rule(route, endpoint=page_endpoint, view_func=table_page)
        app.add_url_rule(api_route, endpoint=api_endpoint, view_func=table_api)

    for n, c in TABLE_CONFIGS.items():
        register_table_routes(n, c)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
