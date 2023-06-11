from flask import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, FileField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Regexp, Length

from database.database import db, Coach, Race, Season, SeasonRules, League
from util import formatting


class BaseLeagueForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a league name.")])
    short_name = StringField("Short name", validators=[DataRequired("Please enter a league short name.")])
    logo = FileField("Logo", validators=[DataRequired(message="Please enter a png file for the logo.")])


class AddLeagueForm(BaseLeagueForm):
    submit = SubmitField(label="Add new league")


class UpdateLeagueForm(BaseLeagueForm):
    submit = SubmitField(label="Update league")


class BaseSeasonForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a season name.")])
    short_name = StringField("Short name", validators=[DataRequired("Please enter a season short name.")])
    team_short_name_length = IntegerField("Team short name length", validators=[DataRequired("Please enter a season short name.")])
    number_of_allowed_matches = IntegerField("Matches per team", validators=[DataRequired("Please enter a season short name.")])
    number_of_allowed_matches_vs_same_opponent = IntegerField("Matches vs same team", validators=[DataRequired("Please enter a season short name.")])
    number_of_playoff_places = IntegerField("Playoff place count", validators=[DataRequired("Please enter a season short name.")])
    term_for_team_names = StringField("Term for team names", validators=[DataRequired("Please enter a season short name.")])
    term_for_coaches = StringField("Term for coaches", validators=[DataRequired("Please enter a season short name.")])
    term_for_races = StringField("Term for races", validators=[DataRequired("Please enter a season short name.")])
    scorings = TextAreaField("Scorings (each line must follow format {TD-Diff}: {Points received}. i.e.: -1: 0)",
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

    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        with app.app_context():
            coach_options = [(coach.id, formatting.format_coach(coach)) for coach in db.session.query(Coach).order_by(Coach.first_name).all()]
            self.coach_select.choices = coach_options

            race_options = [(race.id, race.name) for race in db.session.query(Race).order_by(Race.name).all()]
            self.race_select.choices = race_options


class AddTeamForm(BaseTeamForm):
    submit = SubmitField(label="Add new team")


class UpdateTeamForm(BaseTeamForm):
    is_disqualified = BooleanField("Disqualified")
    submit = SubmitField(label="Update team")
