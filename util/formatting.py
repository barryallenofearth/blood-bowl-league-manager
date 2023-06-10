import re

from database import database
from database.database import db, Team, Coach, BBMatch, SeasonRules


def generate_team_short_name(team_name: str):
    def length_of_all_words(index_words: dict):
        length = 0
        for value in index_words.values():
            length += len(value)
            # if the value does not end in a dot, the value is followed by a space
            if value[-1] != ".":
                length += 1

        return length

    season = database.get_selected_season()
    season_rules = db.session.query(SeasonRules).filter_by(season_id=season.id).first()
    # name is short enough
    max_length = season_rules.team_short_name_length
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


def format_coach(coach: Coach):
    string = f"{coach.first_name} {coach.last_name}"
    if coach.display_name is not None and coach.display_name != "":
        string += f" ({coach.display_name})"
    return string


def format_match(match: BBMatch):
    team1_name = db.session.query(Team).filter_by(match.team_1_id).first().name
    team2_name = db.session.query(Team).filter_by(match.team_2_id).first().name

    string = f"{team1_name} vs. {team2_name} : {match.team_1_touchdown}:{match.team_2_touchdown}"
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
    if match.is_tournament:
        string += " (Tournament)"

    return string
