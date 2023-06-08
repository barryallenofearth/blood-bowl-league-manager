from flask import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Regexp, Length

from database.database import db, Coach, Race, Season, SeasonRules, League


class BaseLeagueForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a league name.")])
    short_name = StringField("Short name", validators=[DataRequired("Please enter a league short name.")])


class AddLeagueForm(BaseLeagueForm):
    submit = SubmitField(label="Add new league")


class UpdateLeagueForm(BaseLeagueForm):
    submit = SubmitField(label="Update league")


class BaseSeasonForm(FlaskForm):
    title = StringField("Name", validators=[DataRequired("Please enter a season name.")])
    short_name = StringField("Short name", validators=[DataRequired("Please enter a season short name.")])


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
            coach_options = [(coach.id, f"{coach.first_name} {coach.last_name}" + f" ({coach.display_name})" if coach.display_name is not None else "") for coach in db.session.query(Coach).order_by(Coach.first_name).all()]
            self.coach_select.choices = coach_options

            race_options = [(race.id, race.name) for race in db.session.query(Race).order_by(Race.name).all()]
            self.race_select.choices = race_options


class AddTeamForm(BaseTeamForm):
    submit = SubmitField(label="Add new season")


class UpdateTeamForm(BaseTeamForm):
    submit = SubmitField(label="Update season")
