from collections import defaultdict

import numpy as np
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

from database.database import BBMatch, Team, Coach, League, Season, Race, AdditionalStatistics
from table import score_table
from table.score_table import CoachScores
from util import formatting


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


class CoachStatistics:
    class SeasonWithMatch:
        def __init__(self, display_season: str, display_match_list: list[str]):
            self.season = display_season
            self.match_list = display_match_list

    class RaceCountTeam:
        def __init__(self, race: Race):
            self.race = race
            self.team_count = 1
            self.number_of_matches = 0

        def increase_count(self):
            self.team_count += 1

    def __init__(self, coach_name: str, race_count: list[RaceCountTeam], vs_coaches_scores: list[CoachScores], seasons_with_matches: list[SeasonWithMatch]):
        self.coach_name = coach_name
        self.race_count = race_count
        self.vs_coaches_scores = vs_coaches_scores
        self.seasons_with_matches = seasons_with_matches


def determine_statistics(db: SQLAlchemy) -> list:
    def calculate(all_seasons: list, all_matches: list, all_coaches: list, all_teams: list, all_additional_statistics: list, league=None) -> Statistics:
        if league is not None:
            seasons_matcher = [season.league_id == league.id for season in all_seasons]
            all_seasons = all_seasons[seasons_matcher]
            all_seasons_ids = [season.id for season in all_seasons]
            matches_matcher = [match.season_id in all_seasons_ids for match in all_matches]
            all_matches = all_matches[matches_matcher]
            teams_matcher = [team.season_id in all_seasons_ids for team in all_teams]
            all_teams = all_teams[teams_matcher]
            all_coaches = {db.session.query(Coach).filter_by(id=team.coach_id).first() for team in all_teams}
            all_additional_statistics = [additional_statistics for additional_statistics in all_additional_statistics if additional_statistics.season_id in all_seasons_ids]

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
        stats.number_of_casualties = sum([additional_stat.casualties for additional_stat in all_additional_statistics])

        return stats

    all_leagues = np.array(db.session.query(League).all())
    all_seasons = np.array(db.session.query(Season).all())
    all_matches = np.array(db.session.query(BBMatch).all())
    all_coaches = np.array(db.session.query(Coach).all())
    all_teams = np.array(db.session.query(Team).all())
    all_additional_statistics = np.array(db.session.query(AdditionalStatistics).all())

    stats = [calculate(all_seasons, all_matches, all_coaches, all_teams, all_additional_statistics)]
    for league in all_leagues:
        stats.append(calculate(all_seasons, all_matches, all_coaches, all_teams, all_additional_statistics, league=league))

    return stats


def coach_statistics(coach_id: int, db: SQLAlchemy) -> (list, CoachStatistics):
    def calculate_coach_result(matches: list[BBMatch], seasons: dict[int:Season], leagues: dict[int:League]) -> list[CoachStatistics.SeasonWithMatch]:
        coach_results = []
        for match in matches:
            season = seasons[match.season_id]
            league = leagues[season.league_id]
            display_season = f"{league.short_name}: {season.name}"

            season_matches = list(filter(lambda match: match.season_id == season.id, matches))
            season_matches.sort(key=lambda match: match.match_number)
            display_matches = []
            for match in season_matches:
                display_matches.append(formatting.format_match(match, resolve_race_and_id=True))

            if len([result for result in coach_results if result.season == display_season]) == 0:
                coach_results.append(CoachStatistics.SeasonWithMatch(display_season, display_matches))
        coach_results.sort(key=lambda result: result.season)

        return coach_results

    def calculate_race_team_counts(teams: list[Team]) -> list[CoachStatistics.RaceCountTeam]:
        race_id_vs_race_count_team = {}
        for team in teams:
            if team.race_id in race_id_vs_race_count_team:
                race_id_vs_race_count_team[team.race_id].increase_count()
            else:
                race_id_vs_race_count_team[team.race_id] = CoachStatistics.RaceCountTeam(db.session.query(Race).filter_by(id=team.race_id).first())

        sorted_races = list(race_id_vs_race_count_team.values())
        for race_count in sorted_races:
            race_teams = [team.id for team in teams if team.race_id == race_count.race.id]
            match_count = db.session.query(BBMatch) \
                .filter(or_(BBMatch.team_1_id.in_(race_teams), BBMatch.team_2_id.in_(race_teams))) \
                .count()
            race_count.number_of_matches = match_count

        sorted_races.sort(key=lambda race_count: race_count.number_of_matches, reverse=True)

        return sorted_races

    def calculate_vs_coach_scores(matches: list[BBMatch], coach_id: int) -> list[CoachScores]:
        team_ids_vs_coach_vs = {team.id: team.coach_id for team in db.session.query(Team).all()}
        vs_coach_ids = set()
        for match in matches:
            vs_coach_ids.add(team_ids_vs_coach_vs[match.team_1_id])
            vs_coach_ids.add(team_ids_vs_coach_vs[match.team_2_id])

        vs_coach_ids.remove(coach_id)

        vs_coaches_scores = score_table.calculate_coaches_scores(coach_id, vs_coach_ids)

        opponent_scores = list(filter(lambda coach_score: coach_score.coach_id != coach_id, vs_coaches_scores))

        return opponent_scores

    teams = db.session.query(Team) \
        .filter_by(coach_id=coach_id) \
        .all()

    team_ids = [team.id for team in teams]
    season_ids = {team.season_id for team in teams}
    seasons = {season.id: season for season in db.session.query(Season).filter(Season.id.in_(season_ids)).all()}

    all_leagues = db.session.query(League).filter(League.id.in_([season.league_id for season in seasons.values()])).all()
    leagues = {league.id: league for league in all_leagues}

    matches = db.session.query(BBMatch) \
        .filter(or_(BBMatch.team_1_id.in_(team_ids), BBMatch.team_2_id.in_(team_ids))) \
        .all()

    coaches_scores = score_table.calculate_coaches_scores(coach_id)

    coach = db.session.query(Coach).filter_by(id=coach_id).first()
    sorted_races = calculate_race_team_counts(teams)
    vs_coach_scores = calculate_vs_coach_scores(matches, coach_id)
    coach_results = calculate_coach_result(matches, seasons, leagues)

    return coaches_scores, CoachStatistics(formatting.coach_table_name(coach.id), sorted_races, vs_coach_scores, coach_results)
