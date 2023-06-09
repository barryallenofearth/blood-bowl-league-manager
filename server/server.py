import json
import os

from flask import Flask, request, send_from_directory, render_template, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm

from database.database import db, League, Race, Coach, Team, Season, SeasonRules, Scorings
from server import forms
import pandas as pd

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

    if db.session.query(League).count() == 0:
        init_leagues = pd.read_csv("init/leagues.csv", delimiter=";")
        for league_index, league_data in init_leagues.iterrows():
            league = League()
            league.id = league_data["id"]
            league.name = league_data["name"]
            league.short_name = league_data["short_name"]
            league.is_selected = league_data["is_selected"]
            db.session.add(league)

        db.session.commit()

        init_seasons = pd.read_csv("init/seasons.csv", delimiter=";")
        for season_index, season_data in init_seasons.iterrows():
            season = Season()
            season.id = season_data["id"]
            season.league_id = season_data["league_id"]
            season.name = season_data["name"]
            season.short_name = season_data["short_name"]
            season.is_selected = season_data["is_selected"]
            db.session.add(season)

        db.session.commit()

        init_races = pd.read_csv("init/races.csv", delimiter=";")
        for race_index, race_data in init_races.iterrows():
            race = Race()
            race.id = race_data["id"]
            race.name = race_data["name"]

            db.session.add(race)

        db.session.commit()

        init_coaches = pd.read_csv("init/coaches.csv", delimiter=";")
        for coach_index, coach_data in init_coaches.iterrows():
            coach = Coach()
            coach.id = coach_data["id"]
            coach.league_id = coach_data["league_id"]
            coach.first_name = coach_data["first_name"]
            coach.last_name = coach_data["last_name"]
            coach.display_name = coach_data["display_name"]
            db.session.add(coach)

        db.session.commit()


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
    entity_id = 0
    if "id" in request.args:
        entity_id = int(request.args.get("id"))

    if entity_type == League.__tablename__:
        title = "Leagues"

        title_row = ["Name", "Short name"]
        for league in db.session.query(League).all():
            table.append([league.name + (f" (active)" if league.is_selected else ""), league.short_name, league.id])

        league: League
        if entity_id > 0:
            league = db.session.query(League).filter_by(id=entity_id).first()
        else:
            league = League()
        form = forms.AddLeagueForm(name=league.name, short_name=league.short_name)

        if form.validate_on_submit():
            league.name = form.name.data
            league.short_name = form.short_name.data
            league.is_selected = True

            selected_league = get_selected_league()
            if selected_league is not None:
                selected_league.is_selected = False
                db.session.add(selected_league)

            return persist_and_redirect(league, entity_type)
    elif entity_type == Season.__tablename__:
        title = "Season"

        title_row = ["Name", "Short name"]
        for season in db.session.query(Season).order_by(Season.short_name).filter_by(league_id=get_selected_league().id).all():
            table.append([season.name + (f" (active)" if season.is_selected else ""), season.short_name, season.id])

        season: Season
        season_rules: SeasonRules
        if entity_id == 0:
            season = Season()
            season_rules = SeasonRules()
        else:
            season = db.session.query(Season).filter_by(id=entity_id).first()
            season_rules = db.session.query(SeasonRules).filter_by(id=season.id).first()
        form = forms.AddSeasonForm(name=season.name,
                                   short_name=season.short_name,
                                   team_short_name_length=season_rules.team_short_name_length,
                                   number_of_allowed_matches=season_rules.number_of_allowed_matches,
                                   number_of_allowed_matches_vs_same_opponent=season_rules.number_of_allowed_matches_vs_same_opponent,
                                   number_of_playoff_places=season_rules.number_of_playoff_places,
                                   term_for_team_names=season_rules.term_for_team_names,
                                   term_for_coaches=season_rules.term_for_coaches,
                                   term_for_races=season_rules.term_for_races)
        if form.validate_on_submit():

            season.league_id = get_selected_league().id
            season.name = form.name.data
            season.short_name = form.short_name.data
            season.is_selected = True

            selected_season = get_selected_season()
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

        race: Race
        if entity_id == 0:
            race = Race()
        else:
            race = db.session.query(Race).filter_by(id=entity_id).first()

        form = forms.AddRaceForm(name=race.name)
        if form.validate_on_submit():
            race.name = form.name.data

            return persist_and_redirect(race, entity_type)
    elif entity_type == Coach.__tablename__:
        title = "Coaches"

        title_row = ["First Name", "Last Name", "Display Name"]
        for coach in db.session.query(Coach).filter_by(league_id=get_selected_league().id).order_by(Coach.first_name).all():
            table.append([coach.first_name, coach.last_name, coach.display_name, coach.id])

        coach: Coach
        if entity_id == 0:
            coach = Coach()
        else:
            coach = db.session.query(Coach).filter_by(id=entity_id).first()

        form = forms.AddCoachForm(first_name=coach.first_name, last_name=coach.last_name, display_name=coach.display_name)

        if form.validate_on_submit():
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
            table.append([team.name, f"{coach.first_name} {coach.last_name} ({coach.display_name})", race.name, team.id])

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

    kwargs = {"form": form, "title": title, "title_row": title_row, "table": table,
              "entity_type": entity_type, "nav_properties": NavProperties(db)}
    return render_template("manage_entities.html", **kwargs)


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
