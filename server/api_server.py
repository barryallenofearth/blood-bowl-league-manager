import json
import os

from flask import Flask, request
from database.database import db, League

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

DATABASE_FILENAME = 'database.db'

database_path = f'sqlite:///{DATABASE_FILENAME}'
if os.environ.get("DATABASE_URI") is not None:
    database_path = os.environ["DATABASE_URI"]
app.config['SQLALCHEMY_DATABASE_URI'] = database_path

db.init_app(app)

with app.app_context():
    db.create_all()


def persist_league(league: League, content):
    if "title" not in content:
        return "No title committed for league persistance", 400
    if "short_name" not in content:
        return "No short_name committed for league persistance", 400
    league.title = content["title"]
    league.short_name = content["short_name"]

    db.session.add(league)
    db.session.commit()


@app.route("/league/create", methods=["POST"])
def create_league():
    # TODO handle logo submission
    new_league = League()
    exception = persist_league(new_league, request.json)
    if exception is not None:
        return exception

    return f"League '{new_league.title}' successfully committed.", 200


@app.route("/league/update/<int:league_id>", methods=["PATCH"])
def update_league(league_id: int):
    # TODO handle logo submission
    league = db.session.query(League).filter_by(id=league_id).first()

    exception = persist_league(league, request.json)
    if exception is not None:
        return exception

    return f"League '{league.title}' successfully updated.", 200


def jsonify_league(league: League):
    return {"id": league.id, "title": league.title, "short_name": league.short_name}


@app.route("/league/get")
def get_all_leagues() -> list:
    all_leagues = db.session.query(League).all()
    leagues_json = {"leagues": []}
    for league in all_leagues:
        leagues_json["leagues"].append(jsonify_league(league))

    string = str(leagues_json).replace("'", '"')
    print(string)
    return json.loads(string)


@app.route("/league/get/<int:league_id>")
def get_league(league_id: int) -> League:
    league = db.session.query(League).filter_by(id=league_id).first()
    league_json = jsonify_league(league)

    string = str(league_json).replace("'", '"')

    print(string)
    return json.loads(string)
