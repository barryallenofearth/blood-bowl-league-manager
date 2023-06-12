import pandas as pd

from database import database
from database.database import db, SeasonRules, Season, Coach, Race, Team, League
from util import formatting


def init_database():
    def init_leagues():
        init_file = pd.read_csv("data/leagues.csv", delimiter=";")
        for league_index, league_data in init_file.iterrows():
            league = League()
            league.id = league_data["id"]
            league.name = league_data["name"]
            league.short_name = league_data["short_name"]
            league.is_selected = league_data["is_selected"]
            db.session.add(league)

        db.session.commit()

    def init_seasons():
        init_file = pd.read_csv("data/seasons.csv", delimiter=";")
        for season_index, season_data in init_file.iterrows():
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

            database.persist_scorings(season_data["scorings"].replace("\\n", "\n"), season.id)

    def init_races():

        init_file = pd.read_csv("data/races.csv", delimiter=";")
        for race_index, race_data in init_file.iterrows():
            race = Race()
            race.id = race_data["id"]
            race.name = race_data["name"]

            db.session.add(race)

        db.session.commit()

    def init_coaches():
        init_file = pd.read_csv("data/coaches.csv", delimiter=";")
        for coach_index, coach_data in init_file.iterrows():
            coach = Coach()
            coach.id = coach_data["id"]
            coach.league_id = coach_data["league_id"]
            coach.first_name = coach_data["first_name"]
            coach.last_name = coach_data["last_name"]
            coach.display_name = coach_data["display_name"]
            db.session.add(coach)

        db.session.commit()

    def init_teams():
        init_file = pd.read_csv("data/teams.csv", delimiter=";")
        for team_index, team_data in init_file.iterrows():
            team = Team()
            team.id = team_data["id"]
            team.season_id = team_data["season_id"]
            team.name = team_data["name"]
            team.short_name = formatting.generate_team_short_name(team.name)
            team.race_id = team_data["race_id"]
            team.coach_id = team_data["coach_id"]
            team.is_disqualified = False
            db.session.add(team)

        db.session.commit()

    if db.session.query(League).count() == 0:
        init_leagues()
        init_seasons()
        init_races()
        init_coaches()
        init_teams()
