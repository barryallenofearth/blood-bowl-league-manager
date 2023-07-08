import re

from database import database
from database.database import db, Team, Coach, BBMatch, Scorings, AdditionalStatistics


def generate_scorings_field_value(season_id: int) -> str:
    scorings_text_area = ""
    all_scorings = db.session.query(Scorings).filter_by(season_id=season_id).all()
    for index in range(0, len(all_scorings)):
        scoring = all_scorings[index]
        scorings_text_area += f"{scoring.touchdown_difference}: {scoring.points_scored}"
        if index < len(all_scorings) - 1:
            scorings_text_area += "\n"
    return scorings_text_area


def generate_team_short_name(team_name: str) -> str:
    def length_of_all_words(index_words: dict) -> int:
        length = 0
        for value in index_words.values():
            length += len(value)
            # if the value does not end in a dot, the value is followed by a space
            if value[-1] != ".":
                length += 1

        return length

    season = database.get_selected_season()
    # name is short enough
    max_length = season.team_short_name_length
    if len(team_name) <= max_length:
        return team_name

    team_words = re.split(r"[\s\-_]+", team_name)
    # name only consists of 1 word => cut off the part that is too long and add a dot
    if len(team_words) == 1:
        return team_name[:max_length - 1] + "."

    index_words = {index: team_words[index] for index in range(0, len(team_words))}
    all_lower_case_words_shortened = False
    index = 1
    # 1) go through every word that is lowercase after the first word and shorten it to starting letter + "."
    # 2) go through every remaining word after the first word and shorten it to starting letter + "."
    # 3) shorten first word to starting letter + "."
    # 4) shorten entire expression like single word expression
    while length_of_all_words(index_words) >= max_length:
        if index_words[index][0].islower() or all_lower_case_words_shortened:
            index_words[index] = index_words[index][0] + "."

        index += 1
        if index == len(index_words) and not all_lower_case_words_shortened:
            all_lower_case_words_shortened = True
            index = 1
        elif index == len(index_words) and all_lower_case_words_shortened:
            index_words[0] = index_words[0][0] + "."
            break

    short_name = ""
    for index, value in index_words.items():
        short_name += value
        if value[-1] != ".":
            short_name += " "
    short_name = short_name.strip()
    if len(short_name) > max_length:
        short_name = short_name[:max_length - 1] + "."

    # if name ends with a .. now reduce it to single dot
    if short_name[-2:] == "..":
        short_name = short_name[:-1]
    return short_name


def format_team(team: Team) -> str:
    return f"{team.name} ({coach_table_name(team.coach_id)})"


def format_coach(coach: Coach) -> str:
    string = f"{coach.first_name} {coach.last_name}"
    if coach.display_name is not None and coach.display_name != "":
        string += f" ({coach.display_name})"
    return string


def coach_table_name(coach_id: int, season_id=-1) -> str:
    def generate_table_name(coach: Coach, index: int):
        if len(coach.last_name) < index:
            return f"{coach.first_name} {coach.last_name}"
        return coach.first_name + " " + coach.last_name[:index + 1]

    if season_id == -1:
        season_id = database.get_selected_season().id

    coach = db.session.query(Coach).filter_by(id=coach_id).first()
    if coach.display_name is not None and coach.display_name != "":
        return coach.display_name

    query = db.session.query(Team)
    if season_id != 0:
        query = query.filter_by(season_id=season_id)
    teams_by_other_coaches = query \
        .filter(Team.coach_id != coach_id) \
        .filter(Team.is_disqualified is not True) \
        .all()
    all_coaches_ids_with_team_in_season = [team.coach_id for team in teams_by_other_coaches]

    all_coaches_with_identical_first_name = db.session.query(Coach) \
        .filter(Coach.id.in_(all_coaches_ids_with_team_in_season)) \
        .filter_by(first_name=coach.first_name) \
        .all()

    if len(all_coaches_with_identical_first_name) == 0:
        return coach.first_name

    index = 0
    full_name = coach.first_name + " " + coach.last_name
    table_name = generate_table_name(coach, index)
    display_names = [generate_table_name(current_coach, index) for current_coach in all_coaches_with_identical_first_name]
    while table_name in display_names and table_name != f"{coach.first_name} {coach.last_name}":
        index += 1

        table_name = generate_table_name(coach, index)
        display_names = [generate_table_name(current_coach, index) for current_coach in all_coaches_with_identical_first_name]

    if table_name != full_name:
        table_name += "."
    else:
        table_name = full_name

    return table_name


def format_match(match: BBMatch) -> str:
    team1_name = db.session.query(Team).filter_by(id=match.team_1_id).first().name
    team2_name = db.session.query(Team).filter_by(id=match.team_2_id).first().name

    string = f"Match {match.match_number}: {team1_name} vs. {team2_name} : {match.team_1_touchdown}:{match.team_2_touchdown}"
    if match.team_1_surrendered:
        string += f" ({team1_name} surrendered)"
    if match.team_2_surrendered:
        string += f" ({team2_name} surrendered)"
    if match.team_1_point_modification is not None and match.team_1_point_modification != 0:
        string += f" ({match.team_1_point_modification} points for {team1_name})"
    if match.team_2_point_modification is not None and match.team_2_point_modification != 0:
        string += f" ({match.team_2_point_modification} points for {team2_name})"
    if match.is_playoff_match:
        string += " (Playoffs)"
    if match.is_tournament_match:
        string += " (Tournament)"
    if match.is_team_1_victory_by_kickoff:
        string += f" ({team1_name} wins by kickoff decision)"
    if match.is_team_2_victory_by_kickoff:
        string += f" ({team2_name} wins by kickoff decision)"

    return string


def format_additional_statistics(additional_statistics: AdditionalStatistics):
    team = db.session.query(Team).filter_by(id=additional_statistics.team_id).first()

    return f"{team.name}: {additional_statistics.casualties} Casualties"
