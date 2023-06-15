import pandas as pd

from database import database
from database.database import db, SeasonRules, Season, Coach, Race, Team, League, BBMatch
from util import formatting


def init_database():
    def init_leagues():
        init_file = pd.read_csv("data/leagues.csv", delimiter=";")
        for league_index, league_data in init_file.iterrows():
            league = League()
            league.name = league_data["name"]
            league.short_name = league_data["short_name"]
            league.is_selected = league_data["is_selected"]
            db.session.add(league)

        db.session.commit()

    def league_id_by_short_name(short_name):
        league = db.session.query(League).filter_by(short_name=short_name).first()
        if league is None:
            raise ValueError(f"League '{short_name}' not found.")
        return league.id

    def season_id_by_short_name(season_short_name: str, league_short_name: str):
        season = db.session.query(Season).filter_by(short_name=season_short_name).filter_by(league_id=league_id_by_short_name(league_short_name)).first()
        if season is None:
            raise ValueError(f"League '{season_short_name}' not found.")
        return season.id

    def init_seasons():
        init_file = pd.read_csv("data/seasons.csv", delimiter=";")
        for season_index, season_data in init_file.iterrows():
            season = Season()
            season.league_id = league_id_by_short_name(season_data["league_short_name"])
            season.name = season_data["name"]
            season.short_name = season_data["short_name"]
            season.is_selected = season_data["is_selected"]
            db.session.add(season)
            db.session.commit()

            season_rules = SeasonRules()
            season_rules.season_id = season.id
            db.session.add(season_rules)
            db.session.commit()

            database.persist_scorings(season_data["scorings"].replace("\\n", "\n"), season.id)

    def init_races():

        init_file = pd.read_csv("data/races.csv", delimiter=";")
        for race_index, race_data in init_file.iterrows():
            race = Race()
            race.name = race_data["name"]

            db.session.add(race)

        db.session.commit()

    def init_teams_and_coaches():
        def race_id_by_name(name: str) -> int:
            race = db.session.query(Race).filter_by(name=name).first()

            if race is None:
                raise ValueError(f"Race '{name}' not found.")
            return race.id

        def coach_id_by_name(first_name: str, last_name: str, display_name: str, league_name: str) -> int:
            league_id = league_id_by_short_name(league_name)
            coach = db.session.query(Coach) \
                .filter_by(first_name=first_name.strip()) \
                .filter_by(last_name=last_name.strip()) \
                .filter_by(display_name=display_name.strip()) \
                .filter_by(league_id=league_id) \
                .first()
            if coach is None:
                coach = Coach()
                coach.first_name = first_name.strip()
                coach.last_name = last_name.strip()
                coach.display_name = display_name.strip()
                coach.league_id = league_id

                db.session.add(coach)
                db.session.commit()

                return coach.id

            return coach.id

        init_file = pd.read_csv("data/teams_and_coaches.csv", delimiter=";")
        for team_index, team_data in init_file.iterrows():
            team = Team()
            team.season_id = season_id_by_short_name(team_data["season_short_name"], team_data["league_short_name"])
            team.name = team_data["name"]
            team.short_name = formatting.generate_team_short_name(team.name)
            team.race_id = race_id_by_name(team_data["race_name"])
            team.coach_id = coach_id_by_name(team_data["coach_first_name"], team_data["coach_last_name"], team_data["coach_display_name"], team_data["league_short_name"])
            team.is_disqualified = False
            db.session.add(team)

        db.session.commit()

    def init_matches():
        def team_id_by_name(team_name: str, season_id: int):
            team = db.session.query(Team).filter_by(name=team_name).filter_by(season_id=season_id).first()
            if team is None:
                raise ValueError(f"Team '{team_name}' not found.")
            return team.id

        init_file = pd.read_csv("data/matches.csv", delimiter=";")
        for team_index, match_data in init_file.iterrows():
            match = BBMatch()
            match.match_number = match_data["match_number"]
            match.season_id = season_id_by_short_name(match_data["season_short_name"], match_data["league_short_name"])
            match.team_1_id = team_id_by_name(match_data["team1"], match.season_id)
            match.team_2_id = team_id_by_name(match_data["team2"], match.season_id)
            match.team_1_touchdown = match_data["td_team_1"]
            match.team_2_touchdown = match_data["td_team_2"]
            match.team_1_point_modification = match_data["point_modification_team_1"]
            match.team_2_point_modification = match_data["point_modification_team_2"]
            match.team_1_surrendered = True if match.team_1_point_modification < 0 else False
            match.team_2_surrendered = True if match.team_2_point_modification < 0 else False
            match.is_playoff_match = True if match_data["is_playoff_match"] == 1 else False
            match.is_tournament_match = True if match_data["is_tournament_match"] == 1 else False
            db.session.add(match)
        db.session.commit()

    if db.session.query(League).count() == 0:
        init_leagues()
        init_seasons()
        init_races()
        init_teams_and_coaches()
        init_matches()
