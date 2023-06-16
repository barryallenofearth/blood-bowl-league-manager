import re

import Levenshtein

import database.database
from database.database import BBMatch, AdditionalStatistics, Team, db

# group 1: Match number
# group 2: Team name 1
# group 3: Team name 2
# group 4: Touchdowns Team 1
# group 5: Touchdowns Team 2
# group 5: remaining part
MATCH_REGEX = r"^(?:Match\s*(\d*)\s*:\s*)?\s*([^:]+?)(?:\s*vs[.\s]\s*)([^:]+?)(?:\s*|:\s*)(\d+)(?:\s*[:-]\s*)(\d+)(.*)$"
MATCH_RESULT_MATCHER = re.compile(MATCH_REGEX)

# group 1: Team name
# group 2 or 3: casualties
CASUALTIES_REGEX = r"^\s*([^:]+?)[\s:]+(?:(\d+)\s*(?:casualties|casulties|cas)|(?:casualties|casulties|cas)\s*(\d+))\s*$"
CASUALTIES_MATCHER = re.compile(CASUALTIES_REGEX, re.IGNORECASE)


def __clean_up_unwanted_chars(user_input: str) -> str:
    user_input = user_input.strip()
    user_input = re.sub("[^\w\s':.\-]+", " ", user_input)
    user_input = re.sub("\s{2,}", " ", user_input)
    return user_input


def __determine_matching_team(all_teams: list, input_name):
    def determine_levenshtein_distance(team, input_name):
        short_name_distance = Levenshtein.distance(team.short_name, input_name)
        name_distance = Levenshtein.distance(team.name, input_name)
        return min(short_name_distance, name_distance)

    smallest_distance = 10000
    best_matching_team: Team

    for team in all_teams:
        distance = determine_levenshtein_distance(team, input_name)
        if distance < smallest_distance:
            smallest_distance = distance
            best_matching_team = team

    return best_matching_team


def parse_match_result(user_input: str) -> BBMatch:
    original_input = user_input

    user_input = __clean_up_unwanted_chars(user_input)
    matching_result = MATCH_RESULT_MATCHER.match(user_input)
    if matching_result is None:
        raise SyntaxError(f"The provided input '{original_input}' could not be parsed after cleanup: '{user_input}'")

    season = database.database.get_selected_season()
    all_teams = db.session.query(Team).filter_by(season_id=season.id).all()

    match_number = matching_result.group(1)
    team_input_1 = matching_result.group(2).strip()
    team_input_2 = matching_result.group(3).strip()
    team_1_td = int(matching_result.group(4).strip())
    team_2_td = int(matching_result.group(5).strip())
    remainder = matching_result.group(6)

    bb_match = BBMatch()
    bb_match.season_id = season.id

    if match_number is None:
        highest_match_number = db.session.query(BBMatch) \
            .filter_by(season_id=season.id) \
            .order_by(BBMatch.match_number.desc()) \
            .first()
        if highest_match_number is None:
            bb_match.match_number = 1
        else:
            bb_match.match_number = highest_match_number.match_number + 1
    else:
        bb_match.match_number = int(match_number.strip())

    bb_match.team_1_id = __determine_matching_team(all_teams, team_input_1).id
    bb_match.team_2_id = __determine_matching_team(all_teams, team_input_2).id

    bb_match.team_1_touchdown = team_1_td
    bb_match.team_2_touchdown = team_2_td

    if remainder is not None:
        remainder = remainder.lower()
        bb_match.is_tournament_match = "turnier" in remainder or "tournament" in remainder
        bb_match.is_playoff_match = "playoff" in remainder

    bb_match.team_1_surrendered = False
    bb_match.team_2_surrendered = False

    bb_match.team_1_point_modification = 0
    bb_match.team_2_point_modification = 0

    return bb_match


def parse_additonal_statistics_input(user_input: str) -> AdditionalStatistics:
    original_input = user_input

    user_input = __clean_up_unwanted_chars(user_input)
    matching_result = CASUALTIES_MATCHER.match(user_input)
    if matching_result is None:
        raise SyntaxError(f"The provided input '{original_input}' could not be parsed after cleanup: '{user_input}'")

    season = database.database.get_selected_season()
    all_teams = db.session.query(Team).filter_by(season_id=season.id).all()

    additional_statistics = AdditionalStatistics()
    additional_statistics.season_id = season.id

    additional_statistics.team_id = __determine_matching_team(all_teams, matching_result.group(1)).id
    if matching_result.group(2) is not None:
        additional_statistics.casualties = int(matching_result.group(2))
    elif matching_result.group(3) is not None:
        additional_statistics.casualties = int(matching_result.group(3))

    return additional_statistics
