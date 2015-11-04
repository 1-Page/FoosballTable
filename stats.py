from model import *
import math
import config
import tools


# We = 1/ (10 (-D/F) + 1);
def wining_expectancy(difference_weight):
    return 1.0 / (math.pow(10.0, -difference_weight / config.F) + 1)


# Rn = Ro + K(S-We)
def rating_increment(score_perc, diff_ratings):
    return config.K * (score_perc * wining_expectancy(diff_ratings))


class Stats:
    def __init__(self,
                 stats_id,
                 player_id=None,
                 attacker_id=None,
                 defender_id=None,
                 team_id=None,
                 wins=0, draws=0, loses=0,
                 goals_pro=0, goals_against=0,
                 elo_rating=config.INITIAL_RATING,
                 timestamp=tools.get_timestamp_for_now()):

        self.stats_id = stats_id

        assert 1 == (player_id is not None) + (attacker_id is not None) + (defender_id is not None) + (team_id is not None), "Use only one of these (player_id, attacker_id, defender_id, team_id)"
        self.player_id = player_id
        self.attacker_id = attacker_id
        self.defender_id = defender_id
        self.team_id = team_id

        self.wins = wins
        self.draws = draws
        self.loses = loses

        self.goals_pro = goals_pro
        self.goals_against = goals_against

        self.elo_rating = elo_rating

        self.timestamp = timestamp


class StatsDB:
    con = None

    def __init__(self, con):
        self.con = con
        self._create_table()

    def _create_table(self):
        cur = self.con.cursor()
        s = """
              CREATE TABLE IF NOT EXISTS stats (stats_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                player_id INT, attacker_id INT, defender_id INT, team_id INT,
                                                wins INT, draws INT, loses INT,
                                                goals_pro INT, goals_against INT,
                                                elo_rating NUMBER,
                                                timestamp TEXT)
            """
        cur.execute(s)
        self.con.commit()


    def add_stats(self,
                  player_id=None,
                  attacker_id=None,
                  defender_id=None,
                  team_id=None,
                  wins=0, draws=0, loses=0,
                  goals_pro=0, goals_against=0,
                  elo_rating=config.INITIAL_RATING,
                  timestamp=tools.get_timestamp_for_now()):

            stat_dict = dict(player_id=player_id, attacker_id=attacker_id, defender_id=defender_id, team_id=team_id,
                             wins=wins, draws=draws, loses=loses,
                             goals_pro=goals_pro, goals_against=goals_against,
                             elo_rating=elo_rating, timestamp=timestamp)

            s = """
                  INSERT INTO stats(player_id, attacker_id, defender_id, team_id,
                                    wins, draws, loses,
                                    goals_pro, goals_against,
                                    elo_rating, timestamp)
                          VALUES(:player_id, :attacker_id, :defender_id, :team_id,
                                 :wins, :draws, :loses,
                                 :goals_pro, :goals_against,
                                 :elo_rating, :timestamp)
                """

            cur = self.con.cursor()
            cur.execute(s, stat_dict)
            self.con.commit()

