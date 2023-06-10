from database.database import db, Team, Coach, BBMatch

def generate_team_short_name(team_name: str):
    # TODO generate proper team name
    return team_name
def format_coach(coach: Coach):
    string = f"{coach.first_name} {coach.last_name}"
    if coach.display_name is not None and coach.display_name != "":
        string += f" ({coach.display_name})"
    return string


def format_match(match: BBMatch):
    team1_name = db.session.query(Team).filter_by(match.team_1_id).first().name
    team2_name = db.session.query(Team).filter_by(match.team_2_id).first().name

    string = f"{team1_name} vs. {team2_name} : {match.team_1_touchdown}:{match.team_2_touchdown}"
    if match.team_1_surrendered:
        string += f" ({team1_name} surrendered)"
    if match.team_2_surrendered:
        string += f" ({team2_name} surrendered)"
    if match.team_1_point_modification is not None and match.team_1_point_modification != 0:
        string += f" ({match.team_1_point_modification} points for {team1_name})"
    if match.team_2_point_modification is not None and match.team_2_point_modification != 0:
        string += f" ({match.team_2_point_modification} points for {team2_name})"
    if match.is_playoff_match:
        string += " (Playoffs)"
    if match.is_tournament:
        string += " (Tournament)"

    return string
