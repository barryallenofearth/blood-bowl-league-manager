from flask import redirect, url_for, Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm

from database import database
from database.database import League, Season, SeasonRules, Scorings, Coach, Race, Team
from server import forms
from server.forms import UpdateTeamForm, BaseSeasonForm, BaseCoachForm, BaseRaceForm, BaseTeamForm
from util import formatting

FORM_KEY = "form"


def persist_and_redirect(entity, entity_type: str, db: SQLAlchemy):
    db.session.add(entity)
    db.session.commit()
    return redirect(url_for("manage", entity_type=entity_type, _anchor=f"row-entity-{entity.id}"))


def __get_league(db, entity_id):
    league: League
    if entity_id > 0:
        league = db.session.query(League).filter_by(id=entity_id).first()
    else:
        league = League()
    return league


def league_get(db: SQLAlchemy, entity_id: int) -> dict:
    title_row = ["Name", "Short name"]
    table = []
    for league in db.session.query(League).all():
        table.append([league.name + (f" (active)" if league.is_selected else ""), league.short_name, league.id])

    league = __get_league(db, entity_id)

    if entity_id == 0:
        form = forms.AddLeagueForm()
    else:
        form = forms.UpdateLeagueForm(name=league.name, short_name=league.short_name)
    kwargs = {FORM_KEY: form, "title": "Leagues", "title_row": title_row, "table": table}

    return kwargs


def league_submit(form: FlaskForm, db: SQLAlchemy, entity_id: int):
    league = __get_league(db, entity_id)
    league.name = form.name.data.strip()
    league.short_name = form.short_name.data.strip()

    if entity_id == 0:
        league.is_selected = True
        selected_league = database.get_selected_league()
        if selected_league is not None:
            selected_league.is_selected = False
            db.session.add(selected_league)

    return persist_and_redirect(league, League.__tablename__, db)


def __get_season_and_rules(db: SQLAlchemy, entity_id: int) -> tuple:
    season: Season
    season_rules: SeasonRules
    if entity_id == 0:
        season = Season()
        season_rules = SeasonRules()
    else:
        season = db.session.query(Season).filter_by(id=entity_id).first()
        season_rules = db.session.query(SeasonRules).filter_by(id=season.id).first()

    return season, season_rules


def season_get(db: SQLAlchemy, entity_id: int):
    table = []
    for season in db.session.query(Season).order_by(Season.short_name).filter_by(league_id=database.get_selected_league().id).all():
        table.append([season.name + (f" (active)" if season.is_selected else ""), season.short_name, season.id])

    season_and_rules = __get_season_and_rules(db, entity_id)

    season = season_and_rules[0]
    season_rules = season_and_rules[1]

    if entity_id == 0:
        selected_season = database.get_selected_season()
        if selected_season is None:
            scorings_text_area = Scorings.DEFAULT_SCORINGS_ENTRY
        else:
            scorings_text_area = formatting.generate_scorings_field_value(selected_season.id)
        form = forms.AddSeasonForm(team_short_name_length=season_rules.team_short_name_length,
                                   number_of_allowed_matches=season_rules.number_of_allowed_matches,
                                   number_of_allowed_matches_vs_same_opponent=season_rules.number_of_allowed_matches_vs_same_opponent,
                                   number_of_playoff_places=season_rules.number_of_playoff_places,
                                   term_for_team_names=season_rules.term_for_team_names,
                                   term_for_coaches=season_rules.term_for_coaches,
                                   term_for_races=season_rules.term_for_races,
                                   scorings=scorings_text_area)
    else:
        scorings_text_area = formatting.generate_scorings_field_value(season.id)
        form = forms.UpdateSeasonForm(name=season.name,
                                      short_name=season.short_name,
                                      team_short_name_length=season_rules.team_short_name_length,
                                      number_of_allowed_matches=season_rules.number_of_allowed_matches,
                                      number_of_allowed_matches_vs_same_opponent=season_rules.number_of_allowed_matches_vs_same_opponent,
                                      number_of_playoff_places=season_rules.number_of_playoff_places,
                                      term_for_team_names=season_rules.term_for_team_names,
                                      term_for_coaches=season_rules.term_for_coaches,
                                      term_for_races=season_rules.term_for_races,
                                      scorings=scorings_text_area)
    return {FORM_KEY: form, "title": "Seasons", "title_row": ["Name", "Short name"], "table": table}


def season_submit(form: BaseSeasonForm, db: SQLAlchemy, entity_id: int):
    season, season_rules = __get_season_and_rules(db, entity_id)

    season.league_id = database.get_selected_league().id
    season.name = form.name.data.strip()
    season.short_name = form.short_name.data.strip()

    selected_season = database.get_selected_season()
    if entity_id == 0:
        season.is_selected = True

        if selected_season is not None:
            selected_season.is_selected = False
            db.session.add(selected_season)

    db.session.add(season)
    db.session.commit()

    season_rules.season_id = selected_season.id
    season_rules.team_short_name_length = form.team_short_name_length.data
    season_rules.number_of_allowed_matches = form.number_of_allowed_matches.data
    season_rules.number_of_allowed_matches_vs_same_opponent = form.number_of_allowed_matches_vs_same_opponent.data
    season_rules.number_of_playoff_places = form.number_of_playoff_places.data
    season_rules.term_for_team_names = form.term_for_team_names.data.strip()
    season_rules.term_for_coaches = form.term_for_coaches.data.strip()
    season_rules.term_for_races = form.term_for_races.data.strip()

    db.session.add(season_rules)
    db.session.commit()

    database.persist_scorings(form.scorings.data, season.id)

    return redirect(url_for("manage", entity_type=Season.__tablename__))


def __get_coach(db: SQLAlchemy, entity_id: int) -> Coach:
    coach: Coach
    if entity_id == 0:
        coach = Coach()
    else:
        coach = db.session.query(Coach).filter_by(id=entity_id).first()

    return coach


def coach_get(db: SQLAlchemy, entity_id: int) -> dict:
    table = []
    for coach in db.session.query(Coach).filter_by(league_id=database.get_selected_league().id).order_by(Coach.first_name).all():
        table.append([coach.first_name, coach.last_name, coach.display_name, coach.id])

    coach = __get_coach(db, entity_id)
    if entity_id == 0:
        form = forms.AddCoachForm()
    else:
        form = forms.UpdateCoachForm(first_name=coach.first_name, last_name=coach.last_name, display_name=coach.display_name)
    return {FORM_KEY: form, "title": "Coaches", "title_row": ["First Name", "Last Name", "Display Name"], "table": table}


def coach_submit(form: BaseCoachForm, db: SQLAlchemy, entity_id: int):
    coach = __get_coach(db, entity_id)
    coach.first_name = form.first_name.data.strip()
    coach.last_name = form.last_name.data.strip()
    coach.display_name = form.display_name.data.strip() if form.display_name.data is not None else None

    return persist_and_redirect(coach, Coach.__tablename__, db)


def __get_race(db: SQLAlchemy, entity_id: int) -> Race:
    race: Race
    if entity_id == 0:
        race = Race()
    else:
        race = db.session.query(Race).filter_by(id=entity_id).first()

    return race


def race_get(db: SQLAlchemy, entity_id: int) -> dict:
    table = []
    for race in db.session.query(Race).order_by(Race.name).all():
        table.append([race.name, race.id])

    race = __get_race(db, entity_id)

    if entity_id == 0:
        form = forms.AddRaceForm()
    else:
        form = forms.UpdateRaceForm(name=race.name)

    return {FORM_KEY: form, "title": "Races", "title_row": ["Name"], "table": table}


def race_submit(form: BaseRaceForm, db: SQLAlchemy, entity_id: int):
    race = __get_race(db, entity_id)
    race.name = form.name.data

    return persist_and_redirect(race, Race.__tablename__, db)


def __get_team(db: SQLAlchemy, entity_id: int) -> Team:
    team: Team
    if entity_id == 0:
        team = Team()
    else:
        team = db.session.query(Team).filter_by(id=entity_id).first()

    return team


def team_get(app: Flask, db: SQLAlchemy, entity_id: int) -> dict:
    table = []
    selected_season = database.get_selected_season()
    for team in db.session.query(Team).filter_by(season_id=selected_season.id).order_by(Team.name).all():
        coach = db.session.query(Coach).filter_by(id=team.coach_id).first()
        race = db.session.query(Race).filter_by(id=team.race_id).first()
        table.append([team.name, team.short_name, formatting.format_coach(coach), race.name, team.is_disqualified, team.id])

    team = __get_team(db, entity_id)
    if entity_id == 0:
        form = forms.AddTeamForm(app=app)
    else:
        form = forms.UpdateTeamForm(app=app, name=team.name, coach_select=team.coach_id, race_select=team.race_id, is_disqualified=team.is_disqualified)

    return {FORM_KEY: form, "title": "Teams", "title_row": ["Name", "Short name", "Coach", "Race", "Disqualified"], "table": table}


def team_submit(form: BaseTeamForm, db: SQLAlchemy, entity_id: int):
    team = __get_team(db, entity_id)
    team.season_id = database.get_selected_season().id
    team.name = form.name.data.strip()
    team.short_name = formatting.generate_team_short_name(team.name)
    team.coach_id = form.coach_select.data
    team.race_id = form.race_select.data

    if type(form) == UpdateTeamForm:
        team.is_disqualified = form.is_disqualified.data

    return persist_and_redirect(team, Team.__tablename__, db)
