from flask_wtf import FlaskForm
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FileField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Regexp

import database.database
from database.database import db, Coach, Race, Team
from util import formatting, parsing


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
    is_disqualified = BooleanField("Disqualified")
    submit = SubmitField(label="Update team")


class BaseMatchForm(FlaskForm):
    team1 = SelectField("Team 1", validators=[DataRequired("Please select a team")])


class AddMatchForm(FlaskForm):
    match_user_input = StringField("Match user input", description="Matches need to be entered using the following pattern: {TEAM 1} vs. {TEAM 2} : {TEAM 1 TOUCHDOWNS}:{TEAM 2 TOUCHDOWNS}<br>"
                                                                   "i.e.: Wolbecker Wolpertinger vs. Necropolis Nightmares 2:1",
                                   validators=[Regexp(regex=parsing.MATCH_REGEX, message="Please enter match results in the required format")])
    submit = SubmitField(label="Add new match")


class UpdateMatchForm(FlaskForm):
    team1 = SelectField("Team 1", validators=[DataRequired("Please select a team")])
    team2 = SelectField("Team 2", validators=[DataRequired("Please select an opponent")])
    team1_td_made = IntegerField("Team 1 touchdowns")
    team2_td_made = IntegerField("Team 2 touchdowns")
    match_number = IntegerField("Match number", validators=[DataRequired("Please enter a valid number.")])
    surrendered_select = SelectField("Team surrendered", choices=[(0, "No team surrendered"), (1, "Team 1 surrendered"), (2, "Team 2 surrendered")])
    team1_points_modification = IntegerField("Team 1 points modification")
    team2_points_modification = IntegerField("Team 2 points modification")
    match_type_select = SelectField("Match type", choices=[(0, "Standard match"), (1, "Playoff match"), (2, "Tournament match")])
    submit = SubmitField(label="Update match")

    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)

        with app.app_context():
            season = database.database.get_selected_season()
            all_teams = db.session.query(Team).filter_by(season_id=season.id).all()
            self.team1.choices = [(team.id, formatting.format_team(team)) for team in all_teams]
            self.team2.choices = [(team.id, formatting.format_team(team)) for team in all_teams]
