import re

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FileField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Regexp

import database.database
from database.database import db, Coach, Race, Team, League
from util import formatting, parsing


class StatisticsForm(FlaskForm):
    league = SelectField("League", validators=[DataRequired("Please select a league")])
    submit = SubmitField(label="Calculate")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.league.choices = [(0, "All seasons")]
        for league in db.session.query(League).all():
            self.league.choices.append((league.id, league.name))

        if "league" in kwargs:
            self.league.data = kwargs["league"]


class BaseLeagueForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a league name.")], render_kw={"placeholder": "Westfalia Blood Bowl League"})
    short_name = StringField("Short name", validators=[DataRequired("Please enter a league short name.")], render_kw={"placeholder": "WBBL"})
    logo = FileField("Logo", validators=[DataRequired(message="Please enter a png file for the logo.")])


class AddLeagueForm(BaseLeagueForm):
    submit = SubmitField(label="Add new league")


class UpdateLeagueForm(BaseLeagueForm):
    submit = SubmitField(label="Update league")


class BaseSeasonForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a season name.")], render_kw={"placeholder": "Season 4"})
    short_name = StringField("Short name", validators=[DataRequired("Please enter a season short name.")], render_kw={"placeholder": "S.4"})
    team_short_name_length = IntegerField("Team short name length", validators=[DataRequired("Please enter a season short name.")])
    number_of_allowed_matches = IntegerField("Matches per team", validators=[DataRequired("Please enter a season short name.")])
    number_of_allowed_matches_vs_same_opponent = IntegerField("Matches vs same team", validators=[DataRequired("Please enter a season short name.")])
    number_of_playoff_places = IntegerField("Playoff place count", validators=[DataRequired("Please enter a season short name.")])
    term_for_team_names = StringField("Term for team names", validators=[DataRequired("Please enter a season short name.")])
    term_for_coaches = StringField("Term for coaches", validators=[DataRequired("Please enter a season short name.")])
    term_for_races = StringField("Term for races", validators=[DataRequired("Please enter a season short name.")])
    scorings = TextAreaField("Scorings (each line must follow format {TD-Diff}: {Points received}. i.e.: -1: 0)",
                             render_kw={"rows": 5, "cols": 11},
                             validators=[Regexp(regex=r"^(?:-?\d+\s*:\s*-?\d+\s*)+$", message="Please enter scorings in the required format")])


class AddSeasonForm(BaseSeasonForm):
    submit = SubmitField(label="Add new season")


class UpdateSeasonForm(BaseSeasonForm):
    submit = SubmitField(label="Update season")


class BaseCoachForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired("Please enter a first name.")])
    last_name = StringField("Last Name", validators=[DataRequired("Please enter a last name.")])
    display_name = StringField("Short name")


class AddCoachForm(BaseCoachForm):
    submit = SubmitField(label="Add new coach")


class UpdateCoachForm(BaseCoachForm):
    submit = SubmitField(label="Update coach")


class BaseRaceForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a race name.")])


class AddRaceForm(BaseRaceForm):
    submit = SubmitField(label="Add new race")


class UpdateRaceForm(BaseRaceForm):
    submit = SubmitField(label="Update race")


class BaseTeamForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a team name.")])
    coach_select = SelectField("Coach", validators=[DataRequired("Please select a coach")])
    race_select = SelectField("Race", validators=[DataRequired("Please select a race")])
    is_disqualified = BooleanField("Disqualified")

    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)

        with app.app_context():
            coach_options = [(coach.id, formatting.format_coach(coach)) for coach in db.session.query(Coach).order_by(Coach.first_name).order_by(Coach.last_name).all()]
            self.coach_select.choices = coach_options

            race_options = [(race.id, race.name) for race in db.session.query(Race).order_by(Race.name).all()]
            self.race_select.choices = race_options


class AddTeamForm(BaseTeamForm):
    submit = SubmitField(label="Add new team")


class UpdateTeamForm(BaseTeamForm):
    submit = SubmitField(label="Update team")


class BaseMatchForm(FlaskForm):
    team1 = SelectField("Team 1", validators=[DataRequired("Please select a team")])
    team2 = SelectField("Team 2", validators=[DataRequired("Please select an opponent")])
    team1_td_made = IntegerField("Team 1 touchdowns")
    team2_td_made = IntegerField("Team 2 touchdowns")
    match_number = IntegerField("Match number", validators=[DataRequired("Please enter a valid number.")])
    surrendered_select = SelectField("Team surrendered", choices=[(0, "No team surrendered"), (1, "Team 1 surrendered"), (2, "Team 2 surrendered")])
    team1_points_modification = IntegerField("Team 1 points modification")
    team2_points_modification = IntegerField("Team 2 points modification")
    match_type_select = SelectField("Match type", choices=[(0, "Standard match"), (1, "Playoff match"), (2, "Tournament match")])
    victory_by_kickoff_select = SelectField("Victory by kickoff", choices=[(0, "No kickoff decision"), (1, "Team 1 won by kickoff"), (2, "Team 2 won by kickoff")])

    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)

        with app.app_context():
            season = database.database.get_selected_season()
            all_teams = db.session.query(Team).filter_by(season_id=season.id).order_by(Team.name).all()
            self.team1.choices = [(team.id, formatting.format_team(team)) for team in all_teams]
            self.team2.choices = [(team.id, formatting.format_team(team)) for team in all_teams]


class AddMatchForm(BaseMatchForm):
    submit = SubmitField(label="Add new match")

    def __init__(self, app, **kwargs):
        super().__init__(app=app, **kwargs)


class UpdateMatchForm(BaseMatchForm):
    submit = SubmitField(label="Update match")

    def __init__(self, app, **kwargs):
        super().__init__(app=app, **kwargs)


class BaseAdditionalStatisticsEntryForm(FlaskForm):
    team = SelectField("Team", validators=[DataRequired("Please select a team")])
    casualties = IntegerField("Please enter the number of casualties made.")

    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)

        with app.app_context():
            season = database.database.get_selected_season()
            all_teams = db.session.query(Team).filter_by(season_id=season.id).all()
            self.team.choices = [(current_team.id, formatting.format_team(current_team)) for current_team in all_teams]


class AddAdditionalStatisticsEntryForm(BaseAdditionalStatisticsEntryForm):
    submit = SubmitField(label="Add new statistics")

    def __init__(self, app=None, **kwargs):
        super().__init__(app=app, **kwargs)


class UpdateAdditionalStatisticsEntryForm(BaseAdditionalStatisticsEntryForm):
    submit = SubmitField(label="Update statistics")

    def __init__(self, app=None, **kwargs):
        super().__init__(app=app, **kwargs)


class UserInputForm(FlaskForm):
    user_input = StringField("User input",
                             description="i.e.: Wolbecker Wolpertinger vs. Necropolis Nightmares 2:1<br>"
                                         "i.e.: Wolbecker Wolpertinger: 3 Casualties",
                             render_kw={"placeholder": "Wolbecker Wolpertinger vs. Necropolis Nightmares 2:1 (Playoffs)"},
                             validators=[Regexp(regex=f"({parsing.MATCH_REGEX}|{parsing.CASUALTIES_REGEX})", flags=re.IGNORECASE, message="Please enter a valid match result or casualties entry.")])
    match_type_select = SelectField("Match type", choices=[(0, "Standard match"), (1, "Playoff match"), (2, "Tournament match")])
    submit = SubmitField(label="Process user input")
