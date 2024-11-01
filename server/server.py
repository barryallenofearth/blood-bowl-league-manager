import json
import logging
import os
from json.decoder import JSONDecodeError

from flask import send_from_directory, render_template, request
from flask_bootstrap import Bootstrap
from flask_caching import Cache

import database.database
from database import bootstrapping
from database.database import db
from server import delete_entities
from server.forms import UserInputForm, StatisticsForm
from server.manage_entities import *
from table import score_table, casualties_table, statistics
from table.score_table import SeasonStatistics
from util import parsing, imaging
from util.parsing import ParsingResponse

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

cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 100000000000000
})
cache.init_app(app)


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


@app.route('/health')
def health():
    return "I am fine"


def parse_user_input(user_input: str, match_type_selector=None):
    def could_not_be_parsed(user_input: str):
        return ParsingResponse(400, 'user input could not be parsed', f"{user_input}", '')

    try:
        if parsing.MATCH_RESULT_MATCHER.match(user_input):
            bb_match = parsing.parse_match_result(user_input)
            if match_type_selector is not None:
                set_match_type(match_type_selector, bb_match)
            db.session.add(bb_match)
            db.session.commit()
            return ParsingResponse(200, 'match successfully entered', f"{user_input}", f"{formatting.format_match(bb_match)}")
        elif parsing.CASUALTIES_MATCHER.match(user_input):
            additional_statistics = parsing.parse_additional_statistics_input(user_input)
            db.session.add(additional_statistics)
            db.session.commit()
            return ParsingResponse(200, 'casualties entry successfully entered', f"{user_input}", f"{formatting.format_additional_statistics(additional_statistics)}")
        else:
            return could_not_be_parsed(user_input)

    except SyntaxError:
        return could_not_be_parsed(user_input)


def only_cache_get(*args, **kwargs):
    if request.method == 'GET':
        return False

    return True


@app.route('/', methods=["GET", "POST"])
def home():
    if database.get_selected_league() is None:
        return redirect(url_for("manage", entity_type="league"))

    season = database.get_selected_season()
    if season is None:
        return redirect(url_for("manage", entity_type="season"))

    form = UserInputForm()

    kwargs = render_start_page(season)

    kwargs['form'] = form

    if form.validate_on_submit():
        cache.clear()
        parsing_response = parse_user_input(form.user_input.data, form.match_type_select.data)
        kwargs['parsing_response'] = parsing_response
    return render_template("home.html", **kwargs)


@cache.cached(unless=only_cache_get)
def render_start_page(season):
    team_results = score_table.calculate_team_scores()

    coaches_unique = set()
    number_of_matches = 0
    for team_result in team_results:
        coaches_unique.add(team_result.coach)
        number_of_matches += team_result.number_of_matches

    season_statistics = SeasonStatistics(len(team_results), len(coaches_unique), int(number_of_matches / 2))

    team_casualties = casualties_table.calculate_team_casualties()
    total_number_of_casualties = sum([team_casualty.casualties for team_casualty in team_casualties])
    scorings = db.session.query(Scorings).filter_by(season_id=season.id).order_by(Scorings.touchdown_difference.desc()).all()
    kwargs = {'team_results': team_results, 'scorings': scorings, 'nav_properties': NavProperties(db),
              'team_casualties': team_casualties, 'total_number_of_casualties': total_number_of_casualties,
              'term_for_team_names': season.term_for_team_names, 'term_for_coaches': season.term_for_coaches, 'term_for_races': season.term_for_races,
              'season_statistics': season_statistics,
              'number_of_allowed_matches': season.number_of_allowed_matches, 'number_of_playoff_places': season.number_of_playoff_places}
    return kwargs


@app.route("/statistics", methods=["GET", "POST"])
@cache.cached(unless=only_cache_get)
def statistics_overview():
    form = StatisticsForm()
    analyzed_league = "All leagues"
    if form.validate_on_submit():
        selected_league_id = int(form.league.data)

        coach_results = score_table.calculate_coaches_scores(league_id=selected_league_id)
        race_results = score_table.calculate_races_scores(league_id=selected_league_id)
        form = StatisticsForm(league=form.league.data)

        if selected_league_id != 0:
            analyzed_league = db.session.query(League).filter_by(id=selected_league_id).first().name

    else:
        coach_results = score_table.calculate_coaches_scores()
        race_results = score_table.calculate_races_scores()
    stats = statistics.determine_statistics(db)

    season = database.get_selected_season()
    scorings = score_table.generate_scorings()[::-1]
    return render_template("statistics.html", nav_properties=NavProperties(db), stats=stats, race_results=race_results, coach_results=coach_results,
                           term_for_coaches=season.term_for_coaches, term_for_races=season.term_for_races, scorings=scorings, show_coaches_stats_link=True,
                           form=form, analyzed_league=analyzed_league)


@app.route("/statistics/coach/<int:coach_id>")
@cache.cached()
def statistics_coach(coach_id: int):
    coach_results, coach_statistics = statistics.coach_statistics(coach_id, db)

    season = database.get_selected_season()
    scorings = score_table.generate_scorings()[::-1]

    return render_template("statistics_coaches.html", nav_properties=NavProperties(db), coach_results=coach_results, coach_statistics=coach_statistics,
                           term_for_coaches=season.term_for_coaches, term_for_races=season.term_for_races, scorings=scorings)


@app.route("/download/<string:entity_type>")
def download_table(entity_type: str):
    imaging.update_images(entity_type)

    league = database.get_selected_league()
    season = database.get_selected_season()
    uploads = os.path.join(app.root_path, "static/output/")
    file_name = f"{entity_type}_table_{league.short_name}_season_{season.short_name.replace('.', '_')}.png"
    return send_from_directory(directory=uploads, path=file_name, as_attachment=True, download_name=file_name)


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

    cache.clear()
    return redirect(url_for('manage', entity_type="league"))


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

    cache.clear()
    return redirect(url_for('manage', entity_type="season"))


@app.route("/<string:entity_type>/manage", methods=["GET", "POST"])
def manage(entity_type: str):
    entity_id = 0
    if "id" in request.args:
        entity_id = int(request.args.get("id"))

    if request.method == "POST":
        cache.clear()

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
    elif entity_type == AdditionalStatistics.__tablename__:
        kwargs = additional_statistics_get(app, db, entity_id)
        form = kwargs[FORM_KEY]
        if form.validate_on_submit():
            return additional_statistics_submit(form, db, entity_id)

    kwargs["entity_type"] = entity_type
    kwargs["nav_properties"] = NavProperties(db)
    return render_template("manage_entities.html", **kwargs)


@app.route("/<string:entity_type>/delete/<int:id>", methods=["POST"])
def delete(entity_type: str, id: int):
    message = "No matching entity type found"
    cache.clear()
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
    elif entity_type == AdditionalStatistics.__tablename__:
        message = delete_entities.additional_statistics_delete(id)

    return_json = {"message": message, "status": 200 if "success" in message else 403}
    try:
        return json.dumps(return_json)
    except JSONDecodeError:
        logging.error(f"original json string could not be converted to true json since it probably contains a ' or a \" in the message part: {return_json}")
        return_json = str({"message": f"The {entity_type} could not be deleted.", "status": 500}).replace("'", '"')
        return json.loads(return_json)


@app.route("/user-input", methods=["POST"])
def match_result_from_user_inpt():
    cache.clear()
    user_inputs = request.json["user-inputs"]  # type list

    if len(user_inputs) == 0:
        return {'message': 'No match results were submitted.', 'status': 200}

    response = {'results': []}
    for user_input in user_inputs:
        parsing_response = parse_user_input(user_input)
        response['results'].append({'status': parsing_response.status,
                                    'message': parsing_response.message,
                                    'user_input': parsing_response.user_input,
                                    'parsed_result': parsing_response.parsed_result})

    return json.dumps(response)


@app.route("/export")
def export_data():
    content = {'leagues': [],
               'races': [race.name for race in db.session.query(Race).all()],
               'coaches': [{'first_name': coach.first_name,
                            'last_name': coach.last_name,
                            'display_name': coach.display_name} for coach in db.session.query(Coach).all()]}

    for league in db.session.query(League).all():
        league_json = {'name': league.name,
                       'short_name': league.short_name,
                       'is_selected': league.is_selected,
                       'seasons': []}
        content['leagues'].append(league_json)
        for season in db.session.query(Season).filter_by(league_id=league.id).all():
            season_json = {'name': season.name,
                           'short_name': season.short_name,
                           'is_selected': season.is_selected,
                           "team_short_name_length": season.team_short_name_length,
                           "number_of_allowed_matches": season.number_of_allowed_matches,
                           "number_of_allowed_matches_vs_same_opponent": season.number_of_allowed_matches_vs_same_opponent,
                           "number_of_playoff_places": season.number_of_playoff_places,
                           "term_for_team_names": season.term_for_team_names,
                           "term_for_coaches": season.term_for_coaches,
                           "term_for_races": season.term_for_races,
                           "scorings": [{'touchdown_difference': scoring.touchdown_difference,
                                         'points_scored': scoring.points_scored} for scoring in db.session.query(Scorings).filter_by(season_id=season.id).all()],
                           'teams': [],
                           'matches': [],
                           'additional_statistics': []}
            for team in db.session.query(Team).filter_by(season_id=season.id).all():
                race_name = db.session.query(Race).filter_by(id=team.race_id).first().name
                coach = db.session.query(Coach).filter_by(id=team.coach_id).first()
                team_json = {'name': team.name,
                             'coach_first_name': coach.first_name,
                             'coach_last_name': coach.last_name,
                             'coach_display_name': coach.display_name,
                             'race': race_name,
                             'is_disqualified': team.is_disqualified}
                season_json['teams'].append(team_json)

            for additional_statistics in db.session.query(AdditionalStatistics).filter_by(season_id=season.id).all():
                team_name = db.session.query(Team).filter_by(id=additional_statistics.team_id).first().name
                statistics_json = {'team': team_name, 'casualties': additional_statistics.casualties}
                season_json['additional_statistics'].append(statistics_json)
            for match in db.session.query(BBMatch).filter_by(season_id=season.id).all():
                team_name_1 = db.session.query(Team).filter_by(id=match.team_1_id).first().name
                team_name_2 = db.session.query(Team).filter_by(id=match.team_2_id).first().name
                season_json['matches'].append({
                    'match_number': match.match_number,
                    'team_1': team_name_1,
                    'team_2': team_name_2,
                    'team_1_touchdowns': match.team_1_touchdown,
                    'team_2_touchdowns': match.team_2_touchdown,
                    'team_1_surrendered': match.team_1_surrendered,
                    'team_2_surrendered': match.team_2_surrendered,
                    'is_team_1_victory_by_kickoff': match.is_team_1_victory_by_kickoff,
                    'is_team_2_victory_by_kickoff': match.is_team_2_victory_by_kickoff,
                    'team_1_point_modification': match.team_1_point_modification,
                    'team_2_point_modification': match.team_2_point_modification,
                    'is_playoff_match': match.is_playoff_match,
                    'is_tournament_match': match.is_tournament_match
                })
            league_json['seasons'].append(season_json)
    return json.dumps(content)
