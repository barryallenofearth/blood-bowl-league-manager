import logging
from operator import itemgetter

from sqlalchemy.orm import Query

from database import database
from database.database import db, BBMatch, Team, Race, Coach, Scorings, Season
from util import formatting
from sqlalchemy import or_


class BaseScores:
    def __init__(self, number_of_scorings: int, place=1, number_of_matches=0, td_received=0, td_made=0, td_diff=0,
                 points=0):
        self.place = place
        self.number_of_matches = number_of_matches
        self.match_result_counts = [0 for _ in range(number_of_scorings)]
        self.td_received = td_received
        self.td_made = td_made
        self.td_diff = td_diff
        self.points = points


def __repr__(self):
    return f"place: {self.place}, number_of_matches:{self.number_of_matches},match_result_counts:{self.match_result_counts},td_received:{self.td_received},td_made:{self.td_made},td_diff:{self.td_diff},points:{self.points}>\n"


class TeamScores(BaseScores):
    def __init__(self, team: Team, number_of_scorings: int, place=1, number_of_matches=0, td_received=0, td_made=0,
                 td_diff=0, points=0):
        super().__init__(number_of_scorings, place, number_of_matches, td_received, td_made, td_diff, points)
        self.team_short_name = team.short_name
        self.race = db.session.query(Race).filter_by(id=team.race_id).first().name
        self.coach = formatting.coach_table_name(team.coach_id)

    def __repr__(self):
        return f"TeamResults<place: team_short_name:{self.team_short_name}, race:{self.race}, coach:{self.coach}, " + super().__repr__()


class SeasonStatistics:

    def __init__(self, number_of_teams: int, number_of_coaches: int, number_of_matches: int):
        self.number_of_teams = number_of_teams
        self.number_of_coaches = number_of_coaches
        self.number_of_matches = number_of_matches


class CoachScores(BaseScores):
    def __init__(self, coach: Coach, number_of_teams: int, number_of_seasons: int, number_of_playoff_matches: int,
                 number_of_scorings: int, place=1, number_of_matches=0, td_received=0, td_made=0, td_diff=0, points=0):
        super().__init__(number_of_scorings, place, number_of_matches, td_received, td_made, td_diff, points)
        self.coach = formatting.coach_table_name(coach.id, season_id=0)
        self.coach_id = coach.id
        self.number_of_teams = number_of_teams
        self.number_of_seasons = number_of_seasons
        self.number_of_playoff_matches = number_of_playoff_matches
        self.win_loss_diff = 0
        self.number_of_matches_per_team = 0

    def __repr__(self):
        return f"CoachResults<place: coach:{self.coach}, " + super().__repr__()


class RaceScores(BaseScores):
    def __init__(self, race: Race, number_of_teams: int, number_of_seasons: int, number_of_playoff_matches: int,
                 number_of_scorings: int, place=1, number_of_matches=0, td_received=0, td_made=0, td_diff=0, points=0):
        super().__init__(number_of_scorings, place, number_of_matches, td_received, td_made, td_diff, points)
        self.race = race.name
        self.number_of_teams = number_of_teams
        self.number_of_seasons = number_of_seasons
        self.number_of_playoff_matches = number_of_playoff_matches
        self.win_loss_diff = 0
        self.number_of_matches_per_team = 0

    def __repr__(self):
        return f"RaceResults<place: race:{self.race}, " + super().__repr__()


def __calculate_scores(results: dict, scorings: list, season_id: int, entity_id_from_team_id_getter, coach_id=0, vs_coach_ids=None, league_id=0) -> dict[int:list]:
    def modify_team_score(analysis_results: dict, entity_id: int, td_made: int, td_received: int,
                          points_modification: int, scorings: list, is_team_1_victory_by_kickoff: bool, is_team_2_victory_by_kickoff: bool):
        def determine_points(td_diff: int, is_team_1_victory_by_kickoff: bool, is_team_2_victory_by_kickoff: bool) -> int:
            def increment_match_results_count(index: int):
                analysis_scoring.match_result_counts[len(scorings) - 1 - index] = analysis_scoring.match_result_counts[len(scorings) - 1 - index] + 1

            if is_team_1_victory_by_kickoff:
                increment_match_results_count(len(scorings) - 1)
                return scorings[-1].points_scored

            if is_team_2_victory_by_kickoff:
                increment_match_results_count(0)
                return scorings[0].points_scored

            if td_diff <= scorings[0].touchdown_difference:
                increment_match_results_count(0)
                return scorings[0].points_scored
            elif scorings[-1].touchdown_difference <= td_diff:
                increment_match_results_count(len(scorings) - 1)
                return scorings[-1].points_scored

            for index in range(1, len(scorings) - 1):
                if scorings[index].touchdown_difference == td_diff:
                    increment_match_results_count(index)
                    return scorings[index].points_scored
            raise ValueError(f"No points entry found for points difference {td_diff}")

        if entity_id not in analysis_results:
            return
        analysis_scoring = analysis_results[entity_id]
        analysis_scoring.number_of_matches = analysis_scoring.number_of_matches + 1
        analysis_scoring.td_made = analysis_scoring.td_made + td_made
        analysis_scoring.td_received = analysis_scoring.td_received + td_received
        td_diff = td_made - td_received
        analysis_scoring.td_diff = analysis_scoring.td_diff + td_diff
        analysis_scoring.points = analysis_scoring.points + points_modification + determine_points(td_diff, is_team_1_victory_by_kickoff, is_team_2_victory_by_kickoff)

    if len(results) == 0:
        return {}

    is_teams_table = type(next(iter(results.values()))) == TeamScores

    if season_id != 0:
        season = db.session.query(Season).filter_by(id=season_id).first()
    else:
        season = db.session.query(Season).first()

    if league_id != 0:
        all_season_ids = [season.id for season in db.session.query(Season).all() if season.league_id == league_id]
    else:
        all_season_ids = [season.id for season in db.session.query(Season).all()]

    query: Query
    if coach_id == 0 or vs_coach_ids is None:
        if season_id != 0:
            query = db.session.query(BBMatch).filter_by(season_id=season_id)
        else:
            query = db.session.query(BBMatch)
    else:
        coaches_teams_query = db.session.query(Team).filter_by(coach_id=coach_id)
        if league_id != 0:
            coaches_teams_query = coaches_teams_query.filter(Team.season_id.in_(all_season_ids))

        coaches_teams = coaches_teams_query.all()

        team_ids = [team.id for team in coaches_teams]
        vs_coaches_teams = db.session.query(Team).filter(Team.coach_id.in_(vs_coach_ids)).all()
        vs_coach_team_ids = [team.id for team in vs_coaches_teams]
        query = (db.session.query(BBMatch)
                 .filter(or_(BBMatch.team_1_id.in_(team_ids), BBMatch.team_2_id.in_(team_ids)))
                 .filter(or_(BBMatch.team_1_id.in_(vs_coach_team_ids), BBMatch.team_2_id.in_(vs_coach_team_ids))))
        if season_id != 0:
            query = query.filter_by(season_id=season_id)

    if league_id != 0:
        query = query.filter(BBMatch.season_id.in_(all_season_ids))

    matches = query.order_by(BBMatch.match_number).all()

    skip_team_1_result = False
    skip_team_2_result = False
    for match in matches:
        if is_teams_table and season_id > 0:
            if match.is_playoff_match:
                continue

            skip_team_1_result = match.is_tournament_match and results[entity_id_from_team_id_getter(match.team_1_id)].number_of_matches == season.number_of_allowed_matches
            skip_team_2_result = match.is_tournament_match and results[entity_id_from_team_id_getter(match.team_2_id)].number_of_matches == season.number_of_allowed_matches

        if not skip_team_1_result:
            modify_team_score(results, entity_id_from_team_id_getter(match.team_1_id), match.team_1_touchdown,
                              match.team_2_touchdown, match.team_1_point_modification, scorings, match.is_team_1_victory_by_kickoff, match.is_team_2_victory_by_kickoff)
        if not skip_team_2_result:
            modify_team_score(results, entity_id_from_team_id_getter(match.team_2_id), match.team_2_touchdown,
                              match.team_1_touchdown, match.team_2_point_modification, scorings, match.is_team_2_victory_by_kickoff, match.is_team_1_victory_by_kickoff)

    return results


def determine_placings(sorted_results: list, show_vs_table=False):
    if len(sorted_results) == 0:
        return []
    points_previous = sorted_results[0].points
    td_diff_previous = sorted_results[0].td_diff
    td_made_previous = sorted_results[0].td_made
    place_previous = sorted_results[0].place
    for index in range(1, len(sorted_results)):
        if show_vs_table:
            if points_previous < sorted_results[index].points or td_diff_previous < sorted_results[index].td_diff or td_made_previous < sorted_results[index].td_made:
                sorted_results[index].place = place_previous + 1
            else:
                sorted_results[index].place = place_previous

        else:
            if points_previous > sorted_results[index].points or td_diff_previous > sorted_results[index].td_diff or td_made_previous > sorted_results[index].td_made:
                sorted_results[index].place = place_previous + 1
            else:
                sorted_results[index].place = place_previous

        points_previous = sorted_results[index].points
        td_diff_previous = sorted_results[index].td_diff
        td_made_previous = sorted_results[index].td_made
        place_previous = sorted_results[index].place


def calculate_team_scores() -> list[TeamScores]:
    def team_id_getter(team_id: int):
        return team_id

    def alphabetic_sorter(team_scores: TeamScores):
        return team_scores.team_short_name

    season = database.get_selected_season()
    teams = db.session.query(Team).filter_by(season_id=season.id).all()

    scorings = db.session.query(Scorings).filter_by(season_id=season.id).order_by(Scorings.touchdown_difference).all()
    team_results = {team.id: TeamScores(team=team, number_of_scorings=len(scorings)) for team in teams if not team.is_disqualified}
    results = __calculate_scores(team_results, scorings, season.id, team_id_getter)
    sorted_results = sorted([result for result in results.values() if result.number_of_matches > 0],
                            key=lambda result: (
                                -result.points, -result.td_diff, -result.td_made, -result.number_of_matches,
                                alphabetic_sorter(result)))
    sorted_results = sorted_results + sorted([result for result in results.values() if result.number_of_matches == 0],
                                             key=lambda result: alphabetic_sorter(result))
    determine_placings(sorted_results)

    return sorted_results


def generate_scorings():
    scorings = []
    for td_diff in range(-1, 2):
        scoring = Scorings()
        scoring.touchdown_difference = td_diff
        scoring.points_scored = td_diff
        scorings.append(scoring)
    return scorings


def calculate_coaches_scores(coach_id=None, vs_coach_ids=None, league_id=0) -> list[CoachScores]:
    def get_teams(coach_id: int, season_ids=[], league_id=0):
        query = db.session.query(Team)
        if coach_id is not None:
            query = query.filter_by(coach_id=coach_id)
        if league_id != 0:
            query = query.filter(Team.season_id.in_(season_ids))
        return query.all()

    def coach_id_getter(team_id: int):
        return db.session.query(Team).filter_by(id=team_id).first().coach_id

    def alphabetic_sorter(coach_scores: CoachScores):
        return coach_scores.coach

    def number_of_seasons(coach_id: int, season_ids=[], league_id=0) -> int:
        team_ids = [team.id for team in get_teams(coach_id, season_ids, league_id)]
        return len({match.season_id for match in db.session.query(BBMatch).filter(or_(BBMatch.team_1_id.in_(team_ids), BBMatch.team_2_id.in_(team_ids))).all()})

    def number_of_playoff_matches(coach_id: int, season_ids=[], league_id=0) -> int:
        team_ids = [team.id for team in get_teams(coach_id, season_ids, league_id)]
        return db.session.query(BBMatch).filter_by(is_playoff_match=True).filter(or_(BBMatch.team_1_id.in_(team_ids), BBMatch.team_2_id.in_(team_ids))).count()

    logging.info("calculate coaches scores")
    if coach_id is None and vs_coach_ids is None:
        coaches = db.session.query(Coach).all()
    elif coach_id is not None and vs_coach_ids is not None:
        coaches = db.session.query(Coach).filter(or_(Coach.id == coach_id, Coach.id.in_(vs_coach_ids))).all()
    else:
        coaches = db.session.query(Coach).filter_by(id=coach_id).all()

    logging.info("coaches identified by teams")
    scorings = generate_scorings()

    if league_id != 0:
        all_season_ids = [season.id for season in db.session.query(Season).all() if season.league_id == league_id]
    else:
        all_season_ids = [season.id for season in db.session.query(Season).all()]

    coach_results = {coach.id: CoachScores(coach=coach,
                                           number_of_teams=len(get_teams(coach.id, all_season_ids, league_id)),
                                           number_of_seasons=number_of_seasons(coach.id, all_season_ids, league_id),
                                           number_of_playoff_matches=number_of_playoff_matches(coach.id, all_season_ids, league_id),
                                           number_of_scorings=len(scorings))
                     for coach in coaches}
    results = __calculate_scores(coach_results, scorings, 0, coach_id_getter, coach_id=coach_id, vs_coach_ids=vs_coach_ids, league_id=league_id)
    for result in results.values():
        result.win_loss_diff = result.match_result_counts[0] - result.match_result_counts[-1]
        result.points = result.win_loss_diff
        if result.number_of_teams > 0:
            result.number_of_matches_per_team = result.number_of_matches / result.number_of_teams

    if coach_id is None and vs_coach_ids is None:
        sorted_results = sorted([result for result in results.values() if result.number_of_matches > 0],
                                key=lambda result: (-result.win_loss_diff, -result.td_diff, -result.td_made, -result.number_of_matches, alphabetic_sorter(result)))
    else:

        if coach_id is not None and vs_coach_ids is not None:
            filtered_results = filter(lambda result: result.coach_id != coach_id, results.values())
        else:
            filtered_results = results.values()

        sorted_results = sorted([result for result in filtered_results if result.number_of_matches > 0],
                                key=lambda result: (result.win_loss_diff, result.td_diff, -result.td_made, -result.number_of_matches, alphabetic_sorter(result)))

    determine_placings(sorted_results, coach_id != 0 and vs_coach_ids and not None)

    return sorted_results


def calculate_races_scores(league_id=0) -> list[RaceScores]:
    def get_teams(race_id: int, season_ids=[], league_id=0):
        query = db.session.query(Team)
        if race_id is not None:
            query = query.filter_by(race_id=race_id)
        if league_id != 0:
            query = query.filter(Team.season_id.in_(season_ids))
        return query.all()

    def race_id_getter(team_id: int):
        return db.session.query(Team).filter_by(id=team_id).first().race_id

    def alphabetic_sorter(race_scores: RaceScores):
        return race_scores.race

    def number_of_seasons(race_id: int, season_ids=[], league_id=0) -> int:
        return len({team.season_id for team in get_teams(race_id, season_ids, league_id)})

    def number_of_playoff_matches(race_id: int, season_ids=[], league_id=0) -> int:
        team_ids = [team.id for team in get_teams(race_id, season_ids, league_id)]
        return db.session.query(BBMatch).filter_by(is_playoff_match=True).filter(or_(BBMatch.team_1_id.in_(team_ids), BBMatch.team_2_id.in_(team_ids))).count()

    races = db.session.query(Race).all()
    if league_id != 0:
        all_season_ids = [season.id for season in db.session.query(Season).all() if season.league_id == league_id]
    else:
        all_season_ids = [season.id for season in db.session.query(Season).all()]

    scorings = generate_scorings()
    race_results = {
        race.id: RaceScores(race=race,
                            number_of_teams=len(get_teams(race.id, season_ids=all_season_ids, league_id=league_id)),
                            number_of_scorings=len(scorings),
                            number_of_seasons=number_of_seasons(race.id, season_ids=all_season_ids, league_id=league_id),
                            number_of_playoff_matches=number_of_playoff_matches(race.id, season_ids=all_season_ids, league_id=league_id)) for race in races}

    results = __calculate_scores(race_results, scorings, 0, race_id_getter, league_id=league_id)

    for result in results.values():
        result.win_loss_diff = result.match_result_counts[0] - result.match_result_counts[-1]
        result.points = result.win_loss_diff
        if result.number_of_teams > 0:
            result.number_of_matches_per_team = result.number_of_matches / result.number_of_teams

    sorted_results = sorted([result for result in results.values() if result.number_of_matches > 0],
                            key=lambda result: (-result.win_loss_diff, -result.td_diff, -result.td_made, -result.number_of_matches, alphabetic_sorter(result)))
    determine_placings(sorted_results)

    return sorted_results
