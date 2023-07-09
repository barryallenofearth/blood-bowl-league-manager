from collections import defaultdict

import numpy as np
from flask_sqlalchemy import SQLAlchemy
from numpy.ma import array

from database.database import BBMatch, Team, Coach, League, Season


class Statistics:

    def __init__(self):
        self.title = ""
        self.number_of_matches = 0
        self.number_of_non_playoff_matches = 0
        self.number_of_seasons = 0
        self.longest_season = ""
        self.average_number_of_games_per_season = 0
        self.number_of_teams = 0
        self.number_of_coaches = 0


def determine_statistics(db: SQLAlchemy) -> list:
    def calculate(all_seasons: list, all_matches: list, all_coaches: list, all_teams: list, league=None) -> Statistics:
        if league is not None:
            seasons_matcher = [season.league_id == league.id for season in all_seasons]
            all_seasons = all_seasons[seasons_matcher]
            all_seasons_ids = [season.id for season in all_seasons]
            matches_matcher = [match.season_id in all_seasons_ids for match in all_matches]
            all_matches = all_matches[matches_matcher]
            teams_matcher = [team.season_id in all_seasons_ids for team in all_teams]
            all_teams = all_teams[teams_matcher]
            all_coaches = {db.session.query(Coach).filter_by(id=team.coach_id).first() for team in all_teams}

        stats = Statistics()
        if league is None:
            stats.title = "All leagues"
        else:
            stats.title = league.short_name

        stats.number_of_matches = len(all_matches)
        stats.number_of_non_playoff_matches = len(all_matches[[not match.is_playoff_match for match in all_matches]])
        stats.number_of_seasons = len(all_seasons)

        matches_per_season = defaultdict(lambda: 0)
        for match in all_matches:
            if not match.is_playoff_match:
                matches_per_season[match.season_id] = matches_per_season[match.season_id] + 1

        max_number_of_matches = 0
        max_game_count_season_id = 0
        for season_id, match_count in matches_per_season.items():
            if max_number_of_matches < match_count:
                max_number_of_matches = match_count
                max_game_count_season_id = season_id

        max_season = all_seasons[[season.id == max_game_count_season_id for season in all_seasons]][0]
        if league is None:
            league = db.session.query(League).filter_by(id=max_season.league_id).first()
            stats.longest_season = f"{max_number_of_matches} ({league.short_name} | {max_season.short_name}) "
        else:
            stats.longest_season = f"{max_number_of_matches} ({max_season.short_name})"

        stats.average_number_of_games_per_season = np.average([match_count for match_count in matches_per_season.values()])
        stats.number_of_teams = len(all_teams)
        stats.number_of_coaches = len(all_coaches)

        return stats

    all_leagues = np.array(db.session.query(League).all())
    all_seasons = np.array(db.session.query(Season).all())
    all_matches = np.array(db.session.query(BBMatch).all())
    all_coaches = np.array(db.session.query(Coach).all())
    all_teams = np.array(db.session.query(Team).all())

    stats = [calculate(all_seasons, all_matches, all_coaches, all_teams)]
    for league in all_leagues:
        stats.append(calculate(all_seasons, all_matches, all_coaches, all_teams, league=league))

    return stats
