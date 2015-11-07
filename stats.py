# from model import Player, Team, Game, AFL_DB
import math
import config
import tools


# We = 1/ (10 (-D/F) + 1);
def wining_expectancy(diff_ratings):
    return 1.0 / (math.pow(10.0, -diff_ratings / config.F) + 1)


# Rn = Ro + K(S-We)
def rating_increment(score_perc, diff_ratings):
    return config.K * (score_perc - wining_expectancy(diff_ratings))


class Stats:
    def __init__(self,
                 stats_id=None,
                 player_id=None,
                 attacker_id=None,
                 defender_id=None,
                 team_id=None,
                 wins=0, draws=0, losses=0,
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
        self.losses = losses

        self.goals_pro = goals_pro
        self.goals_against = goals_against

        self.elo_rating = elo_rating

        self.timestamp = timestamp


    def update(self, i_wins=0, i_draws=0, i_losses=0, i_goals_pro=0, i_goals_against=0, i_elo_rating=0, timestamp=tools.get_timestamp_for_now()):
        self.wins += i_wins
        self.draws += i_draws
        self.losses += i_losses
        self.goals_pro += i_goals_pro
        self.goals_against += i_goals_against
        self.elo_rating += i_elo_rating
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
                                                wins INT, draws INT, losses INT,
                                                goals_pro INT, goals_against INT,
                                                elo_rating NUMBER,
                                                timestamp TEXT)
            """
        cur.execute(s)
        self.con.commit()

    def get_stats(self, player_id=None, attacker_id=None, defender_id=None, team_id=None, limit=None):
        cur = self.con.cursor()

        assert 1 == (player_id is not None) + (attacker_id is not None) + (defender_id is not None) + (team_id is not None), "Use only one of these (player_id, attacker_id, defender_id, team_id)"

        ids_dict = dict(player_id=player_id, attacker_id=attacker_id, defender_id=defender_id, team_id=team_id)

        if player_id:
            s_id = "player_id"
        elif attacker_id:
            s_id = "attacker_id"
        elif defender_id:
            s_id = "defender_id"
        elif team_id:
            s_id = "team_id"
        else:
            pass # will never happen
            raise Exception("Assert failed, this should never happen")

        q = """
                SELECT player_id, attacker_id, defender_id, team_id, wins, draws, losses, goals_pro, goals_against, elo_rating, timestamp
                FROM STATS
                WHERE {s_id}=:{s_id}
                ORDER BY stats_id DESC
            """.format(s_id=s_id)

        if limit:
            q += " LIMIT {limit}".format(limit=limit)

        cur.execute(q, ids_dict)

        all_stats = list(cur.fetchall())

        if len(all_stats) > 0:
            stats_list = [Stats(player_id=player_id, attacker_id=attacker_id, defender_id=defender_id, team_id=team_id,
                           wins=wins, draws=draws, losses=losses,
                           goals_pro=goals_pro, goals_against=goals_against, elo_rating=elo_rating, timestamp=timestamp)

                            for player_id, attacker_id, defender_id, team_id, wins, draws, losses, goals_pro, goals_against, elo_rating, timestamp in all_stats]

        else:
            stats_list = [Stats(**ids_dict)]

        return stats_list


    def increment_stats(self,
                        player_id=None,
                        attacker_id=None,
                        defender_id=None,
                        team_id=None,
                        i_wins=0, i_draws=0, i_losses=0,
                        i_goals_pro=0, i_goals_against=0,
                        i_elo_rating=0,
                        timestamp=tools.get_timestamp_for_now()):
        """
            Increment the stats of a player, attacker, defender, or team based by certain values
        """

        cur = self.con.cursor()
        stats = self.get_stats(player_id=player_id, attacker_id=attacker_id, defender_id=defender_id, team_id=team_id, limit=1)[0]

        stats.update(i_wins=i_wins, i_draws=i_draws, i_losses=i_losses, i_goals_pro=i_goals_pro, i_goals_against=i_goals_against, i_elo_rating=i_elo_rating, timestamp=timestamp)


        s = """
              INSERT INTO stats(player_id, attacker_id, defender_id, team_id,
                                wins, draws, losses,
                                goals_pro, goals_against,
                                elo_rating, timestamp)
                      VALUES(:player_id, :attacker_id, :defender_id, :team_id,
                             :wins, :draws, :losses,
                             :goals_pro, :goals_against,
                             :elo_rating, :timestamp)
            """


        cur.execute(s, stats.__dict__)
        self.con.commit()

        stats.stats_id = cur.lastrowid

        return stats




    def add_game(self, game):
        if not game.ended:
            raise Exception("Game not ended")

        """
        game.timestamp = timestamp
        game.team_left = team_left
        game.team_right = team_right
        game.score_left = score_left
        game.score_right = score_right
        """

        stats_timestamp = game.timestamp

        # Get all stats

        elo_team_left = self.get_stats(team_id=game.team_left.team_id, limit=1)[0].elo_rating
        elo_team_right = self.get_stats(team_id=game.team_right.team_id, limit=1)[0].elo_rating
        elo_attack_left = self.get_stats(attacker_id=game.team_left.attack_player.player_id, limit=1)[0].elo_rating
        elo_defense_left = self.get_stats(defender_id=game.team_left.defense_player.player_id, limit=1)[0].elo_rating
        elo_attack_right = self.get_stats(attacker_id=game.team_right.attack_player.player_id, limit=1)[0].elo_rating
        elo_defense_right = self.get_stats(defender_id=game.team_right.defense_player.player_id, limit=1)[0].elo_rating

        elo_player_attack_left = self.get_stats(player_id=game.team_left.attack_player.player_id, limit=1)[0].elo_rating
        elo_player_defense_left = self.get_stats(player_id=game.team_left.defense_player.player_id, limit=1)[0].elo_rating
        elo_player_attack_right = self.get_stats(player_id=game.team_right.attack_player.player_id, limit=1)[0].elo_rating
        elo_player_defense_right = self.get_stats(player_id=game.team_right.defense_player.player_id, limit=1)[0].elo_rating

        # Score percentages

        if (game.score_left+game.score_right) != 0:
            score_p_left = game.score_left / float(game.score_left+game.score_right)
            score_p_right = 1.0 - score_p_left
        else:
            score_p_left = 0.5
            score_p_right = 0.5


        i_elo_team_left = rating_increment(score_perc=score_p_left, diff_ratings=(elo_team_left - elo_team_right))
        i_elo_team_right = rating_increment(score_perc=score_p_right, diff_ratings=(elo_team_right - elo_team_left))

        i_elo_left_players_pos = rating_increment(score_perc=score_p_left, diff_ratings=((elo_attack_left+elo_defense_left) - (elo_attack_right+elo_defense_right)))
        i_elo_right_players_pos = rating_increment(score_perc=score_p_right, diff_ratings=((elo_attack_right+elo_defense_right)-(elo_attack_left+elo_defense_left)))

        i_elo_left_players_ind = rating_increment(score_perc=score_p_left, diff_ratings=((elo_player_attack_left+elo_player_defense_left) - (elo_player_attack_right+elo_player_defense_right)))
        i_elo_right_players_ind = rating_increment(score_perc=score_p_right, diff_ratings=((elo_player_attack_right+elo_player_defense_right) - (elo_player_attack_left+elo_player_defense_left)))


        # Increments for left or right teams
        left_dict_goals_increment = dict(i_wins=int(game.score_left>game.score_right),
                                         i_draws=int(game.score_left==game.score_right),
                                         i_losses=int(game.score_left<game.score_right),
                                         i_goals_pro=game.score_left,
                                         i_goals_against=game.score_right,
                                         timestamp=stats_timestamp)

        right_dict_goals_increment = dict(i_wins=int(game.score_right>game.score_left),
                                          i_draws=int(game.score_left==game.score_right),
                                          i_losses=int(game.score_right<game.score_left),
                                          i_goals_pro=game.score_right,
                                          i_goals_against=game.score_left,
                                          timestamp=stats_timestamp)



        self.increment_stats(team_id=game.team_left.team_id,
                             i_elo_rating=i_elo_team_left,
                             **left_dict_goals_increment)

        self.increment_stats(team_id=game.team_right.team_id,
                             i_elo_rating=i_elo_team_right,
                             **right_dict_goals_increment)

        self.increment_stats(attacker_id=game.team_left.attack_player.player_id,
                             i_elo_rating=i_elo_left_players_pos,
                             **left_dict_goals_increment)

        self.increment_stats(defender_id=game.team_left.defense_player.player_id,
                             i_elo_rating=i_elo_left_players_pos,
                             **left_dict_goals_increment)

        self.increment_stats(attacker_id=game.team_right.attack_player.player_id,
                             i_elo_rating=i_elo_right_players_pos,
                             **right_dict_goals_increment)

        self.increment_stats(defender_id=game.team_right.defense_player.player_id,
                             i_elo_rating=i_elo_right_players_pos,
                             **right_dict_goals_increment)

        self.increment_stats(player_id=game.team_left.attack_player.player_id,
                             i_elo_rating=i_elo_left_players_ind,
                             **left_dict_goals_increment)

        if game.team_left.attack_player.player_id != game.team_left.defense_player.player_id:
            self.increment_stats(player_id=game.team_left.defense_player.player_id,
                                 i_elo_rating=i_elo_left_players_ind,
                                 **left_dict_goals_increment)

        self.increment_stats(player_id=game.team_right.attack_player.player_id,
                             i_elo_rating=i_elo_right_players_ind,
                             **right_dict_goals_increment)

        if game.team_right.attack_player.player_id != game.team_right.defense_player.player_id:
            self.increment_stats(player_id=game.team_right.defense_player.player_id,
                                 i_elo_rating=i_elo_right_players_ind,
                                 **right_dict_goals_increment)



    def recalculate_stats(self, games):
        cur = self.con.cursor()

        cur.execute("DELETE FROM STATS")
        self.con.commit()

        for game in games:
            self.add_game(game=game)

