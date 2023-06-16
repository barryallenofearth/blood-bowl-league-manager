from collections import defaultdict

from sqlalchemy import or_

from database import database
from database.database import db, BBMatch, Team, Season, Coach, Race, Scorings, League, SeasonRules, AdditionalStatistics
from util import formatting

SUCCESSFULLY_DELETED = "successfully deleted"


def league_delete(id: int):
    league = db.session.query(League).filter_by(id=id).first()

    seasons = db.session.query(Season).filter_by(league_id=id).all()
    if len(seasons) > 0:
        error_message = f"Could not delete league {league.name}. There are still the following seasons connected to this league:\n - "
        error_message += '\n - '.join([season.name for season in seasons])
        return error_message

    db.session.delete(league)
    db.session.commit()
    return SUCCESSFULLY_DELETED


def season_delete(id: int):
    season = db.session.query(Season).filter_by(id=id).first()

    teams = db.session.query(Team).filter_by(season_id=id).all()
    if len(teams) > 0:
        error_message = f"Could not delete season {season.name}. There are still the following teams connected to this season:\n - "
        error_message += '\n - '.join([team.name for team in teams])
        return error_message

    season_rules = db.session.query(SeasonRules).filter_by(season_id=id).first()
    for scorings in db.session.query(Scorings).filter_by(season_id=season_rules.id).all():
        db.session.delete(db.session.query(Scorings).filter_by(id=scorings.id).first())

    db.session.delete(season_rules)
    db.session.delete(season)

    db.session.commit()
    return SUCCESSFULLY_DELETED


def scoring_delete(id: int):
    db.session.delete(db.session.query(Scorings).filter_by(id=id).first())
    db.session.commit()
    return SUCCESSFULLY_DELETED


def race_delete(id: int):
    race = db.session.query(Race).filter_by(id=id).first()

    race_teams = db.session.query(Team).filter_by(race_id=id).all()
    if len(race_teams) > 0:
        teams_and_seasons = defaultdict(list)
        for team in race_teams:
            teams_and_seasons[team.season_id].append(team.name)

        error_message = f"Could not delete race {race.name}. There are still the following teams connected to this race:"
        for season_id, teams in teams_and_seasons.items():
            team_names = '\n - '.join(teams)
            error_message += f"\n{db.session.query(Season).filter_by(id=season_id).first().name}:\n - {team_names}"

        return error_message

    db.session.delete(race)
    db.session.commit()
    return SUCCESSFULLY_DELETED


def coach_delete(id: int) -> str:
    coach = db.session.query(Coach).filter_by(id=id).first()

    coaches_teams = db.session.query(Team).filter_by(coach_id=id).all()
    if len(coaches_teams) > 0:
        teams_and_seasons = defaultdict(list)
        for team in coaches_teams:
            teams_and_seasons[team.season_id].append(team.name)

        error_message = f"Could not delete coach {formatting.format_coach(coach)}. There are still the following teams connected to this coach:"
        for season_id, teams in teams_and_seasons.items():
            team_names = '\n - '.join(teams)
            error_message += f"\n{db.session.query(Season).filter_by(id=season_id).first().name}:\n - {team_names}"

        return error_message

    db.session.delete(coach)
    db.session.commit()
    return SUCCESSFULLY_DELETED


def team_delete(id: int):
    team_matches = db.session.query(BBMatch).filter(or_(BBMatch.team_1_id == id, BBMatch.team_2_id == id)).all()
    team = db.session.query(Team).filter_by(id=id).first()
    if len(team_matches) > 0:
        error_message = f"Could not delete team {team.name}. There are still the following matches connected to this team:"
        for match in team_matches:
            error_message += "\n" + str(match)

        team.is_disqualified = True
        db.session.add(team)

    db.session.delete(team)
    db.session.commit()
    return SUCCESSFULLY_DELETED


def match_delete(id: int) -> str:
    bb_match = db.session.query(BBMatch).filter_by(id=id).first()
    match_number = bb_match.match_number
    db.session.delete(bb_match)
    db.session.commit()

    highest_match_number = database.highest_match_number()
    if match_number != highest_match_number:
        season = database.get_selected_season()
        all_matches = db.session.query(BBMatch) \
            .filter_by(season_id=season.id) \
            .filter(BBMatch.match_number >= match_number) \
            .all()

        for match in all_matches:
            match.match_number = match.match_number - 1
            db.session.add(match)

        db.session.commit()

    return SUCCESSFULLY_DELETED


def additional_statistics_delete(id: int) -> str:
    additional_statistics = db.session.query(AdditionalStatistics).filter_by(id=id).first()
    db.session.delete(additional_statistics)
    db.session.commit()

    return SUCCESSFULLY_DELETED
