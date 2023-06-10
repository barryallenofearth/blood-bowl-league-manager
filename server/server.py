import json
import os

from flask import Flask, request, send_from_directory, render_template
from flask_bootstrap import Bootstrap

from database.database import db, Team
from server import delete_entities
from server.manage_entities import *

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
    database.init_database()


class NavProperties:

    def __init__(self, db: SQLAlchemy):
        self.selected_league = db.session.query(League).order_by(League.name).filter_by(is_selected=True).first()
        self.leagues = db.session.query(League).order_by(League.name).all()

        self.selected_season = None
        self.seasons = []
        if self.selected_league is not None:
            self.selected_season = database.get_selected_season()
            self.seasons = db.session.query(Season).filter_by(league_id=self.selected_league.id).order_by(Season.name).all()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='images/vnd.microsoft.icon')


@app.route('/')
def home():
    return render_template("home.html", nav_properties=NavProperties(db))


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
    entity_id = 0
    if "id" in request.args:
        entity_id = int(request.args.get("id"))

    kwargs = {}
    if entity_type == League.__tablename__:
        kwargs = league_get(db, entity_id)
        form = kwargs[FORM_KEY]
        if form.validate_on_submit():
            return league_submit(form, db, entity_id)
    elif entity_type == Season.__tablename__:
        kwargs = season_get(db, entity_id)
        form = kwargs[FORM_KEY]
        if form.validate_on_submit():
            return season_submit(form, db, entity_id)

    elif entity_type == Race.__tablename__:
        kwargs = race_get(db, entity_id)
        form = kwargs[FORM_KEY]
        if form.validate_on_submit():
            return race_submit(form, db, entity_id)
    elif entity_type == Coach.__tablename__:
        kwargs = coach_get(db, entity_id)
        form = kwargs[FORM_KEY]
        if form.validate_on_submit():
            return coach_submit(form, db, entity_id)
    elif entity_type == Team.__tablename__:
        kwargs = team_get(app, db, entity_id)
        form = kwargs[FORM_KEY]
        if form.validate_on_submit():
            return team_submit(form, db, entity_id)

    kwargs["entity_type"] = entity_type
    kwargs["nav_properties"] = NavProperties(db)
    return render_template("manage_entities.html", **kwargs)


@app.route("/<string:entity_type>/delete/<int:id>", methods=["POST"])
def delete(entity_type: str, id: int):
    message = "No matching entity type found"
    if entity_type == League.__tablename__:
        message = delete_entities.league_delete(id)
        print(message)
    elif entity_type == Season.__tablename__:
        message = delete_entities.season_delete(id)
        print(message)

    elif entity_type == Race.__tablename__:
        message = delete_entities.race_delete(id)
        print(message)
    elif entity_type == Coach.__tablename__:
        message = delete_entities.coach_delete(id)
        print(message)
    elif entity_type == Team.__tablename__:
        message = delete_entities.team_delete(id)
        print(message)

    dict = str({'message': message}).replace("'", '"')
    print(dict)
    return json.loads(dict)


def jsonify_league(league: League):
    return {"id": league.id, "title": league.title, "short_name": league.short_name}


@app.route("/match-result/user-input", methods=["POST"])
def match_result_from_user_inpt():
    match_result = request.json["match-result"]

    pass
