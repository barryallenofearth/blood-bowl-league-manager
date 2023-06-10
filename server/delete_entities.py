from collections import defaultdict

from sqlalchemy import or_

from database.database import db, BBMatch, Team, Season, Coach, Race

SUCCESSFULLY_DELETED = "successfully deleted"


def league_delete(id: int):
    return SUCCESSFULLY_DELETED


def season_delete(id: int):
    return SUCCESSFULLY_DELETED


def scoring_delete(id: int):
    return SUCCESSFULLY_DELETED


def race_delete(id: int):
    race = db.session.query(Race).filter_by(id=id).first()

    race_teams = db.session.query(Team).filter_by(race_id=id).all()
    if len(race_teams) > 0:
        teams_and_seasons = defaultdict(list)
        for team in race_teams:
            teams_and_seasons[team.season_id].append(team.name)

        error_message = f"Could not delete race {race}. There are still the following teams connected to this race:"
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

        error_message = f"Could not delete coach {coach}. There are still the following teams connected to this coach:"
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


def match_delete(id: int):
    bb_match = db.session.query(BBMatch).filter_by(id=id).first()
    db.session.delete(bb_match)
    db.session.commit()
