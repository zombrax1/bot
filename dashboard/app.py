from flask import Flask, jsonify, render_template, url_for

# Dashboard statistics
STATS = {
    "alliances": 12,
    "members": 324,
    "success_rate": 86,
    "next_run": "Today 18:00",
}

# Line chart data
CHARTS = {
    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "values": [12, 18, 9, 20, 16, 25, 14],
}

# Table columns and sample rows
ALLIANCE_COLUMNS = ["ID", "Name", "Guild", "Members", "Created"]
SAMPLE_ALLIANCES = [
    {"id": 1, "name": "Nova Corps", "guild_id": "12345", "members_count": 58, "created_at": "2024-01-10"},
    {"id": 2, "name": "Shadow Order", "guild_id": "22345", "members_count": 41, "created_at": "2024-03-21"},
    {"id": 3, "name": "Crimson Wing", "guild_id": "32345", "members_count": 36, "created_at": "2024-05-02"},
    {"id": 4, "name": "Azure Vanguard", "guild_id": "42345", "members_count": 49, "created_at": "2024-06-15"},
    {"id": 5, "name": "Iron Wolves", "guild_id": "52345", "members_count": 27, "created_at": "2024-07-08"},
]


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")

    @app.route("/")
    def index() -> str:
        return render_template(
            "index.html",
            title="Overview",
            stats=STATS,
            charts=CHARTS,
            active="overview",
        )

    @app.route("/alliances")
    def alliances() -> str:
        return render_template(
            "table.html",
            title="Alliances",
            columns=ALLIANCE_COLUMNS,
            data_url=url_for("alliances_data"),
            active="alliances",
        )

    @app.route("/api/alliances")
    def alliances_data() -> dict:
        return jsonify({"items": SAMPLE_ALLIANCES, "total": len(SAMPLE_ALLIANCES)})

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
