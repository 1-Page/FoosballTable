from models import Player, Team, Game, Stats

import tools
import elo

import sqlite3 as lite

import config


class DBAccess:
    con = None

    def __init__(self, database):
        self.con = lite.connect(database=database, check_same_thread=False)
        self._create_all_tables()

    def __del__(self):
        if self.con:
            self.con.close()

    def _create_all_tables(self):
        cur = self.con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS players (player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                           name TEXT, photo TEXT,
                                                           player_stats_id INT, attack_stats_id INT, defense_stats_id INT)""")

        cur.execute("CREATE TABLE IF NOT EXISTS teams (team_id INTEGER PRIMARY KEY AUTOINCREMENT, defense_player_id INT, attack_player_id INT, team_stats_id INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS games (game_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, left_team_id INT, right_team_id INT, left_score INT, right_score INT, ended INT)")

        cur.execute("""CREATE TABLE IF NOT EXISTS stats (stats_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                player_id INT, attack_player_id INT, defense_player_id INT, team_id INT,
                                                wins INT, draws INT, losses INT,
                                                goals_pro INT, goals_against INT,
                                                elo_rating NUMBER,
                                                timestamp TEXT)
            """)

        cur.execute("""CREATE TABLE IF NOT EXISTS hidden_players (player_id INTEGER)""")

        self.con.commit()

    def get_visible_players(self):
        return self.get_hidden_players(hidden=False)

    def get_hidden_players(self, hidden=True):
        cur = self.con.cursor()
        sql = """SELECT player_id, name, photo, player_stats_id, attack_stats_id, defense_stats_id FROM players
                 WHERE player_id {} in (SELECT player_id from hidden_players)""".format("not" if not hidden else "")
        cur.execute(sql)
        all_players = list(cur.fetchall())
        return [Player(player_id=player_id, name=name, photo=photo, player_stats=self.get_stats(player_stats_id), attack_stats=self.get_stats(attack_stats_id), defense_stats=self.get_stats(defense_stats_id))
                        for player_id, name, photo, player_stats_id, attack_stats_id, defense_stats_id in all_players]


    def hide_player(self, player_name, hidden):

        player = self.get_player_by_name(name=player_name)

        cur = self.con.cursor()
        cur.execute("SELECT player_id FROM hidden_players WHERE player_id = :player_id", dict(player_id=player.player_id))
        player_exists = cur.fetchone()
        if player_exists and not hidden:
            cur.execute("DELETE FROM hidden_players WHERE player_id = :player_id", dict(player_id=player.player_id))
        elif not player_exists and hidden:
            cur.execute("INSERT INTO hidden_players(player_id) VALUES(:player_id)", dict(player_id=player.player_id))

        self.con.commit()



    def get_player_by_name(self, name):
        cur = self.con.cursor()

        player_dict = dict(name=name)

        cur.execute("SELECT player_id, name, photo, player_stats_id, attack_stats_id, defense_stats_id FROM players WHERE name LIKE :name", player_dict)
        player_exists = cur.fetchone()
        if player_exists:
            player_id, _, photo, player_stats_id, attack_stats_id, defense_stats_id = player_exists
            return Player(player_id=player_id, name=name, photo=photo, player_stats=self.get_stats(player_stats_id), attack_stats=self.get_stats(attack_stats_id), defense_stats=self.get_stats(defense_stats_id))
        else:
            return None

    def get_player(self, player_id):
        cur = self.con.cursor()

        cur.execute("SELECT player_id, name, photo, player_stats_id, attack_stats_id, defense_stats_id  FROM players WHERE player_id = :player_id", dict(player_id=player_id))
        player_exists = cur.fetchone()
        if player_exists:
            player_id, name, photo, player_stats_id, attack_stats_id, defense_stats_id = player_exists
            return Player(player_id=player_id, name=name, photo=photo, player_stats=self.get_stats(player_stats_id), attack_stats=self.get_stats(attack_stats_id), defense_stats=self.get_stats(defense_stats_id))
        else:
            return None

    def get_all_players(self):
        cur = self.con.cursor()
        cur.execute("SELECT player_id, name, photo, player_stats_id, attack_stats_id, defense_stats_id FROM players")
        all_players = list(cur.fetchall())
        return [Player(player_id=player_id, name=name, photo=photo, player_stats=self.get_stats(player_stats_id), attack_stats=self.get_stats(attack_stats_id), defense_stats=self.get_stats(defense_stats_id))
                        for player_id, name, photo, player_stats_id, attack_stats_id, defense_stats_id in all_players]

    def create_player(self, name, photo):
        cur = self.con.cursor()

        if self.get_player_by_name(name=name):
            return None
        else:
            player_dict = dict(name=name, photo=photo)
            cur.execute("INSERT INTO players(name, photo) VALUES(:name, :photo)", player_dict)
            self.con.commit()
            player_id = cur.lastrowid

            player_stats = self.add_first_stats(player_id=player_id)
            attack_stats = self.add_first_stats(attack_player_id=player_id)
            defense_stats = self.add_first_stats(defense_player_id=player_id)

            self.update_player_stats(player_id=player_id,
                                     player_stats_id=player_stats.stats_id,
                                     attack_stats_id=attack_stats.stats_id,
                                     defense_stats_id=defense_stats.stats_id)

            return Player(player_id=player_id, name=name, photo=photo, player_stats=player_stats, attack_stats=attack_stats, defense_stats=defense_stats)

    def update_player_stats(self, player_id, player_stats_id, attack_stats_id, defense_stats_id):
        cur = self.con.cursor()
        cur.execute("UPDATE players SET player_stats_id = :player_stats_id, attack_stats_id = :attack_stats_id, defense_stats_id = :defense_stats_id   WHERE player_id = :player_id",
                    dict(player_id=player_id, player_stats_id=player_stats_id, attack_stats_id=attack_stats_id, defense_stats_id=defense_stats_id))
        self.con.commit()

    def edit_player(self, player_name, new_player_name, new_player_photo):
        cur = self.con.cursor()

        player = self.get_player_by_name(name=player_name)
        if not player:
            return None
        else:
            player_dict = dict(name=new_player_name, photo=new_player_photo, player_id=player.player_id)
            cur.execute("UPDATE players SET name = :name, photo = :photo WHERE player_id = :player_id", player_dict)
            self.con.commit()

            player.name = new_player_name
            player.photo = new_player_photo
            return player

    def edit_player(self, player_name, new_player_name, new_player_photo):
        cur = self.con.cursor()

        player = self.get_player_by_name(name=player_name)
        if not player:
            return None
        else:
            player_dict = dict(name=new_player_name, photo=new_player_photo, player_id=player.player_id)
            cur.execute("UPDATE players SET name = :name, photo = :photo WHERE player_id = :player_id", player_dict)
            self.con.commit()

            player.name = new_player_name
            player.photo = new_player_photo
            return player


    def get_all_teams(self):
        cur = self.con.cursor()
        cur.execute("SELECT team_id, defense_player_id, attack_player_id, team_stats_id FROM teams")
        self.con.commit()
        all_teams = list(cur.fetchall())
        return [Team(team_id=team_id,
                     defense_player=self.get_player(player_id=defense_player_id),
                     attack_player=self.get_player(player_id=attack_player_id),
                     team_stats=self.get_stats(team_stats_id))
                    for team_id, defense_player_id, attack_player_id, team_stats_id in all_teams]

    def get_team(self, team_id):
        cur = self.con.cursor()

        cur.execute("SELECT team_id, defense_player_id, attack_player_id, team_stats_id FROM teams WHERE team_id = :team_id",
                    dict(team_id=team_id))
        team_exists = cur.fetchone()
        if team_exists:
            team_id, defense_player_id, attack_player_id, team_stats_id  = team_exists
            return Team(team_id=team_id,
                        defense_player=self.get_player(player_id=defense_player_id),
                        attack_player=self.get_player(player_id=attack_player_id),
                        team_stats=self.get_stats(team_stats_id))
        else:
            return None

    def create_team(self, defense_player, attack_player):

        cur = self.con.cursor()

        team_dict = dict(defense_player=defense_player, attack_player=attack_player)
        team_dict_sql = dict(defense_player_id=defense_player.player_id, attack_player_id=attack_player.player_id)

        cur.execute(
            "SELECT team_id, defense_player_id, attack_player_id, team_stats_id FROM teams WHERE defense_player_id=:defense_player_id AND attack_player_id=:attack_player_id", team_dict_sql)
        team_exists = cur.fetchone()
        if team_exists:
            team_id, _, _, team_stats_id = team_exists
            return Team(team_id=team_id, team_stats=self.get_stats(team_stats_id), **team_dict)
        else:
            cur.execute("INSERT INTO teams(defense_player_id, attack_player_id) VALUES(:defense_player_id, :attack_player_id)",
                        team_dict_sql)
            self.con.commit()
            team_id = cur.lastrowid

            team_stats = self.add_first_stats(team_id=team_id)

            self.update_team_stats(team_id=team_id, team_stats_id=team_stats.stats_id)
            
            return Team(team_id=team_id, team_stats=team_stats, **team_dict)


    def update_team_stats(self, team_id, team_stats_id):
        cur = self.con.cursor()
        cur.execute("UPDATE teams SET team_stats_id = :team_stats_id WHERE team_id = :team_id",
                    dict(team_id=team_id, team_stats_id=team_stats_id))
        self.con.commit()


    def get_all_games(self):
        cur = self.con.cursor()
        cur.execute(
            "SELECT game_id, timestamp, left_team_id, right_team_id, left_score, right_score, ended FROM games ORDER BY TIMESTAMP DESC")

        all_games = list(cur.fetchall())
        return [Game(game_id=game_id, timestamp=timestamp,
                     left_team=self.get_team(left_team_id), right_team=self.get_team(right_team_id),
                     left_score=left_score, right_score=right_score, ended=ended)
                for game_id, timestamp, left_team_id, right_team_id, left_score, right_score, ended in all_games]

    def delete_game_by_timestamp(self, timestamp):
        cur = self.con.cursor()
        cur.execute("DELETE FROM games WHERE timestamp=:timestamp", dict(timestamp=timestamp))
        self.con.commit()
        self.recalculate_stats()




    def get_game_by_timestamp(self, timestamp):
        cur = self.con.cursor()

        cur.execute("SELECT game_id, timestamp, left_team_id, right_team_id, left_score, right_score, ended " +
                    "FROM games WHERE timestamp=:timestamp", dict(timestamp=timestamp))
        game_exists = cur.fetchone()
        if game_exists:
            game_id, _, left_team_id, right_team_id, left_score, right_score, ended = game_exists
            game = Game(game_id=game_id, timestamp=timestamp,
                        left_team=self.get_team(left_team_id), right_team=self.get_team(right_team_id),
                        left_score=left_score, right_score=right_score, ended=ended)

            if game.game_should_end():
                self.end_game(game)
            return game
        else:
            return None

    def create_update_game(self, timestamp, left_team, right_team, left_score=0, right_score=0, ended=0):
        cur = self.con.cursor()
        # todo: check some sort of upsert

        game_dict = dict(timestamp=timestamp, left_team=left_team, right_team=right_team,
                         left_score=left_score, right_score=right_score, ended=ended)

        game_dict_sql = dict(timestamp=timestamp, left_team_id=left_team.team_id, right_team_id=right_team.team_id,
                         left_score=left_score, right_score=right_score, ended=ended)

        previous_game = self.get_game_by_timestamp(timestamp=timestamp)
        if previous_game:
            cur.execute("UPDATE games SET timestamp = :timestamp, left_team_id = :left_team_id, right_team_id = :right_team_id, " +
                        "left_score = :left_score, right_score = :right_score, ended = :ended " +
                        "WHERE game_id = :game_id",
                        dict(game_id=previous_game.game_id, **game_dict_sql))
            self.con.commit()
            game_id = previous_game.game_id
        else:
            self.end_all_opened_games()
            cur.execute("INSERT INTO games(timestamp, left_team_id, right_team_id, left_score, right_score, ended) " +
                        "VALUES(:timestamp, :left_team_id, :right_team_id, :left_score, :right_score, :ended)", game_dict_sql)

            self.con.commit()
            game_id = cur.lastrowid

        return Game(game_id=game_id, **game_dict)


    def end_all_opened_games(self):
        cur = self.con.cursor()

        cur.execute("SELECT game_id, timestamp, left_team_id, right_team_id, left_score, right_score, ended " +
                    "FROM games WHERE ended=:ended", dict(ended=0))
        open_games = list(cur.fetchall())
        for (game_id, timestamp, _, _, left_score, right_score, ended) in open_games:
            cur.execute("UPDATE games SET ended = :ended WHERE game_id = :game_id",
                        dict(game_id=game_id, ended=1))
            self.con.commit()

    def _end_games_that_shouldnt_be_open(self):
        cur = self.con.cursor()

        cur.execute("SELECT game_id, timestamp, left_team_id, right_team_id, left_score, right_score, ended " +
                    "FROM games WHERE ended=:ended", dict(ended=0))
        open_games = list(cur.fetchall())
        for (game_id, timestamp, _, _, left_score, right_score, ended) in open_games:
            game = Game(game_id=game_id, left_team=None, right_team=None, timestamp=timestamp, left_score=left_score,
                        right_score=right_score, ended=ended)
            if game.game_should_end():
                self.end_game(game)

    def get_open_game(self):
        self._end_games_that_shouldnt_be_open()

        cur = self.con.cursor()

        cur.execute("SELECT game_id, timestamp, left_team_id, right_team_id, left_score, right_score, ended " +
                    "FROM games WHERE ended=:ended ORDER BY game_id desc", dict(ended=0))

        open_game = cur.fetchone()
        if open_game:
            game_id, timestamp, left_team_id, right_team_id, left_score, right_score, ended = open_game
            return Game(game_id=game_id, timestamp=timestamp,
                        left_team=self.get_team(left_team_id), right_team=self.get_team(right_team_id),
                        left_score=left_score, right_score=right_score, ended=ended)
        else:
            return None

    def goal(self, side, value=1):
        open_game = self.get_open_game()
        open_game.goal_scored(side=side, value=value)

        cur = self.con.cursor()

        cur.execute("UPDATE games SET left_score = :left_score, right_score = :right_score, ended = :ended " +
                    "WHERE game_id = :game_id",
                    dict(game_id=open_game.game_id,
                         left_score=open_game.left_score,
                         right_score=open_game.right_score,
                         ended=open_game.ended))
        self.con.commit()

        if open_game.game_should_end():
            self.end_game(open_game)

    def end_game(self, game):
        cur = self.con.cursor()
        cur.execute("UPDATE games SET ended = :ended WHERE game_id = :game_id",
                    dict(game_id=game.game_id, ended=1))
        self.con.commit()

        game.ended = 1
        self.add_stats_game(game=game)



    def get_stats(self, stats_id):
        cur = self.con.cursor()

        q = """ SELECT stats_id, player_id, attack_player_id, defense_player_id, team_id, wins, draws, losses, goals_pro, goals_against, elo_rating, timestamp
                FROM STATS
                WHERE stats_id = :stats_id
            """

        cur.execute(q, dict(stats_id=stats_id))

        stats_exists = cur.fetchone()
        if stats_exists:
            _, player_id, attack_player_id, defense_player_id, team_id, wins, draws, losses, goals_pro, goals_against, elo_rating, timestamp = stats_exists
            return Stats(stats_id=stats_id, player_id=player_id, attack_player_id=attack_player_id, defense_player_id=defense_player_id, team_id=team_id,
                         wins=wins, draws=draws, losses=losses, goals_pro=goals_pro, goals_against=goals_against,
                         elo_rating=elo_rating, timestamp=timestamp)

        else:
           return None




    def get_all_stats(self, player_id=None, attack_player_id=None, defense_player_id=None, team_id=None, limit=None):
        cur = self.con.cursor()

        assert 1 == (player_id is not None) + (attack_player_id is not None) + (defense_player_id is not None) + (team_id is not None), "Use only one of these (player_id, attacker_id, defender_id, team_id)"

        ids_dict = dict(player_id=player_id, attack_player_id=attack_player_id, defense_player_id=defense_player_id, team_id=team_id)

        if player_id:
            s_id = "player_id"
        elif attack_player_id:
            s_id = "attack_player_id"
        elif defense_player_id:
            s_id = "defense_player_id"
        elif team_id:
            s_id = "team_id"
        else:
            pass # will never happen
            raise Exception("Assert failed, this should never happen")

        q = """ SELECT player_id, attack_player_id, defense_player_id, team_id, wins, draws, losses, goals_pro, goals_against, elo_rating, timestamp
                FROM STATS
                WHERE {s_id}=:{s_id}
                ORDER BY timestamp DESC
            """.format(s_id=s_id)

        if limit:
            q += " LIMIT {limit}".format(limit=limit)

        cur.execute(q, ids_dict)

        all_stats = list(cur.fetchall())

        if len(all_stats) > 0:
            stats_list = [Stats(player_id=player_id, attack_player_id=attack_player_id, defense_player_id=defense_player_id, team_id=team_id,
                           wins=wins, draws=draws, losses=losses,
                           goals_pro=goals_pro, goals_against=goals_against, elo_rating=elo_rating, timestamp=timestamp)

                            for player_id, attack_player_id, defense_player_id, team_id, wins, draws, losses, goals_pro, goals_against, elo_rating, timestamp in all_stats]

        else:
            stats_list = [Stats(**ids_dict)]

        return stats_list


    def add_first_stats(self, player_id=None, attack_player_id=None, defense_player_id=None, team_id=None, timestamp=tools.get_timestamp_for_now()):
        return self.increment_stats(player_id=player_id, attack_player_id=attack_player_id, defense_player_id=defense_player_id, team_id=team_id, timestamp=timestamp)

    def increment_stats(self,
                        player_id=None,
                        attack_player_id=None,
                        defense_player_id=None,
                        team_id=None,
                        i_wins=0, i_draws=0, i_losses=0,
                        i_goals_pro=0, i_goals_against=0,
                        i_elo_rating=0,
                        timestamp=tools.get_timestamp_for_now()):
        """
            Increment the stats of a player, attacker, defender, or team based by certain values
        """

        cur = self.con.cursor()
        stats = self.get_all_stats(player_id=player_id, attack_player_id=attack_player_id, defense_player_id=defense_player_id, team_id=team_id, limit=1)[0]


        stats.update(i_wins=i_wins, i_draws=i_draws, i_losses=i_losses, i_goals_pro=i_goals_pro, i_goals_against=i_goals_against, i_elo_rating=i_elo_rating, timestamp=timestamp)


        s = """
              INSERT INTO stats(player_id, attack_player_id, defense_player_id, team_id,
                                wins, draws, losses,
                                goals_pro, goals_against,
                                elo_rating, timestamp)
                      VALUES(:player_id, :attack_player_id, :defense_player_id, :team_id,
                             :wins, :draws, :losses,
                             :goals_pro, :goals_against,
                             :elo_rating, :timestamp)
            """


        cur.execute(s, stats.__dict__)
        self.con.commit()

        stats.stats_id = cur.lastrowid
        return stats


    def add_stats_game(self, game):
        if not game.ended:
            raise Exception("Game not ended")

        stats_timestamp = game.timestamp

        game = self.get_game_by_timestamp(timestamp=stats_timestamp)

        # Get all stats

        elo_left_team = game.left_team.team_stats.elo_rating
        elo_right_team = game.right_team.team_stats.elo_rating
        elo_attack_left = game.left_team.attack_player.attack_stats.elo_rating
        elo_defense_left = game.left_team.defense_player.defense_stats.elo_rating
        elo_attack_right = game.right_team.attack_player.attack_stats.elo_rating
        elo_defense_right = game.right_team.defense_player.defense_stats.elo_rating

        elo_player_attack_left = game.left_team.attack_player.player_stats.elo_rating
        elo_player_defense_left = game.left_team.defense_player.player_stats.elo_rating
        elo_player_attack_right = game.right_team.attack_player.player_stats.elo_rating
        elo_player_defense_right = game.right_team.defense_player.player_stats.elo_rating


        # Score percentages

        if (game.left_score+game.right_score) != 0:
            score_p_left = game.left_score / float(game.left_score+game.right_score)
            score_p_right = 1.0 - score_p_left
        else:
            score_p_left = 0.5
            score_p_right = 0.5

        i_elo_left_team = elo.rating_increment(score_perc=score_p_left, diff_ratings=(elo_left_team - elo_right_team))
        i_elo_right_team = elo.rating_increment(score_perc=score_p_right, diff_ratings=(elo_right_team - elo_left_team))

        i_elo_left_players_pos = elo.rating_increment(score_perc=score_p_left, diff_ratings=((elo_attack_left+elo_defense_left) - (elo_attack_right+elo_defense_right)))
        i_elo_right_players_pos = elo.rating_increment(score_perc=score_p_right, diff_ratings=((elo_attack_right+elo_defense_right)-(elo_attack_left+elo_defense_left)))

        i_elo_left_players_ind = elo.rating_increment(score_perc=score_p_left, diff_ratings=((elo_player_attack_left+elo_player_defense_left) - (elo_player_attack_right+elo_player_defense_right)))
        i_elo_right_players_ind = elo.rating_increment(score_perc=score_p_right, diff_ratings=((elo_player_attack_right+elo_player_defense_right) - (elo_player_attack_left+elo_player_defense_left)))


        # Increments for left or right teams
        left_dict_goals_increment = dict(i_wins=int(game.left_score > game.right_score),
                                         i_draws=int(game.left_score == game.right_score),
                                         i_losses=int(game.left_score < game.right_score),
                                         i_goals_pro=game.left_score,
                                         i_goals_against=game.right_score,
                                         timestamp=stats_timestamp)

        right_dict_goals_increment = dict(i_wins=int(game.right_score > game.left_score),
                                          i_draws=int(game.left_score == game.right_score),
                                          i_losses=int(game.right_score < game.left_score),
                                          i_goals_pro=game.right_score,
                                          i_goals_against=game.left_score,
                                          timestamp=stats_timestamp)



        new_left_team_stats = self.increment_stats(team_id=game.left_team.team_id, i_elo_rating=i_elo_left_team, **left_dict_goals_increment)
        self.update_team_stats(team_id=game.left_team.team_id, team_stats_id=new_left_team_stats.stats_id)

        new_right_team_stats = self.increment_stats(team_id=game.right_team.team_id, i_elo_rating=i_elo_right_team, **right_dict_goals_increment)
        self.update_team_stats(team_id=game.right_team.team_id, team_stats_id=new_right_team_stats.stats_id)


        new_left_attack_attack_stats = self.increment_stats(attack_player_id=game.left_team.attack_player.player_id, i_elo_rating=i_elo_left_players_pos, **left_dict_goals_increment)
        new_left_attack_player_stats = self.increment_stats(player_id=game.left_team.attack_player.player_id, i_elo_rating=i_elo_left_players_ind, **left_dict_goals_increment)

        self.update_player_stats(player_id=game.left_team.attack_player.player_id,
                                 player_stats_id=new_left_attack_player_stats.stats_id,
                                 attack_stats_id=new_left_attack_attack_stats.stats_id,
                                 defense_stats_id=game.left_team.attack_player.defense_stats.stats_id) # not changed


        new_left_defense_defense_stats = self.increment_stats(defense_player_id=game.left_team.defense_player.player_id, i_elo_rating=i_elo_left_players_pos, **left_dict_goals_increment)
        if game.left_team.attack_player.player_id != game.left_team.defense_player.player_id:
            new_left_defense_player_stats = self.increment_stats(player_id=game.left_team.defense_player.player_id, i_elo_rating=i_elo_left_players_ind, **left_dict_goals_increment)
        else:
            new_left_defense_player_stats = new_left_attack_player_stats

        self.update_player_stats(player_id=game.left_team.defense_player.player_id,
                                 player_stats_id=new_left_defense_player_stats.stats_id,
                                 attack_stats_id=game.left_team.defense_player.attack_stats.stats_id, #not changed
                                 defense_stats_id=new_left_defense_defense_stats.stats_id)


        new_right_attack_attack_stats = self.increment_stats(attack_player_id=game.right_team.attack_player.player_id, i_elo_rating=i_elo_right_players_pos, **right_dict_goals_increment)
        new_right_attack_player_stats = self.increment_stats(player_id=game.right_team.attack_player.player_id, i_elo_rating=i_elo_right_players_ind, **right_dict_goals_increment)

        self.update_player_stats(player_id=game.right_team.attack_player.player_id,
                                 player_stats_id=new_right_attack_player_stats.stats_id,
                                 attack_stats_id=new_right_attack_attack_stats.stats_id,
                                 defense_stats_id=game.right_team.attack_player.defense_stats.stats_id) # not changed

        new_right_defense_defense_stats = self.increment_stats(defense_player_id=game.right_team.defense_player.player_id, i_elo_rating=i_elo_right_players_pos, **right_dict_goals_increment)
        if game.right_team.attack_player.player_id != game.right_team.defense_player.player_id:
            new_right_defense_player_stats = self.increment_stats(player_id=game.right_team.defense_player.player_id, i_elo_rating=i_elo_right_players_ind, **right_dict_goals_increment)
        else:
            new_right_defense_player_stats = new_right_attack_player_stats

        self.update_player_stats(player_id=game.right_team.defense_player.player_id,
                                 player_stats_id=new_right_defense_player_stats.stats_id,
                                 attack_stats_id=game.right_team.defense_player.attack_stats.stats_id, #not changed
                                 defense_stats_id=new_right_defense_defense_stats.stats_id)




    def recalculate_stats(self):
        cur = self.con.cursor()

        cur.execute("DELETE FROM STATS")
        self.con.commit()

        players = self.get_all_players()
        for player in players:
            player_stats = self.add_first_stats(player_id=player.player_id, timestamp=config.FIRST_TIMESTAMP)
            attack_stats = self.add_first_stats(attack_player_id=player.player_id, timestamp=config.FIRST_TIMESTAMP)
            defense_stats = self.add_first_stats(defense_player_id=player.player_id, timestamp=config.FIRST_TIMESTAMP)

            self.update_player_stats(player_id=player.player_id,
                                     player_stats_id=player_stats.stats_id,
                                     attack_stats_id=attack_stats.stats_id,
                                     defense_stats_id=defense_stats.stats_id)


        teams = self.get_all_teams()
        for team in teams:
            team_stats = self.add_first_stats(team_id=team.team_id, timestamp=config.FIRST_TIMESTAMP)
            self.update_team_stats(team_id=team.team_id, team_stats_id=team_stats.stats_id)

        games = reversed(self.get_all_games())
        for game in games:
            self.add_stats_game(game=game)


