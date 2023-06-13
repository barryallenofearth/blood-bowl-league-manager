from operator import itemgetter

from database import database
from database.database import db, BBMatch, Team, Race, Coach, Scorings
from util import formatting


class TeamScores:
    def __init__(self, team: Team, match_result_counts, place=1, number_of_matches=0, td_received=0, td_made=0, td_diff=0, points=0):
        self.place = place
        self.team_short_name = team.short_name
        self.race = db.session.query(Race).filter_by(id=team.race_id).first().name
        self.coach = formatting.format_coach(db.session.query(Coach).filter_by(id=team.coach_id).first())
        self.number_of_matches = number_of_matches
        self.match_result_counts = match_result_counts
        self.td_received = td_received
        self.td_made = td_made
        self.td_diff = td_diff
        self.points = points

    def __repr__(self):
        return f"place: {self.place}, team_short_name:{self.team_short_name}, race:{self.race}, coach:{self.coach}, " \
               f"number_of_matches:{self.number_of_matches},match_result_counts:{self.match_result_counts},td_received:{self.td_received},td_made:{self.td_made},td_diff:{self.td_diff},points:{self.points}\n"


def calculate_team_scores():
    def modify_team_score(team_results: dict, team_id: int, td_made: int, td_received: int, points_modification: int, scorings: list):
        def determine_points(td_diff: int) -> int:
            def increment_match_results_count(index: int):
                team_scoring.match_result_counts[len(scorings) - 1 - index] = team_scoring.match_result_counts[len(scorings) - 1 - index] + 1

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

        team_scoring = team_results[team_id]
        team_scoring.number_of_matches = team_scoring.number_of_matches + 1
        team_scoring.td_made = team_scoring.td_made + td_made
        team_scoring.td_received = team_scoring.td_received + td_received
        td_diff = td_made - td_received
        team_scoring.td_diff = team_scoring.td_diff + td_diff
        team_scoring.points = team_scoring.points + points_modification + determine_points(td_diff)

    season = database.get_selected_season()
    teams = db.session.query(Team).filter_by(season_id=season.id).all()

    scorings = db.session.query(Scorings).filter_by(season_id=season.id).order_by(Scorings.touchdown_difference).all()
    team_results = {team.id: TeamScores(team=team, match_result_counts=[0 for _ in range(len(scorings))]) for team in teams}

    matches = db.session.query(BBMatch).filter_by(season_id=season.id).all()

    for match in matches:
        modify_team_score(team_results, match.team_1_id, match.team_1_touchdown, match.team_2_touchdown, match.team_1_point_modification, scorings)
        modify_team_score(team_results, match.team_2_id, match.team_2_touchdown, match.team_1_touchdown, match.team_2_point_modification, scorings)

    sorted_results = sorted(team_results.values(), key=lambda result: (-result.points, -result.td_diff, -result.td_made, -result.number_of_matches))
    points_previous = sorted_results[0].points
    td_diff_previous = sorted_results[0].td_diff
    td_made_previous = sorted_results[0].td_made
    place_previous = sorted_results[0].place
    for index in range(1, len(sorted_results)):
        if points_previous > sorted_results[index].points or td_diff_previous > sorted_results[index].td_diff or td_made_previous > sorted_results[index].td_made:
            sorted_results[index].place = place_previous + 1
        else:
            sorted_results[index].place = place_previous

        points_previous = sorted_results[index].points
        td_diff_previous = sorted_results[index].td_diff
        td_made_previous = sorted_results[index].td_made
        place_previous = sorted_results[index].place

    return sorted_results
