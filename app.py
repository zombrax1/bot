from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List, Tuple

from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    request,
    send_from_directory,
    url_for,
)
import sqlite3

STATS = {
    "alliances": 12,
    "members": 324,
    "success_rate": 86,
    "next_run": "Today 18:00",
}

CHART_DATA = {
    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "values": [12, 18, 9, 20, 16, 25, 14],
}

DB_FOLDER = Path("db")

ALLIANCE_DB = DB_FOLDER / "alliance.sqlite"
USERS_DB = DB_FOLDER / "users.sqlite"
GIFT_DB = DB_FOLDER / "giftcode.sqlite"
CHANGES_DB = DB_FOLDER / "changes.sqlite"
BEAR_DB = DB_FOLDER / "beartime.sqlite"
SETTINGS_DB = DB_FOLDER / "settings.sqlite"
ID_DB = DB_FOLDER / "id_channel.sqlite"
BACKUP_DB = DB_FOLDER / "backup.sqlite"

TABLE_CONFIG = {
    "alliances": {
        "db": ALLIANCE_DB,
        "table": "alliance_list",
        "columns": ["alliance_id", "name", "discord_server_id"],
        "search": ["name", "discord_server_id"],
        "sort": ["alliance_id", "name", "discord_server_id"],
        "default": ("name", "ASC"),
    },
    "alliancesettings": {
        "db": ALLIANCE_DB,
        "table": "alliancesettings",
        "columns": ["alliance_id", "channel_id", "interval"],
        "search": ["alliance_id"],
        "sort": ["alliance_id", "channel_id", "interval"],
        "default": ("alliance_id", "ASC"),
    },
    "users": {
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
        "sort": [
            "fid",
            "nickname",
            "furnace_lv",
            "kid",
            "stove_lv_content",
            "alliance",
        ],
        "default": ("fid", "ASC"),
    },
    "giftcodes": {
        "db": GIFT_DB,
        "table": "gift_codes",
        "columns": ["giftcode", "date", "validation_status"],
        "search": ["giftcode", "validation_status"],
        "sort": ["giftcode", "date", "validation_status"],
        "default": ("date", "DESC"),
    },
    "giftclaims": {
        "db": GIFT_DB,
        "table": "claim_logs",
        "columns": ["id", "fid", "giftcode", "claim_time"],
        "search": ["giftcode", "fid"],
        "sort": ["id", "fid", "giftcode", "claim_time"],
        "default": ("claim_time", "DESC"),
    },
    "usergiftcodes": {
        "db": GIFT_DB,
        "table": "user_giftcodes",
        "columns": ["fid", "giftcode", "status"],
        "search": ["fid", "giftcode", "status"],
        "sort": ["fid", "giftcode", "status"],
        "default": ("fid", "ASC"),
    },
    "furnacechanges": {
        "db": CHANGES_DB,
        "table": "furnace_changes",
        "columns": ["id", "fid", "old_furnace_lv", "new_furnace_lv", "change_date"],
        "search": ["fid"],
        "sort": ["id", "fid", "change_date"],
        "default": ("change_date", "DESC"),
    },
    "nicknamechanges": {
        "db": CHANGES_DB,
        "table": "nickname_changes",
        "columns": ["id", "fid", "old_nickname", "new_nickname", "change_date"],
        "search": ["fid", "old_nickname", "new_nickname"],
        "sort": ["id", "fid", "change_date"],
        "default": ("change_date", "DESC"),
    },
    "notification_history": {
        "db": BEAR_DB,
        "table": "notification_history",
        "columns": ["id", "notification_id", "notification_time", "sent_at"],
        "search": ["notification_id"],
        "sort": ["id", "notification_id", "sent_at"],
        "default": ("sent_at", "DESC"),
    },
    "botsettings": {
        "db": SETTINGS_DB,
        "table": "botsettings",
        "columns": ["id", "channelid", "giftcodestatus"],
        "search": ["channelid"],
        "sort": ["id", "channelid"],
        "default": ("id", "ASC"),
    },
    "ocr_settings": {
        "db": SETTINGS_DB,
        "table": "ocr_settings",
        "columns": ["id", "enabled", "save_images"],
        "search": ["id"],
        "sort": ["id", "enabled", "save_images"],
        "default": ("id", "ASC"),
    },
    "admin": {
        "db": SETTINGS_DB,
        "table": "admin",
        "columns": ["id", "is_initial"],
        "search": ["id"],
        "sort": ["id", "is_initial"],
        "default": ("id", "ASC"),
    },
    "versions": {
        "db": SETTINGS_DB,
        "table": "versions",
        "columns": ["file_name", "version", "is_main"],
        "search": ["file_name"],
        "sort": ["file_name", "version", "is_main"],
        "default": ("file_name", "ASC"),
    },
    "auto": {
        "db": SETTINGS_DB,
        "table": "auto",
        "columns": ["id", "value"],
        "search": ["id"],
        "sort": ["id", "value"],
        "default": ("id", "ASC"),
    },
    "adminserver": {
        "db": SETTINGS_DB,
        "table": "adminserver",
        "columns": ["id", "admin", "alliances_id"],
        "search": ["id", "admin"],
        "sort": ["id", "admin", "alliances_id"],
        "default": ("id", "ASC"),
    },
    "alliance_logs": {
        "db": SETTINGS_DB,
        "table": "alliance_logs",
        "columns": ["alliance_id", "channel_id"],
        "search": ["alliance_id"],
        "sort": ["alliance_id", "channel_id"],
        "default": ("alliance_id", "ASC"),
    },
    "test_fid_settings": {
        "db": SETTINGS_DB,
        "table": "test_fid_settings",
        "columns": ["id", "test_fid"],
        "search": ["id", "test_fid"],
        "sort": ["id", "test_fid"],
        "default": ("id", "ASC"),
    },
    "id_channels": {
        "db": ID_DB,
        "table": "id_channels",
        "columns": ["guild_id", "alliance_id", "channel_id", "created_at", "created_by"],
        "search": ["guild_id", "alliance_id"],
        "sort": ["guild_id", "alliance_id", "created_at"],
        "default": ("created_at", "DESC"),
    },
    "backups": {
        "db": BACKUP_DB,
        "table": "backup_passwords",
        "columns": ["discord_id", "backup_password", "created_at"],
        "search": ["discord_id"],
        "sort": ["discord_id", "created_at"],
        "default": ("created_at", "DESC"),
    },
}


def open_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def parse_args() -> Tuple[int, int, str, str]:
    page = max(int(request.args.get("page", 1)), 1)
    size = max(int(request.args.get("size", 10)), 1)
    search = request.args.get("search", "")
    sort = request.args.get("sort", "")
    return page, size, search, sort


def fetch_generic(conf: dict, page: int, size: int, search: str, sort: str) -> Tuple[List[dict], int]:
    db_path: Path = conf["db"]
    table: str = conf["table"]
    columns: List[str] = conf["columns"]
    search_cols: List[str] = conf["search"]
    sort_cols: List[str] = conf["sort"]
    default_col, default_dir = conf["default"]

    where = ""
    params: List[str] = []
    if search:
        like = f"%{search}%"
        where = "WHERE " + " OR ".join(f"{c} LIKE ?" for c in search_cols)
        params.extend([like] * len(search_cols))

    sort_col, sort_dir = default_col, default_dir
    if sort:
        try:
            col, direction = sort.split(":")
            if col in sort_cols and direction.lower() in {"asc", "desc"}:
                sort_col, sort_dir = col, direction.upper()
        except ValueError:
            pass

    order_clause = f"ORDER BY {sort_col} {sort_dir}"
    if sort_col == "next_notification":
        order_clause = f"ORDER BY {sort_col} IS NULL, {sort_col} {sort_dir}"

    offset = (page - 1) * size

    query = (
        f"SELECT {', '.join(columns)} FROM {table} {where} {order_clause} LIMIT ? OFFSET ?"
    )
    count_query = f"SELECT COUNT(*) FROM {table} {where}"

    with open_db(db_path) as conn:
        rows = conn.execute(query, params + [size, offset]).fetchall()
        total = conn.execute(count_query, params).fetchone()[0]

    return [dict(r) for r in rows], total


def fetch_notifications(page: int, size: int, search: str, sort: str) -> Tuple[List[dict], int]:
    where = ""
    params: List[str] = []
    if search:
        like = f"%{search}%"
        where = (
            "WHERE description LIKE ? OR timezone LIKE ? OR mention_type LIKE ?"
        )
        params = [like, like, like]

    sort_col, sort_dir = "next_notification", "ASC"
    if sort:
        try:
            col, direction = sort.split(":")
            if col in {
                "id",
                "guild_id",
                "channel_id",
                "next_notification",
            } and direction.lower() in {"asc", "desc"}:
                sort_col, sort_dir = col, direction.upper()
        except ValueError:
            pass

    order_clause = f"ORDER BY {sort_col} IS NULL, {sort_col} {sort_dir}"
    offset = (page - 1) * size

    query = f"""
        SELECT
            n.id,
            n.guild_id,
            n.channel_id,
            printf('%02d:%02d', n.hour, n.minute) AS time,
            n.timezone,
            n.description,
            n.notification_type,
            n.mention_type,
            n.repeat_enabled,
            n.repeat_minutes,
            n.is_enabled,
            n.next_notification,
            (SELECT COUNT(*) FROM bear_notification_embeds e WHERE e.notification_id = n.id) AS embed_count,
            COALESCE((SELECT GROUP_CONCAT(weekday, ',') FROM notification_days d WHERE d.notification_id = n.id), '') AS days
        FROM bear_notifications n
        {where}
        {order_clause}
        LIMIT ? OFFSET ?
    """

    count_query = f"SELECT COUNT(*) FROM bear_notifications n {where}"

    with open_db(BEAR_DB) as conn:
        rows = conn.execute(query, params + [size, offset]).fetchall()
        total = conn.execute(count_query, params).fetchone()[0]

    return [dict(r) for r in rows], total


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        return render_template("index.html", title="Overview", stats=STATS, charts=CHART_DATA)

    @app.route("/alliances")
    def alliances() -> str:
        conf = TABLE_CONFIG["alliances"]
        return render_template(
            "table.html",
            title="Alliances",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("alliances_data"),
        )

    @app.route("/api/alliances")
    def alliances_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["alliances"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/gift-codes")
    def gift_codes() -> str:
        conf = TABLE_CONFIG["giftcodes"]
        return render_template(
            "table.html",
            title="Gift Codes",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("gift_codes_data"),
        )

    @app.route("/api/gift-codes")
    def gift_codes_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["giftcodes"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/gift-codes/claims")
    def gift_claims() -> str:
        conf = TABLE_CONFIG["giftclaims"]
        return render_template(
            "table.html",
            title="Gift Claim Logs",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("gift_claims_data"),
        )

    @app.route("/api/gift-claims")
    def gift_claims_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["giftclaims"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/gift-codes/users")
    def user_giftcodes() -> str:
        conf = TABLE_CONFIG["usergiftcodes"]
        return render_template(
            "table.html",
            title="User Gift Codes",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("user_giftcodes_data"),
        )

    @app.route("/api/user-giftcodes")
    def user_giftcodes_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["usergiftcodes"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/notifications")
    def notifications() -> str:
        return render_template(
            "table.html",
            title="Notification Schedules",
            columns=[
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
            fields=[
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
            data_url=url_for("notifications_data"),
        )

    @app.route("/api/notifications")
    def notifications_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_notifications(page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/changes/nickname")
    def nickname_changes() -> str:
        conf = TABLE_CONFIG["nicknamechanges"]
        return render_template(
            "table.html",
            title="Nickname Changes",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("nickname_changes_data"),
        )

    @app.route("/api/changes/nickname")
    def nickname_changes_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["nicknamechanges"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/changes/furnace")
    def furnace_changes() -> str:
        conf = TABLE_CONFIG["furnacechanges"]
        return render_template(
            "table.html",
            title="Furnace Changes",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("furnace_changes_data"),
        )

    @app.route("/api/changes/furnace")
    def furnace_changes_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["furnacechanges"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/alliances/settings")
    def alliance_settings() -> str:
        conf = TABLE_CONFIG["alliancesettings"]
        return render_template(
            "table.html",
            title="Alliance Settings",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("alliance_settings_data"),
        )

    @app.route("/api/alliancesettings")
    def alliance_settings_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["alliancesettings"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/users")
    def users() -> str:
        conf = TABLE_CONFIG["users"]
        return render_template(
            "table.html",
            title="Users",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("users_data"),
        )

    @app.route("/api/users")
    def users_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["users"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/notifications/history")
    def notifications_history() -> str:
        conf = TABLE_CONFIG["notification_history"]
        return render_template(
            "table.html",
            title="Notification History",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("notifications_history_data"),
        )

    @app.route("/api/notifications/history")
    def notifications_history_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["notification_history"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/settings")
    def settings_bot() -> str:
        conf = TABLE_CONFIG["botsettings"]
        return render_template(
            "table.html",
            title="Bot Settings",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("settings_bot_data"),
        )

    @app.route("/api/settings/bot")
    def settings_bot_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["botsettings"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/settings/ocr")
    def settings_ocr() -> str:
        conf = TABLE_CONFIG["ocr_settings"]
        return render_template(
            "table.html",
            title="OCR Settings",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("settings_ocr_data"),
        )

    @app.route("/api/settings/ocr")
    def settings_ocr_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["ocr_settings"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/settings/admins")
    def settings_admins() -> str:
        conf = TABLE_CONFIG["admin"]
        return render_template(
            "table.html",
            title="Admin Users",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("settings_admins_data"),
        )

    @app.route("/api/settings/admin")
    def settings_admins_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["admin"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/settings/versions")
    def settings_versions() -> str:
        conf = TABLE_CONFIG["versions"]
        return render_template(
            "table.html",
            title="Versions",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("settings_versions_data"),
        )

    @app.route("/api/settings/versions")
    def settings_versions_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["versions"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/settings/auto")
    def settings_auto() -> str:
        conf = TABLE_CONFIG["auto"]
        return render_template(
            "table.html",
            title="Auto",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("settings_auto_data"),
        )

    @app.route("/api/settings/auto")
    def settings_auto_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["auto"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/settings/admin-server")
    def settings_adminserver() -> str:
        conf = TABLE_CONFIG["adminserver"]
        return render_template(
            "table.html",
            title="Admin Server",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("settings_adminserver_data"),
        )

    @app.route("/api/settings/admin-server")
    def settings_adminserver_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["adminserver"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/settings/alliance-logs")
    def settings_alliance_logs() -> str:
        conf = TABLE_CONFIG["alliance_logs"]
        return render_template(
            "table.html",
            title="Alliance Logs",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("settings_alliance_logs_data"),
        )

    @app.route("/api/settings/alliance-logs")
    def settings_alliance_logs_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["alliance_logs"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/settings/test-fid")
    def settings_test_fid() -> str:
        conf = TABLE_CONFIG["test_fid_settings"]
        return render_template(
            "table.html",
            title="Test FID Settings",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("settings_test_fid_data"),
        )

    @app.route("/api/settings/test-fid")
    def settings_test_fid_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["test_fid_settings"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/id-channels")
    def id_channels() -> str:
        conf = TABLE_CONFIG["id_channels"]
        return render_template(
            "table.html",
            title="ID Channels",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("id_channels_data"),
        )

    @app.route("/api/id-channels")
    def id_channels_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["id_channels"], page, size, search, sort)
        return jsonify({"items": rows, "total": total})

    @app.route("/backups")
    def backups() -> str:
        conf = TABLE_CONFIG["backups"]
        return render_template(
            "table.html",
            title="Backup Passwords",
            columns=conf["columns"],
            fields=conf["columns"],
            data_url=url_for("backups_data"),
        )

    @app.route("/api/backups")
    def backups_data() -> dict:
        page, size, search, sort = parse_args()
        rows, total = fetch_generic(TABLE_CONFIG["backups"], page, size, search, sort)
        for row in rows:
            row["backup_password"] = "\u2022" * 6
        return jsonify({"items": rows, "total": total})

    @app.route("/databases")
    def databases() -> str:
        if DB_FOLDER.is_dir():
            db_files = [
                {
                    "name": f.name,
                    "size": round(f.stat().st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
                for f in DB_FOLDER.glob("*.db")
            ]
        else:
            db_files = []
        return render_template(
            "databases.html",
            title="Databases",
            databases=db_files,
        )

    @app.route("/db/<path:name>")
    def download_db(name: str):
        allowed = {f.name for f in DB_FOLDER.glob("*.db")}
        if name not in allowed:
            abort(404)
        return send_from_directory(DB_FOLDER, name, as_attachment=True)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
