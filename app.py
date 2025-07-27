from flask import Flask, jsonify, render_template, url_for

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

TABLE_COLUMNS = ["ID", "Name", "Guild", "Members", "Created"]

SAMPLE_ALLIANCES = [
    {"id": 1, "name": "Alpha", "guild": "A", "members": 50, "created": "2021-01-01"},
    {"id": 2, "name": "Bravo", "guild": "B", "members": 40, "created": "2021-02-10"},
    {"id": 3, "name": "Charlie", "guild": "C", "members": 35, "created": "2021-03-05"},
    {"id": 4, "name": "Delta", "guild": "D", "members": 60, "created": "2021-04-20"},
    {"id": 5, "name": "Echo", "guild": "E", "members": 30, "created": "2021-05-15"},
]


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
            columns=TABLE_COLUMNS,
            data_url=url_for("alliances_data"),
        )

    @app.route("/api/alliances")
    def alliances_data() -> dict:
        return jsonify({"items": SAMPLE_ALLIANCES, "total": len(SAMPLE_ALLIANCES)})

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
