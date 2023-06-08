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
    title = db.Column(db.String, nullable=False, unique=True)
    short_name = db.Column(db.String, nullable=False, unique=True)
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
    league_id = db.Column(db.Integer, db.ForeignKey(f'{League.__tablename__}.id'))
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
    league_id = db.Column(db.Integer, db.ForeignKey(f'{League.__tablename__}.id'))
    team_1_id = db.Column(db.Integer, db.ForeignKey(f'{Team.__tablename__}.id'), nullable=False)
    team_2_id = db.Column(db.Integer, db.ForeignKey(f'{Team.__tablename__}.id'), nullable=False)
    team_1_touchdown = db.Column(db.Integer, nullable=False)
    team_2_touchdown = db.Column(db.Integer, nullable=False)
    team_1_surrendered = db.Column(db.Boolean, nullable=True)
    team_2_surrendered = db.Column(db.Boolean, nullable=True)
    is_playoff_match = db.Column(db.Boolean)
    is_tournament = db.Column(db.Boolean)


class SeasonRules(db.Model):
    __tablename__ = "season_rules"

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey(f'{Season.__tablename__}.id'))
    team_short_name_length = db.Column(db.Integer, nullable=True)
    number_of_allowed_matches = db.Column(db.Integer, nullable=True)
    number_of_allowed_matches_vs_same_opponent = db.Column(db.Integer, nullable=True)
    number_of_playoff_places = db.Column(db.Integer, nullable=True)
    playoff_highlight_color = db.Column(db.String, nullable=True)
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
    __tablename__ = "scorings"

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey(f'{Season.__tablename__}.id'))
    touchdown_difference = db.Column(db.Integer, nullable=False)
    points_scored = db.Column(db.Integer, nullable=False)
