from flask import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Regexp, Length

from database.database import db, Coach, Race, Season, SeasonRules, League


class BaseLeagueForm(FlaskForm):
    title = StringField("Name", validators=[DataRequired("Please enter a league name.")])
    short_name = StringField("Short name", validators=[DataRequired("Please enter a league short name.")])


class AddLeagueForm(BaseLeagueForm):
    submit = SubmitField(label="Add new league")


class UpdateLeagueForm(BaseLeagueForm):
    submit = SubmitField(label="Update league")


class BaseSeasonForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a season name.")])
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


class BaseGroupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Please enter a group name.")])
    short_name = StringField("Name", validators=[DataRequired("Please enter a group short name.")])


class AddGroupForm(BaseGroupForm):
    submit = SubmitField(label="Add new group")


class UpdateGroupForm(BaseGroupForm):
    submit = SubmitField(label="Update group")


class BaseTeamForm(FlaskForm):
    team_name = StringField("Name", validators=[DataRequired("Please enter a team name.")])
    coach_select = SelectField("Coach", choices=[], validators=[DataRequired("Please select a coach")])
    race_select = SelectField("Race", choices=[], validators=[DataRequired("Please select a race")])

    def __init__(self, app: Flask):
        self.app = app

        with app.app_context():
            coach_options = [(coach.id, f"{coach.first_name} {coach.last_name}" + f"({coach.display_name})" if coach.display_name is not None else "") for coach in db.session.query(Coach).all()]
            self.coach_select.options = coach_options

            race_options = [(race.id, race.name) for race in db.session.query(Race).all()]
            self.race_select.options = race_options


class AddTeamForm(BaseRaceForm):
    submit = SubmitField(label="Add new season")


class UpdateTeamForm(BaseRaceForm):
    submit = SubmitField(label="Update season")
