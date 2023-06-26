from operator import itemgetter

from database import database
from database.database import db, BBMatch, Team, Race, Coach, Scorings, SeasonRules
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


class CoachScores(BaseScores):
    def __init__(self, coach: Coach, number_of_teams: int, number_of_seasons: int, number_of_playoff_matches: int,
                 number_of_scorings: int, place=1, number_of_matches=0, td_received=0, td_made=0, td_diff=0, points=0):
        super().__init__(number_of_scorings, place, number_of_matches, td_received, td_made, td_diff, points)
        self.coach = formatting.coach_table_name(coach.id, season_id=0)
        self.number_of_teams = number_of_teams
        self.number_of_seasons = number_of_seasons
        self.number_of_playoff_matches = number_of_playoff_matches
        self.win_loss_diff = 0

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

    def __repr__(self):
        return f"RaceResults<place: race:{self.race}, " + super().__repr__()


def __calculate_scores(results: dict, scorings: list, season_id: int, entity_id_from_team_id_getter) -> dict:
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

    season_rules = db.session.query(SeasonRules).filter_by(season_id=season_id).first()
    query = db.session.query(BBMatch)
    if season_id != 0:
        query = query.filter_by(season_id=season_id)
    matches = query.order_by(BBMatch.match_number).all()

    skip_team_1_result = False
    skip_team_2_result = False
    for match in matches:
        if is_teams_table and season_id > 0:
            if match.is_playoff_match:
                continue

            skip_team_1_result = match.is_tournament_match and results[entity_id_from_team_id_getter(match.team_1_id)].number_of_matches == season_rules.number_of_allowed_matches
            skip_team_2_result = match.is_tournament_match and results[entity_id_from_team_id_getter(match.team_2_id)].number_of_matches == season_rules.number_of_allowed_matches

        if not skip_team_1_result:
            modify_team_score(results, entity_id_from_team_id_getter(match.team_1_id), match.team_1_touchdown,
                              match.team_2_touchdown, match.team_1_point_modification, scorings, match.is_team_1_victory_by_kickoff, match.is_team_2_victory_by_kickoff)
        if not skip_team_2_result:
            modify_team_score(results, entity_id_from_team_id_getter(match.team_2_id), match.team_2_touchdown,
                              match.team_1_touchdown, match.team_2_point_modification, scorings, match.is_team_2_victory_by_kickoff, match.is_team_1_victory_by_kickoff)

    return results


def determine_placings(sorted_results: list):
    points_previous = sorted_results[0].points
    td_diff_previous = sorted_results[0].td_diff
    td_made_previous = sorted_results[0].td_made
    place_previous = sorted_results[0].place
    for index in range(1, len(sorted_results)):
        if points_previous > sorted_results[index].points or td_diff_previous > sorted_results[
            index].td_diff or td_made_previous > sorted_results[index].td_made:
            sorted_results[index].place = place_previous + 1
        else:
            sorted_results[index].place = place_previous

        points_previous = sorted_results[index].points
        td_diff_previous = sorted_results[index].td_diff
        td_made_previous = sorted_results[index].td_made
        place_previous = sorted_results[index].place


def calculate_team_scores():
    def team_id_getter(team_id: int):
        return team_id

    def alphabetic_sorter(team_scores: TeamScores):
        return team_scores.team_short_name

    season = database.get_selected_season()
    teams = db.session.query(Team).filter_by(season_id=season.id).all()

    scorings = db.session.query(Scorings).filter_by(season_id=season.id).order_by(Scorings.touchdown_difference).all()
    team_results = {team.id: TeamScores(team=team, number_of_scorings=len(scorings)) for team in teams}
    results = __calculate_scores(team_results, scorings, season.id, team_id_getter)
    sorted_results = sorted([result for result in results.values() if result.number_of_matches > 0],
                            key=lambda result: (
                                -result.points, -result.td_diff, -result.td_made, -result.number_of_matches,
                                alphabetic_sorter(result)))
    sorted_results = sorted_results + sorted([result for result in results.values() if result.number_of_matches == 0],
                                             key=lambda result: alphabetic_sorter(result))
    determine_placings(sorted_results)

    return sorted_results


def winning_scorings():
    scorings = []
    for td_diff in range(-1, 2):
        scoring = Scorings()
        scoring.touchdown_difference = td_diff
        scoring.points_scored = td_diff
        scorings.append(scoring)

    return scorings


def calculate_coaches_scores():
    def coach_id_getter(team_id: int):
        return db.session.query(Team).filter_by(id=team_id).first().coach_id

    def alphabetic_sorter(coach_scores: CoachScores):
        return coach_scores.coach

    def number_of_seasons(coach_id: int) -> int:
        team_ids = [team.id for team in db.session.query(Team).filter_by(coach_id=coach_id).all()]
        return len({match.season_id for match in db.session.query(BBMatch).filter(or_(BBMatch.team_1_id.in_(team_ids), BBMatch.team_2_id.in_(team_ids))).all()})

    def number_of_playoff_matches(coach_id: int) -> int:
        team_ids = [team.id for team in db.session.query(Team).filter_by(coach_id=coach_id).all()]
        return db.session.query(BBMatch).filter_by(is_playoff_match=True).filter(or_(BBMatch.team_1_id.in_(team_ids), BBMatch.team_2_id.in_(team_ids))).count()

    print("calculate coaches scores")
    coaches = db.session.query(Coach).all()

    print("coaches identified by teams")
    scorings = winning_scorings()
    coach_results = {coach.id: CoachScores(coach=coach,
                                           number_of_teams=db.session.query(Team).filter_by(coach_id=coach.id).count(),
                                           number_of_seasons=number_of_seasons(coach.id),
                                           number_of_playoff_matches=number_of_playoff_matches(coach.id),
                                           number_of_scorings=len(scorings))
                     for coach in coaches}
    results = __calculate_scores(coach_results, scorings, 0, coach_id_getter)
    for result in results.values():
        result.win_loss_diff = result.match_result_counts[0] - result.match_result_counts[-1]
    sorted_results = sorted([result for result in results.values() if result.number_of_matches > 0],
                            key=lambda result: (-result.win_loss_diff, -result.td_diff, -result.td_made, -result.number_of_matches, alphabetic_sorter(result)))
    determine_placings(sorted_results)

    return sorted_results


def calculate_races_scores():
    def race_id_getter(team_id: int):
        return db.session.query(Team).filter_by(id=team_id).first().race_id

    def alphabetic_sorter(race_scores: RaceScores):
        return race_scores.race

    def number_of_seasons(race_id: int) -> int:
        return len({team.season_id for team in db.session.query(Team).filter_by(race_id=race_id).all()})

    def number_of_playoff_matches(race_id: int) -> int:
        team_ids = [team.id for team in db.session.query(Team).filter_by(race_id=race_id).all()]
        return db.session.query(BBMatch).filter_by(is_playoff_match=True).filter(or_(BBMatch.team_1_id.in_(team_ids), BBMatch.team_2_id.in_(team_ids))).count()

    races = db.session.query(Race).all()

    scorings = winning_scorings()
    race_results = {
        race.id: RaceScores(race=race, number_of_teams=db.session.query(Team).filter_by(race_id=race.id).count(),
                            number_of_scorings=len(scorings),
                            number_of_seasons=number_of_seasons(race.id),
                            number_of_playoff_matches=number_of_playoff_matches(race.id)) for race in races}

    results = __calculate_scores(race_results, scorings, 0, race_id_getter)

    for result in results.values():
        result.win_loss_diff = result.match_result_counts[0] - result.match_result_counts[-1]

    sorted_results = sorted([result for result in results.values() if result.number_of_matches > 0],
                            key=lambda result: (-result.win_loss_diff, -result.td_diff, -result.td_made, -result.number_of_matches, alphabetic_sorter(result)))
    determine_placings(sorted_results)

    return sorted_results
