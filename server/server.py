import json
import os

from flask import Flask, request, send_from_directory, render_template, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm

from database.database import db, League, Race, Coach, Team, Season, SeasonRules, Scorings
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


class NavProperties:

    def __init__(self, db: SQLAlchemy):
        self.selected_league = db.session.query(League).order_by(League.name).filter_by(is_selected=True).first()
        self.leagues = db.session.query(League).order_by(League.name).all()

        self.selected_season = None
        self.seasons = []
        if self.selected_league is not None:
            self.selected_season = get_selected_season()
            self.seasons = db.session.query(Season).filter_by(league_id=self.selected_league.id).order_by(Season.name).all()


def get_selected_league() -> League:
    return db.session.query(League).filter_by(is_selected=True).first()


def get_selected_season() -> Season:
    selected_league = get_selected_league()
    return db.session.query(Season).filter_by(league_id=selected_league.id).filter_by(is_selected=True).first()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='images/vnd.microsoft.icon')


@app.route('/')
def home():
    return render_template("home.html", nav_properties=NavProperties(db))


def persist_and_redirect(entity, entity_type: str):
    db.session.add(entity)
    db.session.commit()
    return redirect(url_for("manage", entity_type=entity_type))


@app.route("/season/select/<string:id>")
def select_season(id: int):
    selected_season = db.session.query(Season).filter_by(is_selected=True).first()
    if selected_season is not None:
        selected_season.is_selected = False
        db.session.add(selected_season)

    season = db.session.query(Season).filter_by(id=id).first()
    season.is_selected = True
    db.session.add(season)
    db.session.commit()

    return redirect(url_for('manage', entity_type="season"))


@app.route("/league/select/<string:id>")
def select_league(id: int):
    selected_league = db.session.query(League).filter_by(is_selected=True).first()
    if selected_league is not None:
        selected_league.is_selected = False
        db.session.add(selected_league)

    league = db.session.query(League).filter_by(id=id).first()
    league.is_selected = True
    db.session.add(league)
    db.session.commit()

    return redirect(url_for('manage', entity_type="league"))


@app.route("/<string:entity_type>/manage", methods=["GET", "POST"])
def manage(entity_type: str):
    form: FlaskForm
    title: str
    title_row = []
    table = []  # list of lists (every internal list contains entity information)

    if entity_type == League.__tablename__:
        title = "Leagues"

        title_row = ["Name", "Short name"]
        for league in db.session.query(League).all():
            table.append([league.name + (f" (active)" if league.is_selected else ""), league.short_name, league.id])
        form = forms.AddLeagueForm()
        if form.validate_on_submit():
            league = League()
            league.name = form.name.data
            league.short_name = form.short_name.data
            league.is_selected = True

            if selected_league is not None:
                selected_league.is_selected = False
                db.session.add(selected_league)
                db.session.commit()

            return persist_and_redirect(league, entity_type)
    elif entity_type == Season.__tablename__:
        title = "Season"

        title_row = ["Name", "Short name"]
        for season in db.session.query(Season).order_by(Season.short_name).filter_by(
                league_id=get_selected_league().id).all():
            table.append([season.name + (f" (active)" if season.is_selected else ""), season.short_name, season.id])
        form = forms.AddSeasonForm()
        if form.validate_on_submit():
            season = Season()
            season.league_id = get_selected_league().id
            season.name = form.title.data
            season.short_name = form.short_name.data
            season.is_selected = True

            if selected_season is not None:
                selected_season.is_selected = False
                db.session.add(selected_season)
                db.session.commit()

            db.session.add(season)
            db.session.commit()

            selected_season = get_selected_season()
            season_rules = SeasonRules()
            season_rules.season_id = selected_season.id

            db.session.add(season_rules)
            db.session.commit()

            scorings_loss = Scorings()
            scorings_loss.season_id = selected_season.id
            scorings_loss.touchdown_difference = -1
            scorings_loss.points_scored = 0
            db.session.add(scorings_loss)

            scorings_tie = Scorings()
            scorings_tie.season_id = selected_season.id
            scorings_tie.touchdown_difference = 0
            scorings_tie.points_scored = 1
            db.session.add(scorings_tie)

            scorings_win = Scorings()
            scorings_win.season_id = selected_season.id
            scorings_win.touchdown_difference = 1
            scorings_win.points_scored = 3
            db.session.add(scorings_win)

            db.session.commit()

            return redirect(url_for("manage", entity_type=entity_type))

    elif entity_type == Race.__tablename__:
        title = "Races"

        title_row = ["Name"]
        for race in db.session.query(Race).order_by(Race.name).all():
            table.append([race.name, race.id])

        form = forms.AddRaceForm()
        if form.validate_on_submit():
            race = Race()
            race.name = form.name.data

            return persist_and_redirect(race, entity_type)
    elif entity_type == Coach.__tablename__:
        title = "Coaches"

        title_row = ["First Name", "Last Name", "Display Name"]
        for coach in db.session.query(Coach).order_by(Coach.first_name).all():
            table.append([coach.first_name, coach.last_name, coach.display_name, coach.id])

        form = forms.AddCoachForm()

        if form.validate_on_submit():
            coach = Coach()
            coach.first_name = form.first_name.data
            coach.last_name = form.last_name.data
            coach.display_name = form.display_name.data

            return persist_and_redirect(coach, entity_type)
    elif entity_type == Team.__tablename__:
        title = "Teams"

        title_row = ["Name", "Coach", "Race"]

        selected_season = get_selected_season()
        for team in db.session.query(Team).filter_by(season_id=selected_season.id).order_by(Team.name).all():
            coach = db.session.query(Coach).filter_by(id=team.coach_id).first()
            race = db.session.query(Race).filter_by(id=team.race_id).first()
            table.append(
                [team.name, f"{coach.first_name} {coach.last_name} ({coach.display_name})", race.name, team.id])

        form = forms.AddTeamForm(app=app)
        if form.validate_on_submit():
            def generate_short_name(team_name: str) -> str:
                # TODO generate proper team name
                return team_name

            team = Team()
            team.name = form.name.data
            team.short_name = generate_short_name(form.name.data)
            team.coach_id = form.coach_select.data
            team.race_id = form.race_select.data
            team.season_id = selected_season.id

            return persist_and_redirect(team, entity_type)

    return render_template("add-or-update-entity.html", form=form, title=title, title_row=title_row, table=table,
                           entity_type=entity_type, nav_properties=NavProperties(db))


@app.route("/<string:entity_type>/update/<int:id>", methods=["GET", "POST"])
def update(entity_type: str, id: int):
    pass


@app.route("/<string:entity_type>/delete/<int:id>", methods=["POST"])
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
