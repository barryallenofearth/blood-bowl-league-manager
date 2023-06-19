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
        error_message = f"<p>Could not delete league {league.name}.</p><p>There are still the following seasons connected to this league:</p><ul><li>"
        error_message += "</li><li>".join([season.name for season in seasons])
        error_message += "</li></ul>"
        return error_message

    success_message = f"<p>League {league.name} ({league.short_name}) successfully deleted.</p>"
    db.session.delete(league)
    db.session.commit()
    return success_message


def season_delete(id: int):
    season = db.session.query(Season).filter_by(id=id).first()

    teams = db.session.query(Team).filter_by(season_id=id).all()
    if len(teams) > 0:
        error_message = f"<p>Could not delete season {season.name}.</p><p>There are still the following teams connected to this season:</p><ul><li>"
        error_message += "</li><li>".join([team.name for team in teams])
        error_message += "</li></ul>"
        return error_message

    season_rules = db.session.query(SeasonRules).filter_by(season_id=id).first()
    for scorings in db.session.query(Scorings).filter_by(season_id=season_rules.id).all():
        db.session.delete(db.session.query(Scorings).filter_by(id=scorings.id).first())

    success_message = f"<p>Season {season.name} ({season.short_name}) successfully deleted.</p>"

    db.session.delete(season_rules)
    db.session.delete(season)

    db.session.commit()
    return success_message


def race_delete(id: int):
    race = db.session.query(Race).filter_by(id=id).first()

    race_teams = db.session.query(Team).filter_by(race_id=id).all()
    if len(race_teams) > 0:
        teams_and_seasons = defaultdict(list)
        for team in race_teams:
            teams_and_seasons[team.season_id].append(team.name)

        error_message = f"<p>Could not delete race {race.name}.</p><p>There are still the following teams connected to this race:</p><ul>"
        for season_id, teams in teams_and_seasons.items():
            season = db.session.query(Season).filter_by(id=season_id).first()
            error_message += f"<li>{season.name} ({season.short_name}):</li><ul><li>"
            team_names = "</li><li>".join(teams)
            error_message += f"{team_names}</li></ul>"
        error_message += "</ul>"

        return error_message

    success_message = f"<p>Race {race.name} successfully deleted.</p>"
    db.session.delete(race)
    db.session.commit()
    return success_message


def coach_delete(id: int) -> str:
    coach = db.session.query(Coach).filter_by(id=id).first()

    coaches_teams = db.session.query(Team).filter_by(coach_id=id).all()
    if len(coaches_teams) > 0:
        teams_and_seasons = defaultdict(list)
        for team in coaches_teams:
            teams_and_seasons[team.season_id].append(team.name)

        error_message = f"<p>Could not delete coach {formatting.format_coach(coach)}.</p><p>There are still the following teams connected to this coach:</p><ul>"
        for season_id, teams in teams_and_seasons.items():
            season = db.session.query(Season).filter_by(id=season_id).first()
            error_message += f"<li>Season {season.name} ({season.short_name})</li><ul><li>"
            team_names = "</li><li>".join(teams)
            error_message += f"{team_names}</li></ul>"
        error_message += "</ul>"

        return error_message

    success_message = f"<p>Coach {formatting.format_coach(coach.name)} successfully deleted.</p>"
    db.session.delete(coach)
    db.session.commit()
    return success_message


def team_delete(id: int):
    team_matches = db.session.query(BBMatch).filter(or_(BBMatch.team_1_id == id, BBMatch.team_2_id == id)).all()
    team = db.session.query(Team).filter_by(id=id).first()
    if len(team_matches) > 0:
        error_message = f"<p>Could not delete team {team.name}.</p><p>There are still the following matches connected to this team:</p><ul>"

        for match in team_matches:
            error_message += f"<li>{formatting.format_match(match)}</li>"
        error_message += "</ul>"
        return error_message

    success_message = f"<p>Team {formatting.format_team(team)} successfully deleted.</p>"
    db.session.delete(team)
    db.session.commit()

    return success_message


def match_delete(id: int) -> str:
    bb_match = db.session.query(BBMatch).filter_by(id=id).first()
    match_number = bb_match.match_number
    success_message = f"<p>Match {formatting.format_match(bb_match)} successfully deleted.</p>"
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

    return success_message


def additional_statistics_delete(id: int) -> str:
    additional_statistics = db.session.query(AdditionalStatistics).filter_by(id=id).first()
    success_message = f"<p>Casualties entry {formatting.format_additional_statistics(additional_statistics)} successfully deleted.</p>"
    db.session.delete(additional_statistics)
    db.session.commit()

    return success_message
