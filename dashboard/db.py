import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Environment variable names
ALLIANCE_DB_ENV = "ALLIANCE_DB"
USERS_DB_ENV = "USERS_DB"
GIFTCODE_DB_ENV = "GIFTCODE_DB"
CHANGES_DB_ENV = "CHANGES_DB"
BEARTIME_DB_ENV = "BEARTIME_DB"
SETTINGS_DB_ENV = "SETTINGS_DB"
ID_CHANNEL_DB_ENV = "ID_CHANNEL_DB"
BACKUP_DB_ENV = "BACKUP_DB"

# Default locations
DEFAULT_PATHS = {
    ALLIANCE_DB_ENV: "./data/alliance.sqlite",
    USERS_DB_ENV: "./data/users.sqlite",
    GIFTCODE_DB_ENV: "./data/giftcode.sqlite",
    CHANGES_DB_ENV: "./data/changes.sqlite",
    BEARTIME_DB_ENV: "./data/beartime.sqlite",
    SETTINGS_DB_ENV: "./data/settings.sqlite",
    ID_CHANNEL_DB_ENV: "./data/id_channel.sqlite",
    BACKUP_DB_ENV: "./data/backup.sqlite",
}

_connections: Dict[str, sqlite3.Connection] = {}


def get_connection(path: str) -> sqlite3.Connection:
    """Return a cached sqlite3 connection for the given path.

    Missing parent directories are created automatically so connecting to a path
    that does not yet exist will create an empty database instead of raising an
    error.
    """

    if path not in _connections:
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _connections[path] = conn
    return _connections[path]


def fetch_paginated(
    db_path: str,
    table: str,
    columns: List[str],
    searchable_cols: List[str],
    page: int,
    size: int,
    sort: str,
    default_sort: str,
    search: str = "",
) -> Tuple[List[Dict], int]:
    """Return paginated rows and total count respecting search and sort."""

    conn = get_connection(db_path)
    order_col, order_dir = default_sort.split()
    if sort:
        parts = sort.split(":")
        if (
            len(parts) == 2
            and parts[0] in columns
            and parts[1].lower() in {"asc", "desc"}
        ):
            order_col, order_dir = parts[0], parts[1].upper()
    where_clause = ""
    params: List = []
    search_cols = [c for c in searchable_cols if c in columns]
    if search and search_cols:
        like = f"%{search}%"
        cond = " OR ".join([f"{c} LIKE ?" for c in search_cols])
        where_clause = f"WHERE {cond}"
        params.extend([like] * len(search_cols))
    try:
        total_query = f"SELECT COUNT(*) FROM {table} {where_clause}"
        total = conn.execute(total_query, params).fetchone()[0]
        query = (
            f"SELECT {', '.join(columns)} FROM {table} {where_clause} "
            f"ORDER BY {order_col} {order_dir} LIMIT ? OFFSET ?"
        )
        params_with_paging = params + [size, (page - 1) * size]
        rows = [dict(row) for row in conn.execute(query, params_with_paging).fetchall()]
    except sqlite3.Error:
        rows, total = [], 0
    return rows, total


def redemptions_last_7_days(db_path: str) -> Dict[str, List]:
    """Return labels and counts of redemptions for the last seven days."""
    conn = get_connection(db_path)
    try:
        query = (
            "SELECT substr(claim_time,1,10) AS day, COUNT(*) cnt "
            "FROM claim_logs GROUP BY day ORDER BY day DESC LIMIT 7"
        )
        rows = conn.execute(query).fetchall()
        if not rows:
            raise ValueError("no data")
        data = list(reversed([(row["day"], row["cnt"]) for row in rows]))
    except sqlite3.Error:
        today = datetime.utcnow().date()
        data = [
            ((today - timedelta(days=i)).isoformat(), 0) for i in reversed(range(7))
        ]
    labels = [d for d, _ in data]
    counts = [c for _, c in data]
    return {"labels": labels, "data": counts}


def mask_password(_: str) -> str:
    """Return a masked password representation."""
    return "\u2022\u2022\u2022\u2022\u2022\u2022"


def derive_notifications_rows(rows: List[Dict], conn: sqlite3.Connection) -> List[Dict]:
    """Add derived fields for notifications rows."""
    for row in rows:
        hour = int(row.pop("hour", 0))
        minute = int(row.pop("minute", 0))
        row["time"] = f"{hour:02d}:{minute:02d}"
        try:
            embed_count = conn.execute(
                "SELECT COUNT(*) FROM bear_notification_embeds WHERE notification_id=?",
                (row["id"],),
            ).fetchone()[0]
            days = conn.execute(
                "SELECT GROUP_CONCAT(weekday, ',') FROM notification_days WHERE notification_id=?",
                (row["id"],),
            ).fetchone()[0]
        except sqlite3.Error:
            embed_count = 0
            days = ""
        row["embed_count"] = embed_count
        row["days"] = days or ""
    return rows
