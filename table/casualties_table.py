from database import database
from database.database import Race, Team, db, AdditionalStatistics, Coach
from util import formatting


class BaseCasualties:
    def __init__(self, place=1, number_of_matches=0, casualties=0):
        self.place = place
        self.number_of_matches = number_of_matches
        self.casualties = casualties


class TeamCasualties(BaseCasualties):

    def __init__(self, team: Team, place=1, number_of_matches=0, casualties=0):
        super().__init__(place, number_of_matches, casualties)
        self.team_short_name = team.short_name
        self.race = db.session.query(Race).filter_by(id=team.race_id).first().name
        self.coach = formatting.coach_table_name(team.coach_id)


class RaceCasualties(BaseCasualties):

    def __init__(self, race: Race, number_of_teams: int, place=1, number_of_matches=0, casualties=0):
        super().__init__(place, number_of_matches, casualties)
        self.race = race.name
        self.number_of_teams = number_of_teams


class CoachCasualties(BaseCasualties):

    def __init__(self, coach: Coach, number_of_teams: int, place=1, number_of_matches=0, casualties=0):
        super().__init__(place, number_of_matches, casualties)
        self.coach = formatting.coach_table_name(coach.id)
        self.number_of_teams = number_of_teams


def __calculate_scores(results: dict, season_id: int, entity_id_from_team_id_getter, alphabetic_sorter):
    def modify_team_score(analysis_results: dict, entity_id: int, casualties: int):

        analysis_casualties = analysis_results[entity_id]
        analysis_casualties.number_of_matches = analysis_casualties.number_of_matches + 1
        analysis_casualties.casualties = analysis_casualties.casualties + casualties

    if len(results) == 0:
        return []

    additional_statistics = db.session.query(AdditionalStatistics).filter_by(season_id=season_id).all()

    for statistics in additional_statistics:
        modify_team_score(results, entity_id_from_team_id_getter(statistics.team_id), statistics.casualties)

    sorted_results = sorted([result for result in results.values() if result.number_of_matches > 0],
                            key=lambda result: (-result.casualties, -result.number_of_matches, alphabetic_sorter(result)))
    sorted_results = sorted_results + sorted([result for result in results.values() if result.number_of_matches == 0], key=lambda result: alphabetic_sorter(result))

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


def calculate_team_casulties():
    def team_id_getter(team_id: int):
        return team_id

    def alphabetic_sorter(team_scores: TeamCasualties):
        return team_scores.team_short_name

    season = database.get_selected_season()
    teams = db.session.query(Team).filter_by(season_id=season.id).all()

    team_casualties = {team.id: TeamCasualties(team=team) for team in teams}
    return __calculate_scores(team_casualties, season.id, team_id_getter, alphabetic_sorter)


def calculate_coaches_casulties():
    def team_id_getter(team_id: int):
        return db.session.query(Team).filter_by(id=team_id).first().coach_id

    def alphabetic_sorter(coach_casualties: CoachCasualties):
        return coach_casualties.coach

    season = database.get_selected_season()
    coaches = {db.session.query(Coach).filter_by(id=team.coach_id).first() for team in db.session.query(Team).filter_by(season_id=season.id).all()}

    coach_casualties = {coach.id: CoachCasualties(coach=coach, number_of_teams=db.session.query(Team).filter_by(season_id=season.id).filter_by(coach_id=coach.id).count()) for coach in coaches}
    return __calculate_scores(coach_casualties, season.id, team_id_getter, alphabetic_sorter)


def calculate_races_casulties():
    def team_id_getter(team_id: int):
        return db.session.query(Team).filter_by(id=team_id).first().race_id

    def alphabetic_sorter(race_scores: RaceCasualties):
        return race_scores.race

    season = database.get_selected_season()
    races = {db.session.query(Race).filter_by(id=team.race_id).first() for team in db.session.query(Team).filter_by(season_id=season.id).all()}

    coach_casualties = {race.id: RaceCasualties(race=race, number_of_teams=db.session.query(Team).filter_by(season_id=season.id).filter_by(race_id=race.id).count()) for race in races}
    return __calculate_scores(coach_casualties, season.id, team_id_getter, alphabetic_sorter)
