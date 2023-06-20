import json
import os.path

import requests

OUTPUT_DIRECTORY = "../data"


def create_init_files(database_json: json):
    races = database_json["races"]

    with open(f"{OUTPUT_DIRECTORY}/races.csv", "w", encoding='utf-8') as races_file:
        races_file.write("name\n")
        for race in races:
            races_file.write(f"{race}\n")

    with open(f"{OUTPUT_DIRECTORY}/leagues.csv", "w", encoding='utf-8') as leagues_file:
        leagues_file.write("name;short_name;is_selected\n")
        for league in database_json["leagues"]:
            leagues_file.write(f"{league['name']};{league['short_name']};{league['is_selected']}\n")
    with open(f"{OUTPUT_DIRECTORY}/seasons.csv", "w", encoding='utf-8') as seasons_file:
        seasons_file.write("league_short_name;name;short_name;is_selected;scorings\n")
        for league in database_json["leagues"]:
            for season in league['seasons']:
                seasons_file.write(f"{league['short_name']};{season['name']};{season['short_name']};{season['is_selected']};")
                seasons_file.write("\\n".join([f"{scoring['touchdown_difference']}:{scoring['points_scored']}" for scoring in season["scorings"]]) + "\n")

    with open(f"{OUTPUT_DIRECTORY}/additional_statistics.csv", "w", encoding='utf-8') as additional_statistics_file:
        additional_statistics_file.write("team_name;casualties;season_short_name;league_short_name\n")
        for league in database_json["leagues"]:
            for season in league['seasons']:
                for statistic in season['additional_statistics']:
                    additional_statistics_file.write(f"{statistic['team']};{statistic['casualties']};{season['short_name']};{league['short_name']}\n")
    with open(f"{OUTPUT_DIRECTORY}/teams_and_coaches.csv", "w", encoding='utf-8') as teams_and_coaches_file:
        teams_and_coaches_file.write("name;coach_first_name;coach_last_name;coach_display_name;race_name;season_short_name;league_short_name\n")
        for league in database_json["leagues"]:
            for season in league['seasons']:
                for team in season['teams']:
                    coach_display_name = team['coach_display_name']
                    if coach_display_name is None or len(coach_display_name) == 0:
                        coach_display_name = " "
                    teams_and_coaches_file.write(f"{team['name']};{team['coach_first_name']};{team['coach_last_name']};{coach_display_name};{team['race']};{season['short_name']};{league['short_name']}\n")
    with open(f"{OUTPUT_DIRECTORY}/matches.csv", "w", encoding='utf-8') as matches:
        matches.write("match_number;team1;team2;td_team_1;td_team_2;point_modification_team_1;point_modification_team_2;team_1_surrendered;team_2_surrendered;is_playoff_match;is_tournament_match;season_short_name;league_short_name\n")
        for league in database_json["leagues"]:
            for season in league['seasons']:
                for match in season['matches']:
                    matches.write(
                        f"{match['match_number']};{match['team_1']};{match['team_2']};{match['team_1_touchdowns']};{match['team_2_touchdowns']};{match['team_1_point_modification']};{match['team_2_point_modification']};"
                        f"{match['team_1_surrendered']};{match['team_2_surrendered']};{match['is_playoff_match']};{match['is_tournament_match']};{season['short_name']};{league['short_name']}\n")


def create_configmap():
    init_files = ["additional_statistics.csv", "leagues.csv", "matches.csv", "races.csv", "seasons.csv", "teams_and_coaches.csv"]
    with open("0-configmap-init-files_template.yaml") as config_map_template:
        template_content = config_map_template.read().strip()
        for init_file in init_files:
            with open(f"{OUTPUT_DIRECTORY}/{init_file}") as init_file_content:
                template_content = template_content.replace("{{" + init_file + "}}", init_file_content.read().strip().replace("\n", "\n    "))

        with open(f"../k8s/webapp/0-configmap-init-files.yaml", "w") as config_map_output:
            config_map_output.write(template_content)


get_prod_database = requests.request(url="http://192.168.178.183/export", method="GET")
get_prod_database.raise_for_status()
database_json = get_prod_database.json()

create_init_files(database_json)
create_configmap()
