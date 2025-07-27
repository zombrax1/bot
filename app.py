from pathlib import Path
from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    send_from_directory,
    url_for,
)

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

ALLIANCE_COLUMNS = ["ID", "Name", "Guild", "Members", "Created"]

SAMPLE_ALLIANCES = [
    {"id": 1, "name": "Alpha", "guild": "A", "members": 50, "created": "2021-01-01"},
    {"id": 2, "name": "Bravo", "guild": "B", "members": 40, "created": "2021-02-10"},
    {"id": 3, "name": "Charlie", "guild": "C", "members": 35, "created": "2021-03-05"},
    {"id": 4, "name": "Delta", "guild": "D", "members": 60, "created": "2021-04-20"},
    {"id": 5, "name": "Echo", "guild": "E", "members": 30, "created": "2021-05-15"},
]

GIFT_COLUMNS = ["Code", "Uses", "Created", "Expires"]
SAMPLE_GIFTS = [
    {"code": "SUMMER2025", "uses": 120, "created": "2025-07-01", "expires": "2025-08-01"},
    {"code": "WELCOME", "uses": 200, "created": "2025-05-10", "expires": "2025-12-31"},
    {"code": "ANNIV", "uses": 150, "created": "2025-06-15", "expires": "2025-07-31"},
    {"code": "NEWYEAR", "uses": 300, "created": "2025-01-01", "expires": "2025-02-01"},
    {"code": "BONUS", "uses": 80, "created": "2025-07-20", "expires": "2025-09-01"},
]

NOTIFY_COLUMNS = ["ID", "Description", "Next"]
SAMPLE_NOTIFICATIONS = [
    {"id": 1, "description": "Daily Reset", "next": "00:00"},
    {"id": 2, "description": "Alliance War", "next": "Tomorrow 18:00"},
    {"id": 3, "description": "Weekly Event", "next": "Sun 12:00"},
    {"id": 4, "description": "Gift Drop", "next": "Fri 19:00"},
    {"id": 5, "description": "Maintenance", "next": "Aug 1 03:00"},
]

NAMECHANGE_COLUMNS = ["ID", "User", "Previous", "Changed"]
SAMPLE_NAMECHANGES = [
    {"id": 1, "user": "Warrior#1234", "previous": "Hero#0001", "changed": "2025-06-30"},
    {"id": 2, "user": "Mage#2345", "previous": "Wizard#1111", "changed": "2025-07-10"},
    {"id": 3, "user": "Rogue#3456", "previous": "Sneak#2222", "changed": "2025-07-12"},
    {"id": 4, "user": "Tank#4567", "previous": "Shield#3333", "changed": "2025-06-05"},
    {"id": 5, "user": "Healer#5678", "previous": "Cleric#4444", "changed": "2025-07-01"},
]

FC_COLUMNS = ["ID", "User", "FC", "Last Seen", "Alliance"]
SAMPLE_FC_TRACK = [
    {"id": 1, "user": "Warrior#1234", "fc": "abcd-1234", "last_seen": "2025-07-20", "alliance": "Alpha"},
    {"id": 2, "user": "Mage#2345", "fc": "efgh-5678", "last_seen": "2025-07-18", "alliance": "Bravo"},
    {"id": 3, "user": "Rogue#3456", "fc": "ijkl-9012", "last_seen": "2025-07-19", "alliance": "Charlie"},
    {"id": 4, "user": "Tank#4567", "fc": "mnop-3456", "last_seen": "2025-07-16", "alliance": "Delta"},
    {"id": 5, "user": "Healer#5678", "fc": "qrst-7890", "last_seen": "2025-07-17", "alliance": "Echo"},
]

# Directory holding SQLite databases
DB_FOLDER = Path("db")


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        return render_template("index.html", title="Overview", stats=STATS, charts=CHART_DATA)

    @app.route("/alliances")
    def alliances() -> str:
        return render_template(
            "table.html",
            title="Alliances",
            columns=ALLIANCE_COLUMNS,
            data_url=url_for("alliances_data"),
        )

    @app.route("/api/alliances")
    def alliances_data() -> dict:
        return jsonify({"items": SAMPLE_ALLIANCES, "total": len(SAMPLE_ALLIANCES)})

    @app.route("/giftcodes")
    def giftcodes() -> str:
        return render_template(
            "table.html",
            title="Gift Codes",
            columns=GIFT_COLUMNS,
            data_url=url_for("giftcodes_data"),
        )

    @app.route("/api/giftcodes")
    def giftcodes_data() -> dict:
        return jsonify({"items": SAMPLE_GIFTS, "total": len(SAMPLE_GIFTS)})

    @app.route("/notifications")
    def notifications() -> str:
        return render_template(
            "table.html",
            title="Notifications",
            columns=NOTIFY_COLUMNS,
            data_url=url_for("notifications_data"),
        )

    @app.route("/api/notifications")
    def notifications_data() -> dict:
        return jsonify({"items": SAMPLE_NOTIFICATIONS, "total": len(SAMPLE_NOTIFICATIONS)})

    @app.route("/usernames")
    def usernames() -> str:
        return render_template(
            "table.html",
            title="Name Changes",
            columns=NAMECHANGE_COLUMNS,
            data_url=url_for("usernames_data"),
        )

    @app.route("/api/usernames")
    def usernames_data() -> dict:
        return jsonify({"items": SAMPLE_NAMECHANGES, "total": len(SAMPLE_NAMECHANGES)})

    @app.route("/fc-tracking")
    def fc_tracking() -> str:
        return render_template(
            "table.html",
            title="FC Tracking",
            columns=FC_COLUMNS,
            data_url=url_for("fc_tracking_data"),
        )

    @app.route("/api/fc-tracking")
    def fc_tracking_data() -> dict:
        return jsonify({"items": SAMPLE_FC_TRACK, "total": len(SAMPLE_FC_TRACK)})

    @app.route("/databases")
    def databases() -> str:
        db_files = [f.name for f in DB_FOLDER.glob("*.db")] if DB_FOLDER.is_dir() else []
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
