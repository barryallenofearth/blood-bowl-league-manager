from flask_sqlalchemy import SQLAlchemy
import pandas as pd

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
    league_id = db.Column(db.Integer, db.ForeignKey(f'{League.__tablename__}.id'))
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    display_name = db.Column(db.String, nullable=True)

    def __str__(self):
        string = f"{self.first_name} {self.last_name}"
        if self.display_name is not None and self.display_name != "":
            string += f" ({self.display_name})"
        return string


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
    team_1_point_modification = db.Column(db.Integer, nullable=True)
    team_2_point_modification = db.Column(db.Integer, nullable=True)
    is_playoff_match = db.Column(db.Boolean)
    is_tournament = db.Column(db.Boolean)

    def __str__(self):
        team1_name = db.session.query(Team).filter_by(self.team_1_id).first().name
        team2_name = db.session.query(Team).filter_by(self.team_2_id).first().name

        string = f"{team1_name} vs. {team2_name} : {self.team_1_touchdown}:{self.team_2_touchdown}"
        if self.team_1_surrendered:
            string += f" ({team1_name} surrendered)"
        if self.team_2_surrendered:
            string += f" ({team2_name} surrendered)"
        if self.team_1_point_modification is not None and self.team_1_point_modification != 0:
            string += f" ({self.team_1_point_modification} points for {team1_name})"
        if self.team_2_point_modification is not None and self.team_2_point_modification != 0:
            string += f" ({self.team_2_point_modification} points for {team2_name})"
        if self.is_playoff_match:
            string += " (Playoffs)"
        if self.is_tournament:
            string += " (Tournament)"



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
    __tablename__ = "scorings"

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey(f'{Season.__tablename__}.id'))
    touchdown_difference = db.Column(db.Integer, nullable=False)
    points_scored = db.Column(db.Integer, nullable=False)


def get_selected_league() -> League:
    return db.session.query(League).filter_by(is_selected=True).first()


def get_selected_season() -> Season:
    selected_league = get_selected_league()
    return db.session.query(Season).filter_by(league_id=selected_league.id).filter_by(is_selected=True).first()


def init_database():
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

            season_rules = SeasonRules()
            season_rules.season_id = season.id
            db.session.add(season_rules)
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
