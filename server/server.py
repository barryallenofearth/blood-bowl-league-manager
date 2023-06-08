import json
import os

from flask import Flask, request, send_from_directory, render_template, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm

from database.database import db, League, Race, Coach
from server import forms

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

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


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='images/vnd.microsoft.icon')


@app.route('/')
def home():
    return render_template("home.html")


def persist_and_redirect_home(entity):
    db.session.add(entity)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/<string:entity_type>/create", methods=["GET", "POST"])
def create(entity_type: str):
    form: FlaskForm
    title: str
    title_row = []
    table = []  # list of lists (every internal list contains entity information)

    if entity_type == League.__tablename__:
        title = "League"

        title_row = ["Name", "Short name"]
        for league in db.session.query(League).all():
            table.append([league.title, league.short_name, league.id])
        form = forms.AddLeagueForm()
        if form.validate_on_submit():
            new_league = League()
            new_league.title = form.title.data
            new_league.short_name = form.short_name.data

            return persist_and_redirect_home(new_league)

    elif entity_type == Race.__tablename__:
        title = "Race"

        title_row = ["Name"]
        for race in db.session.query(Race).all():
            table.append([race.name, race.id])

        form = forms.AddRaceForm()
        if form.validate_on_submit():
            race = Race()
            race.title = form.name.data

            return persist_and_redirect_home(race)
    elif entity_type == Coach.__tablename__:
        title = "Coach"

        title_row = ["First Name", "Last Name", "Display Name"]
        for coach in db.session.query(Coach).all():
            table.append([coach.first_name, coach.last_name, coach.display_name, coach.id])

        form = forms.AddCoachForm()
        if form.validate_on_submit():
            coach = Coach()
            coach.first_name = form.first_name.data
            coach.last_name = form.last_name.data
            coach.display_name = form.display_name.data

            return persist_and_redirect_home(coach)

    return render_template("add-or-update-entity.html", form=form, title=title, title_row=title_row, table=table)


@app.route("/<string:entity_type>/update/<int:league_id>", methods=["GET", "POST"])
def update(entity_type: str, id: int):
    pass


@app.route("/<string:entity_type>/delete/<int:league_id>", methods=["POST"])
def delete(entity_type: str, id: int):
    pass


def jsonify_league(league: League):
    return {"id": league.id, "title": league.title, "short_name": league.short_name}


@app.route("/<string:entity_type>/get")
def get_all(entity_type: str) -> list:
    all_leagues = db.session.query(League).all()
    leagues_json = {"leagues": []}
    for league in all_leagues:
        leagues_json["leagues"].append(jsonify_league(league))

    string = str(leagues_json).replace("'", '"')
    print(string)
    return json.loads(string)


@app.route("/<string:entity_type>/get/<int:id>")
def get(entity_type: str, id: int) -> League:
    league = db.session.query(League).filter_by(id=id).first()
    league_json = jsonify_league(league)

    string = str(league_json).replace("'", '"')

    print(string)
    return json.loads(string)


@app.route("/match-result/user-input", methods=["POST"])
def match_result_from_user_inpt():
    match_result = request.json["match-result"]

    pass
