from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class League(db.Model):
    __tablename__ = "league"

    # store logo on disk not in database
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    short_name = db.Column(db.String, nullable=False, unique=True)
    is_selected = db.Column(db.Boolean, nullable=False)

    def __init__(self):
        self.is_selected = False


class Season(db.Model):
    __tablename__ = "season"

    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey(f'{League.__tablename__}.id'))
    name = db.Column(db.String, nullable=False)
    short_name = db.Column(db.String, nullable=False)
    is_selected = db.Column(db.Boolean, nullable=False)

    def __init__(self):
        self.is_selected = False


class Race(db.Model):
    __tablename__ = "race"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)


class Coach(db.Model):
    __tablename__ = "coach"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    display_name = db.Column(db.String, nullable=True)


class Team(db.Model):
    __tablename__ = "team"
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey(f'{Season.__tablename__}.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey(f'{Coach.__tablename__}.id'), nullable=False)
    race_id = db.Column(db.Integer, db.ForeignKey(f'{Race.__tablename__}.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    short_name = db.Column(db.String, nullable=False)
    is_disqualified = db.Column(db.Boolean, nullable=False)

    def __init__(self):
        self.is_disqualified = False


class BBMatch(db.Model):
    __tablename__ = "bb_match"
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey(f'{Season.__tablename__}.id'))
    match_number = db.Column(db.Integer, nullable=False)
    team_1_id = db.Column(db.Integer, db.ForeignKey(f'{Team.__tablename__}.id'), nullable=False)
    team_2_id = db.Column(db.Integer, db.ForeignKey(f'{Team.__tablename__}.id'), nullable=False)
    team_1_touchdown = db.Column(db.Integer, nullable=False)
    team_2_touchdown = db.Column(db.Integer, nullable=False)
    team_1_surrendered = db.Column(db.Boolean, nullable=True)
    team_2_surrendered = db.Column(db.Boolean, nullable=True)
    is_team_1_victory_by_kickoff = db.Column(db.Boolean, nullable=True)
    is_team_2_victory_by_kickoff = db.Column(db.Boolean, nullable=True)
    team_1_point_modification = db.Column(db.Integer, nullable=True)
    team_2_point_modification = db.Column(db.Integer, nullable=True)
    is_playoff_match = db.Column(db.Boolean)
    is_tournament_match = db.Column(db.Boolean)


class SeasonRules(db.Model):
    __tablename__ = "season_rules"

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey(f'{Season.__tablename__}.id'))
    team_short_name_length = db.Column(db.Integer, nullable=True)
    number_of_allowed_matches = db.Column(db.Integer, nullable=True)
    number_of_allowed_matches_vs_same_opponent = db.Column(db.Integer, nullable=True)
    number_of_playoff_places = db.Column(db.Integer, nullable=True)
    term_for_team_names = db.Column(db.String, nullable=False)
    term_for_coaches = db.Column(db.String, nullable=False)
    term_for_races = db.Column(db.String, nullable=False)

    def __init__(self):
        self.team_short_name_length = 30
        self.number_of_allowed_matches = 8
        self.number_of_allowed_matches_vs_same_opponent = 2
        self.number_of_playoff_places = 8
        self.term_for_team_names = "Name"
        self.term_for_coaches = "Trainer"
        self.term_for_races = "Team"


class Scorings(db.Model):
    DEFAULT_SCORINGS_ENTRY = "-1: 0\n0:1\n1:3"

    __tablename__ = "scorings"

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey(f'{Season.__tablename__}.id'))
    touchdown_difference = db.Column(db.Integer, nullable=False)
    points_scored = db.Column(db.Integer, nullable=False)


class AdditionalStatistics(db.Model):
    __tablename__ = "additional_statistics"

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey(f'{Season.__tablename__}.id'))
    team_id = db.Column(db.Integer, db.ForeignKey(f'{Team.__tablename__}.id'), nullable=False)
    casualties = db.Column(db.Integer, nullable=False)


def get_selected_league() -> League:
    return db.session.query(League).filter_by(is_selected=True).first()


def get_selected_season() -> Season:
    selected_league = get_selected_league()
    return db.session.query(Season).filter_by(league_id=selected_league.id).filter_by(is_selected=True).first()


def persist_scorings(user_input: str, season_id: int):
    if season_id == 0:
        season_id = get_selected_season().id

    for scoring in db.session.query(Scorings).filter_by(season_id=season_id).all():
        db.session.delete(scoring)

    scorings_lines = user_input.strip().split("\n")

    for scoring_line in scorings_lines:
        if ":" not in scoring_line:
            continue
        line_split = scoring_line.split(":")

        scoring = Scorings()
        scoring.season_id = season_id
        scoring.touchdown_difference = int(line_split[0].strip())
        scoring.points_scored = int(line_split[1].strip())
        db.session.add(scoring)

    db.session.commit()


def highest_match_number() -> int:
    season = get_selected_season()

    highest_number_match = db.session.query(BBMatch).filter_by(season_id=season.id).order_by(BBMatch.match_number.desc()).first()
    if highest_number_match is None:
        return 0

    return highest_number_match.match_number
