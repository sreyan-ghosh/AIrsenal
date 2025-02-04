from airsenal.framework.utils import (
    get_past_seasons,
    session,
    CURRENT_SEASON,
    get_fixtures_for_season,
    get_player_scores,
)
from airsenal.framework.schema import PlayerScore

from airsenal.framework.season import get_teams_for_season

CHECK_SEASONS = [CURRENT_SEASON] + get_past_seasons(3)
SEPARATOR = "\n" + ("=" * 50) + "\n"  # used to separate groups of print statements


def result_string(n_error):
    """make string representing check result

    Arguments:
        n_error {int} -- number of errors encountered during check
    """
    if n_error == 0:
        return "OK!"
    else:
        return "FAIL! {} errors.".format(n_error)


def season_num_teams(seasons=CHECK_SEASONS, session=session):
    """Check whether each season has 20 teams.

    Keyword Arguments:
        seasons {list} -- seasons to check (default: {CHECK_SEASONS})
    """
    print("Checking seasons have 20 teams...\n")
    n_error = 0
    for season in seasons:
        teams = get_teams_for_season(season, session)
        if len(teams) != 20:
            n_error += 1
            print(
                "Number of teams in {} season is {} (not 20)".format(season, len(teams))
            )

    print("\n", result_string(n_error))
    return n_error


def season_num_new_teams(seasons=CHECK_SEASONS, session=session):
    """Check each season has 3 new teams.

    Keyword Arguments:
        seasons {list} -- seasons to check (default: {CHECK_SEASONS})
    """
    print("Checking seasons have 3 new teams...\n")
    n_error = 0

    teams = [get_teams_for_season(season, session) for season in seasons]
    for i in range(1, len(teams)):
        new_teams = [team for team in teams[i] if team not in teams[i - 1]]
        if len(new_teams) != 3:
            n_error += 1
            print(
                "Number of teams changed between {} and {} is {} (not 3)".format(
                    seasons[i - 1], seasons[i], len(new_teams)
                )
            )

    print("\n", result_string(n_error))
    return n_error


def season_num_fixtures(seasons=CHECK_SEASONS, session=session):
    """Check each season has 380 fixtures.

    Keyword Arguments:
        seasons {list} -- seasons to check (default: CHECK_SEASONS)
        session {SQLAlchemy session} -- DB session (default:
        airsenal.framework.schema.session)
    """
    print("Checking seasons have 380 fixtures...\n")
    n_error = 0

    for season in seasons:
        fixtures = get_fixtures_for_season(season=season)
        if len(fixtures) != 380:
            n_error += 1
            print(
                "Number of fixtures in {} season is {} (not 380)".format(
                    season, len(fixtures)
                )
            )

    print("\n", result_string(n_error))
    return n_error


def fixture_player_teams(seasons=CHECK_SEASONS, session=session):
    """Check players who played in a match are labelled as playing for either
    the home team or the away team.

    Keyword Arguments:
        seasons {[type]} -- seasons to check (default: {CHECK_SEASONS})
        session {SQLAlchemy session} -- DB session (default:
        airsenal.framework.schema.session)
    """
    print("Checking player teams match fixture teams...\n")
    n_error = 0

    for season in seasons:
        fixtures = get_fixtures_for_season(season=season)

        for fixture in fixtures:
            if fixture.result:
                player_scores = get_player_scores(fixture=fixture)

                for score in player_scores:
                    if score.player_team not in [
                        fixture.home_team,
                        fixture.away_team,
                    ]:
                        n_error += 1
                        msg = (
                            "{}: {} in player_scores but labelled as playing for {}."
                        ).format(
                            fixture,
                            score.player,
                            score.player_team,
                        )
                        print(msg)

    print("\n", result_string(n_error))
    return n_error


def fixture_num_players(seasons=CHECK_SEASONS, session=session):
    """Check each fixture has between 11 and 14 players  with at least 1 minute
    in player_scores. For season 19/20 it can be up to 16 players.

    Keyword Arguments:
        seasons {[type]} -- seasons to check (default: {CHECK_SEASONS})
        session {SQLAlchemy session} -- DB session (default:
        airsenal.framework.schema.session)
    """
    print(
        "Checking 11 to 14 players play per team in each fixture...\n"
        "Note:\n"
        "- 2019/20: 5 subs allowed after Covid-19 lockdown (accounted for in checks)\n"
        "- From 2020/21: Concussion subs allowed (may cause false errors)\n"
    )
    n_error = 0

    for season in seasons:
        fixtures = get_fixtures_for_season(season=season)

        for fixture in fixtures:
            result = fixture.result

            if result:
                home_scores = (
                    session.query(PlayerScore)
                    .filter_by(fixture=fixture, player_team=fixture.home_team)
                    .filter(PlayerScore.minutes > 0)
                    .all()
                )

                away_scores = (
                    session.query(PlayerScore)
                    .filter_by(fixture=fixture, player_team=fixture.away_team)
                    .filter(PlayerScore.minutes > 0)
                    .all()
                )

                # Rule change due to shorter season
                if fixture.season == "1920" and int(fixture.gameweek) >= 39:
                    upper_team_limit = 16
                else:
                    upper_team_limit = 14

                if not (
                    (len(home_scores) > 10) and (len(home_scores) <= upper_team_limit)
                ):
                    n_error += 1
                    print(
                        "{}: {} players with minutes > 0 for home team.".format(
                            result, len(home_scores)
                        )
                    )

                if not (
                    (len(away_scores) > 10) and (len(away_scores) <= upper_team_limit)
                ):
                    n_error += 1
                    print(
                        "{}: {} players with minutes > 0 for away team.".format(
                            result, len(away_scores)
                        )
                    )

    print("\n", result_string(n_error))
    return n_error


def fixture_num_goals(seasons=CHECK_SEASONS, session=session):
    """Check individual player goals sum to match result for each fixture.

    Keyword Arguments:
        seasons {[type]} -- seasons to check (default: {CHECK_SEASONS})
        session {SQLAlchemy session} -- DB session (default:
        airsenal.framework.schema.session)
    """
    print("Checking sum of player goals equals match results...\n")
    n_error = 0

    for season in seasons:
        fixtures = get_fixtures_for_season(season=season)

        for fixture in fixtures:
            result = fixture.result

            if result:
                home_scores = (
                    session.query(PlayerScore)
                    .filter_by(fixture=fixture, player_team=fixture.home_team)
                    .all()
                )

                away_scores = (
                    session.query(PlayerScore)
                    .filter_by(fixture=fixture, player_team=fixture.away_team)
                    .all()
                )

                home_goals = sum(score.goals for score in home_scores) + sum(
                    score.own_goals for score in away_scores
                )

                away_goals = sum(score.goals for score in away_scores) + sum(
                    score.own_goals for score in home_scores
                )

                if home_goals != result.home_score:
                    n_error += 1
                    msg = (
                        "{}: Player scores sum to {} but {} goals in result "
                        "for home team"
                    ).format(
                        result,
                        home_goals,
                        result.home_score,
                    )
                    print(msg)

                if away_goals != result.away_score:
                    n_error += 1
                    msg = (
                        "{}: Player scores sum to {} but {} goals in result "
                        "for away team"
                    ).format(
                        result,
                        away_goals,
                        result.away_score,
                    )
                    print(msg)

    print("\n", result_string(n_error))
    return n_error


def fixture_num_assists(seasons=CHECK_SEASONS, session=session):
    """Check number of assists is less than or equal to number of goals
    for home and away team in each fixture.
    Less than or equal to as some goals do not result in an assist being
    awarded.

    Keyword Arguments:
        seasons {[type]} -- seasons to check (default: {CHECK_SEASONS})
        session {SQLAlchemy session} -- DB session (default:
        airsenal.framework.schema.session)
    """
    print("Checking no. assists less than or equal to no. goals...\n")
    n_error = 0

    for season in seasons:
        fixtures = get_fixtures_for_season(season=season)

        for fixture in fixtures:
            result = fixture.result
            if result:
                home_scores = (
                    session.query(PlayerScore)
                    .filter_by(fixture=fixture, player_team=fixture.home_team)
                    .all()
                )

                away_scores = (
                    session.query(PlayerScore)
                    .filter_by(fixture=fixture, player_team=fixture.away_team)
                    .all()
                )

                home_assists = sum(score.assists for score in home_scores)
                away_assists = sum(score.assists for score in away_scores)

                if home_assists > result.home_score:
                    n_error += 1
                    msg = (
                        "{}: Player assists sum to {} but {} goals in result "
                        "for home team"
                    ).format(
                        result,
                        home_assists,
                        result.home_score,
                    )
                    print(msg)

                if away_assists > result.away_score:
                    n_error += 1
                    msg = (
                        "{}: Player assists sum to {} but {} goals in result "
                        "for away team"
                    ).format(
                        result,
                        away_assists,
                        result.away_score,
                    )
                    print(msg)

    print("\n", result_string(n_error))
    return n_error


def fixture_num_conceded(seasons=CHECK_SEASONS, session=session):
    """Check number of goals concdeded equals goals scored by opposition if
    player played whole match (90 minutes).
    NB: only checks max of player conceded values to avoid potential issues
    with substitutes and goals in stoppage time.

    Keyword Arguments:
        seasons {[type]} -- seasons to check (default: {CHECK_SEASONS})
        session {SQLAlchemy session} -- DB session (default:
        airsenal.framework.schema.session)
    """
    print("Checking no. goals conceded matches goals scored by opponent...\n")
    n_error = 0

    for season in seasons:
        fixtures = get_fixtures_for_season(season=season)

        for fixture in fixtures:
            result = fixture.result
            if result:
                home_scores = (
                    session.query(PlayerScore)
                    .filter_by(
                        fixture=fixture, player_team=fixture.home_team, minutes=90
                    )
                    .all()
                )

                away_scores = (
                    session.query(PlayerScore)
                    .filter_by(
                        fixture=fixture, player_team=fixture.away_team, minutes=90
                    )
                    .all()
                )

                home_conceded = max(score.conceded for score in home_scores)
                away_conceded = max(score.conceded for score in away_scores)

                if home_conceded != result.away_score:
                    n_error += 1
                    msg = "{}: Player conceded {} but {} goals in result for home team"
                    msg = msg.format(
                        result,
                        home_conceded,
                        result.away_score,
                    )
                    print(msg)

                if away_conceded != result.home_score:
                    n_error += 1
                    msg = "{}: Player conceded {} but {} goals in result for away team"
                    msg = msg.format(
                        result,
                        away_conceded,
                        result.home_score,
                    )
                    print(msg)

    print("\n", result_string(n_error))
    return n_error


def run_all_checks(seasons=CHECK_SEASONS):
    print("Running checks for seasons:", seasons)
    print(SEPARATOR)

    functions = {
        "season_num_teams": season_num_teams,
        "season_num_new_teams": season_num_new_teams,
        "season_num_fixtures": season_num_fixtures,
        "fixture_player_teams": fixture_player_teams,
        "fixture_num_players": fixture_num_players,
        "fixture_num_goals": fixture_num_goals,
        "fixture_num_assists": fixture_num_assists,
        "fixture_num_conceded": fixture_num_conceded,
    }
    results = {}

    for name, fn in functions.items():
        results[name] = fn(seasons)
        print(SEPARATOR)

    print("SUMMARY\n-------")
    print("Seasons:", seasons, "\n")
    for name, res in results.items():
        print("{}: {}".format(name, result_string(res)))

    n_tests = len(functions)
    n_passed = sum(1 for _, r in results.items() if r == 0)
    n_total_errors = sum(r for _, r in results.items())
    print(
        "\nOVERALL: Passed {} out of {} tests with {} errors.".format(
            n_passed, n_tests, n_total_errors
        )
    )


if __name__ == "__main__":
    run_all_checks()
