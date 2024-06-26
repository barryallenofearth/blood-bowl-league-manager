import datetime
import os
import shutil

from flask import render_template
from html2image import Html2Image

from database import database
from database.database import Scorings, db
from table import score_table, casualties_table

OUTPUT_PATH = f"{os.getcwd()}/server/static/output"
HTML_2_IMAGE = Html2Image(output_path=OUTPUT_PATH)


def update_images(entity_type: str):
    def copy_required_files():
        if not os.path.exists(OUTPUT_PATH):
            os.mkdir(OUTPUT_PATH)
        files_to_copy = [f"{os.getcwd()}/server/static/css/Nuffle.ttf", f"{os.getcwd()}/server/static/logos/logo_league_{database.get_selected_league().id}.png"]

        for file in files_to_copy:
            file_name = file.split("/")[-1]
            if not os.path.exists(f"{HTML_2_IMAGE.temp_path}/{file_name}") and os.path.exists(file):
                shutil.copy(file, HTML_2_IMAGE.temp_path)

        if not os.path.exists(f"{HTML_2_IMAGE.temp_path}/styles.css"):
            with open(f"{os.getcwd()}/server/static/css/styles.css", encoding="utf-8") as css_file:
                with open(f"{HTML_2_IMAGE.temp_path}/styles.css", "w", encoding="utf-8") as imaging_css_file:
                    nuffle_path = "/static/css/Nuffle.ttf"
                    if "SCRIPT_NAME" in os.environ:
                        nuffle_path = os.environ["SCRIPT_NAME"] + nuffle_path
                    print(f"Nuffle Path: {nuffle_path}")
                    imaging_css_file.write(css_file.read().replace(nuffle_path, "Nuffle.ttf"))

    def print_png(table_html: str, dimension: str, number_of_entries: int):
        def generate_base_output_name(dimension: str):
            return f"{dimension}_table_{league.short_name}_season_{season.short_name}".replace('.', '_')

        base_team_table_name = generate_base_output_name(dimension)
        png_output = f"{base_team_table_name}.png"

        height = (number_of_entries + 1) * 31
        height += 100

        HTML_2_IMAGE.screenshot(html_str=table_html, save_as=png_output, size=(1200, height))

    copy_required_files()

    season = database.get_selected_season()
    league = database.get_selected_league()

    rendering_args = {"scorings": db.session.query(Scorings).filter_by(season_id=season.id).order_by(Scorings.touchdown_difference.desc()).all(),
                      "term_for_team_names": season.term_for_team_names,
                      "number_of_allowed_matches": season.number_of_allowed_matches,
                      "number_of_playoff_places": season.number_of_playoff_places,
                      "season": season,
                      "league": league,
                      "creation_date": datetime.date.today().strftime("%d.%m.%Y")}

    if entity_type == "teams":
        team_results = score_table.calculate_team_scores()
        team_casualties = casualties_table.calculate_team_casualties()
        total_number_of_casualties = sum([team_casualty.casualties for team_casualty in team_casualties])
        teams_table = render_template("imaging/teams_table_for_image.html", team_results=team_results, team_casualties=team_casualties,
                                      total_number_of_casualties=total_number_of_casualties,
                                      term_for_coaches=season.term_for_coaches, term_for_races=season.term_for_races,
                                      **rendering_args)
        print_png(teams_table, 'teams', len(team_results) + len(team_casualties))
    elif entity_type == "coaches":
        coach_results = score_table.calculate_coaches_scores()
        coaches_table = render_template("imaging/coaches_table_for_image.html", coach_results=coach_results, term_for_coaches=season.term_for_coaches, **rendering_args)
        print_png(coaches_table, 'coaches', len(coach_results))
    elif entity_type == "races":
        race_results = score_table.calculate_races_scores()
        races_table = render_template("imaging/races_table_for_image.html", race_results=race_results, term_for_races=season.term_for_races, **rendering_args)
        print_png(races_table, 'races', len(race_results))
