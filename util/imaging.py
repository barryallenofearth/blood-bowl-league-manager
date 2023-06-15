import datetime
import os
import shutil

from flask import render_template
from html2image import Html2Image

from database import database
from database.database import Scorings, SeasonRules, db
from table import table_generator

OUTPUT_PATH = f"{os.getcwd()}/server/static/output"
HTML_2_IMAGE = Html2Image(output_path=OUTPUT_PATH)


def update_images():
    def copy_required_files():
        if not os.path.exists(OUTPUT_PATH):
            os.mkdir(OUTPUT_PATH)

        if not os.path.exists(f"{HTML_2_IMAGE.temp_path}/Nuffle.ttf"):
            shutil.copy(f"{os.getcwd()}/server/static/css/Nuffle.ttf", HTML_2_IMAGE.temp_path)

        if not os.path.exists(f"{HTML_2_IMAGE.temp_path}/styles.css"):
            with open(f"{os.getcwd()}/server/static/css/styles.css", encoding="utf-8") as css_file:
                with open(f"{HTML_2_IMAGE.temp_path}/styles.css", "w", encoding="utf-8") as imaging_css_file:
                    imaging_css_file.write(css_file.read().replace("/static/css/Nuffle.ttf", "Nuffle.ttf"))

    def print_png(table_html: str, dimension: str, number_of_entries: int):
        def generate_base_output_name(dimension: str):
            return f"{dimension}_table_{league.short_name}_season_{season.short_name}".replace('.', '_')

        base_team_table_name = generate_base_output_name(dimension)
        png_output = f"{base_team_table_name}.png"
        print(HTML_2_IMAGE.temp_path)
        HTML_2_IMAGE.screenshot(html_str=table_html, save_as=png_output, size=(1080, 100 + (number_of_entries + 1) * 32))

    copy_required_files()

    season = database.get_selected_season()
    league = database.get_selected_league()
    season_rules = db.session.query(SeasonRules).filter_by(season_id=season.id).first()
    team_results = table_generator.calculate_team_scores()
    coach_results = table_generator.calculate_coaches_scores()
    race_results = table_generator.calculate_races_scores()

    rendering_args = {"scorings": db.session.query(Scorings).filter_by(season_id=season.id).order_by(Scorings.touchdown_difference.desc()).all(),
                      "term_for_team_names": season_rules.term_for_team_names,
                      "number_of_allowed_matches": season_rules.number_of_allowed_matches,
                      "number_of_playoff_places": season_rules.number_of_playoff_places,
                      "season": season,
                      "league": league,
                      "creation_date": datetime.date.today().strftime("%d.%m.%Y")}

    teams_table = render_template("imaging/teams_table_for_image.html", team_results=team_results,
                                  term_for_coaches=season_rules.term_for_coaches, term_for_races=season_rules.term_for_races, **rendering_args)
    print_png(teams_table, 'teams', len(team_results))

    coaches_table = render_template("imaging/coaches_table_for_image.html", coach_results=coach_results, term_for_coaches=season_rules.term_for_coaches, **rendering_args)
    print_png(coaches_table, 'coaches', len(coach_results))

    races_table = render_template("imaging/races_table_for_image.html", race_results=race_results, term_for_races=season_rules.term_for_races, **rendering_args)
    print_png(races_table, 'races', len(race_results))
