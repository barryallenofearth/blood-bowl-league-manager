import json
import os

from flask import request, send_from_directory, render_template, Flask
from flask_bootstrap import Bootstrap

import database.database
import table.table_generator
from database import bootstrapping
from database.database import db
from server import delete_entities
from server.manage_entities import *
from util import parsing
from html2image import Html2Image

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
    bootstrapping.init_database()


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
    season = database.get_selected_season()
    if database.get_selected_league() is None:
        return redirect(url_for("manage", entity_type="league"))
    elif season is None:
        return redirect(url_for("manage", entity_type="season"))

    season_rules = db.session.query(SeasonRules).filter_by(season_id=season.id).first()
    team_results = table.table_generator.calculate_team_scores()
    coach_results = table.table_generator.calculate_coaches_scores()
    race_results = table.table_generator.calculate_races_scores()
    scorings = db.session.query(Scorings).filter_by(season_id=season.id).order_by(Scorings.touchdown_difference.desc()).all()

    output_path = f"{os.getcwd()}/server/static/output"
    hti = Html2Image(output_path=output_path)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    with open("server/static/css/styles.css", encoding="utf-8") as css_file:
        css_content = css_file.read()
        teams_table = render_template("teams_table_for_image.html", team_results=team_results, race_results=race_results, coach_results=coach_results, scorings=scorings, css_content=css_content,
                                      term_for_team_names=season_rules.term_for_team_names, term_for_coaches=season_rules.term_for_coaches, term_for_races=season_rules.term_for_races,
                                      number_of_allowed_matches=season_rules.number_of_allowed_matches, number_of_playoff_places=season_rules.number_of_playoff_places)

        html_file = f"{output_path}/table_season_{season.short_name.replace('.', '_')}.html"
        with open(html_file, "w", encoding="utf-8") as output:
            output.write(teams_table)

        # hti.screenshot(html_file=f"{os.getcwd()}/table_season_{season.short_name.replace('.', '_')}.html", save_as=f"{output_path}/table_season_{season.short_name.replace('.', '_')}html_file.png")
        png_output = f"table_season_{season.short_name.replace('.', '_')}.png"
        print(png_output)

        hti.screenshot(html_str=teams_table, save_as=png_output)
    return render_template("home.html", team_results=team_results, race_results=race_results, coach_results=coach_results, scorings=scorings, nav_properties=NavProperties(db),
                           term_for_team_names=season_rules.term_for_team_names, term_for_coaches=season_rules.term_for_coaches, term_for_races=season_rules.term_for_races,
                           number_of_allowed_matches=season_rules.number_of_allowed_matches, number_of_playoff_places=season_rules.number_of_playoff_places)


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
    elif entity_type == BBMatch.__tablename__:
        kwargs = match_get(app, db, entity_id)
        form = kwargs[FORM_KEY]
        if form.validate_on_submit():
            return match_submit(form, db, entity_id)

    kwargs["entity_type"] = entity_type
    kwargs["nav_properties"] = NavProperties(db)
    return render_template("manage_entities.html", **kwargs)


@app.route("/<string:entity_type>/delete/<int:id>", methods=["POST"])
def delete(entity_type: str, id: int):
    message = "No matching entity type found"
    if entity_type == League.__tablename__:
        message = delete_entities.league_delete(id)
    elif entity_type == Season.__tablename__:
        message = delete_entities.season_delete(id)
    elif entity_type == Race.__tablename__:
        message = delete_entities.race_delete(id)
    elif entity_type == Coach.__tablename__:
        message = delete_entities.coach_delete(id)
    elif entity_type == Team.__tablename__:
        message = delete_entities.team_delete(id)
    elif entity_type == BBMatch.__tablename__:
        message = delete_entities.match_delete(id)

    return_json = str({'message': message, 'status': 200 if message == delete_entities.SUCCESSFULLY_DELETED else 403}).replace("'", '"')
    return json.loads(return_json)


@app.route("/match-result/user-input", methods=["POST"])
def match_result_from_user_inpt():
    match_result = request.json["match-results"]  # type list

    response = ""
    if len(match_result) == 0:
        return "No match results were submitted."
    for match in match_result:
        try:
            bb_match = parsing.parse_match_result(match)
            db.session.add(bb_match)
            db.session.commit()
            response += f"[200] Match successfully entered: '{formatting.format_match(bb_match)}' from user input '{match}'\n"
        except SyntaxError:
            response += f"[400] Match result '{match}' did not match the expected pattern.\n"

    return response.strip()
