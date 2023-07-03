from sqlalchemy import or_

from database import database
from database.database import Race, Team, db, AdditionalStatistics, Coach, BBMatch
from util import formatting


class TeamCasualties:

    def __init__(self, team: Team, number_of_matches: int, place=1, casualties=0):
        self.place = place
        self.number_of_matches = number_of_matches
        self.casualties = casualties
        self.team_short_name = team.short_name
        self.race = db.session.query(Race).filter_by(id=team.race_id).first().name
        self.coach = formatting.coach_table_name(team.coach_id)


def __calculate_scores(results: dict, season_id: int, entity_id_from_team_id_getter, alphabetic_sorter):
    def modify_team_score(analysis_results: dict, entity_id: int, casualties: int):

        analysis_casualties = analysis_results[entity_id]
        analysis_casualties.casualties = analysis_casualties.casualties + casualties

    if len(results) == 0:
        return []

    additional_statistics = db.session.query(AdditionalStatistics).filter_by(season_id=season_id).all()

    for statistics in additional_statistics:
        modify_team_score(results, entity_id_from_team_id_getter(statistics.team_id), statistics.casualties)

    sorted_results_with_non_zero_match_count = sorted([result for result in results.values() if result.number_of_matches > 0],
                                                      key=lambda result: (-result.casualties, -result.number_of_matches, alphabetic_sorter(result)))
    sorted_results_with_zero_match_count = sorted([result for result in results.values() if result.number_of_matches == 0], key=lambda result: alphabetic_sorter(result))
    sorted_results = sorted_results_with_non_zero_match_count + sorted_results_with_zero_match_count

    casualties_previous = sorted_results[0].casualties
    place_previous = sorted_results[0].place
    for index in range(1, len(sorted_results)):
        if casualties_previous > sorted_results[index].casualties:
            sorted_results[index].place = place_previous + 1
        else:
            sorted_results[index].place = place_previous

        casualties_previous = sorted_results[index].casualties
        place_previous = sorted_results[index].place

    return sorted_results


def number_of_matches_by_team(team_list: list) -> int:
    number_of_matches = 0
    for team in team_list:
        number_of_matches += db.session.query(BBMatch).filter(or_(BBMatch.team_1_id == team.id, BBMatch.team_2_id == team.id)).count()
    return number_of_matches


def calculate_team_casualties():
    def team_id_getter(team_id: int):
        return team_id

    def alphabetic_sorter(team_scores: TeamCasualties):
        return team_scores.team_short_name

    season = database.get_selected_season()
    teams = db.session.query(Team).filter_by(season_id=season.id).all()

    team_casualties = {team.id: TeamCasualties(team=team, number_of_matches=number_of_matches_by_team([team])) for team in teams}

    results = __calculate_scores(team_casualties, season.id, team_id_getter, alphabetic_sorter)

    return [casualty for casualty in results if casualty.casualties > 0]
