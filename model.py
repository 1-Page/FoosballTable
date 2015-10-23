import config
import tools
import sqlite3 as lite


class Player(object):
    def __init__(self, player_id, name, photo):
        self.player_id = player_id
        self.name = name
        self.photo = photo

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Team(object):
    def __init__(self, team_id, defense_player, attack_player):
        self.team_id = team_id
        self.defense_player = defense_player
        self.attack_player = attack_player

    def summary(self):
        if self.defense_player == self.attack_player:
            return "{defense}".format(defense=self.defense_player.name)
        else:
            return "{defense}+{attack}".format(defense=self.defense_player.name, attack=self.attack_player.name)


class Game(object):
    def __init__(self, game_id, timestamp, team_left, team_right, score_left=0, score_right=0, ended=0):
        self.game_id = game_id
        self.timestamp = timestamp
        self.team_left = team_left
        self.team_right = team_right
        self.score_left = score_left
        self.score_right = score_right
        self.ended = ended

    def goal_scored(self, side, value=1):
        if side == config.RIGHT:
            self.score_right += value
            return self.score_right
        elif side == config.LEFT:
            self.score_left += value
            return self.score_left
        else:
            return 0

    def time_left(self):
        return config.GAME_TIME_LIMIT - tools.get_seconds_from_timestamp(self.timestamp)

    def time_left_string(self):
        return tools.seconds_string(self.time_left())

    def game_should_end(self):
        should_end = ((self.score_left >= config.GAME_GOAL_LIMIT) or (self.score_right >= config.GAME_GOAL_LIMIT)) or \
                     (self.time_left() < 0)

        if should_end:
            self.ended = 1

        return should_end

    def summary(self):
        if self.ended == 0:
            return "Game in progress between {tleft} and {tright} the score is {sleft}x{sright}".format(
                tleft=self.team_left.summary(), tright=self.team_right.summary(), sleft=self.score_left,
                sright=self.score_right)
        elif self.score_left == self.score_right:
            return "Draw between {tleft} and {tright} the score was {sleft}x{sright}".format(
                tleft=self.team_left.summary(), tright=self.team_right.summary(), sleft=self.score_left,
                sright=self.score_right)
        elif self.score_right < self.score_left:
            return "{tleft} defeated {tright} with the score {sleft}x{sright}".format(tleft=self.team_left.summary(),
                                                                                      tright=self.team_right.summary(),
                                                                                      sleft=self.score_left,
                                                                                      sright=self.score_right)
        else:
            return "{tright} defeated {tleft} with the score {sright}x{sleft}".format(tleft=self.team_left.summary(),
                                                                                      tright=self.team_right.summary(),
                                                                                      sleft=self.score_left,
                                                                                      sright=self.score_right)


class AFL_DB:
    con = None

    def __init__(self, database):
        self.con = lite.connect(database=database, check_same_thread=False)
        self._create_all_tables()

    def __del__(self):
        if self.con:
            self.con.close()

    def _create_all_tables(self):
        cur = self.con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS players (player_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS teams (team_id INTEGER PRIMARY KEY AUTOINCREMENT, defense_player INT, attack_player INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS games (game_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, team_left INT, team_right INT, score_left INT, score_right INT, ended INT)")

    def get_player_by_name(self, name):
        cur = self.con.cursor()

        player_dict = dict(name=name)

        cur.execute("SELECT player_id, name, photo FROM players WHERE name LIKE :name", player_dict)
        player_exists = cur.fetchone()
        if player_exists:
            player_id, _, photo = player_exists
            return Player(player_id=player_id, name=name, photo=photo)
        else:
            return None

    def get_player(self, player_id):
        cur = self.con.cursor()

        cur.execute("SELECT player_id, name, photo FROM players WHERE player_id = :player_id", dict(player_id=player_id))
        player_exists = cur.fetchone()
        if player_exists:
            player_id, name, photo = player_exists
            return Player(player_id=player_id, name=name, photo=photo)
        else:
            return None

    def get_all_players(self):
        cur = self.con.cursor()
        cur.execute("SELECT player_id, name, photo FROM players")
        all_players = list(cur.fetchall())
        return [Player(player_id=player_id, name=name, photo=photo) for player_id, name, photo in all_players]

    def create_player(self, name, photo):
        cur = self.con.cursor()

        if self.get_player_by_name(name=name):
            return None
        else:
            player_dict = dict(name=name, photo=photo)
            cur.execute("INSERT INTO players(name, photo) VALUES(:name, :photo)", player_dict)
            self.con.commit()
            player_id = cur.lastrowid
            return Player(player_id=player_id, name=name, photo=photo)

    def edit_player(self, player_name, new_player_name, new_player_photo):
        cur = self.con.cursor()

        player = self.get_player_by_name(name=player_name)
        if not player:
            return None
        else:
            player_dict = dict(name=new_player_name, photo=new_player_photo, player_id=player.player_id)
            cur.execute("UPDATE players SET name = :name, photo = :photo WHERE player_id = :player_id", player_dict)
            self.con.commit()
            return Player(**player_dict)


    def get_all_teams(self):
        cur = self.con.cursor()
        cur.execute("SELECT team_id, defense_player, attack_player FROM teams")
        all_teams = list(cur.fetchall())
        return [Team(team_id=team_id, defense_player=self.get_player(player_id=defense_player),
                     attack_player=self.get_player(player_id=attack_player))
                for team_id, defense_player, attack_player in all_teams]

    def get_team(self, team_id):
        cur = self.con.cursor()

        cur.execute("SELECT team_id, defense_player, attack_player FROM teams WHERE team_id = :team_id",
                    dict(team_id=team_id))
        team_exists = cur.fetchone()
        if team_exists:
            team_id, defense_player, attack_player = team_exists
            return Team(team_id=team_id, defense_player=self.get_player(player_id=defense_player),
                        attack_player=self.get_player(player_id=attack_player))
        else:
            return None

    def create_team(self, defense_player, attack_player):

        cur = self.con.cursor()

        team_dict = dict(defense_player=defense_player, attack_player=attack_player)
        team_dict_sql = dict(defense_player=defense_player.player_id, attack_player=attack_player.player_id)

        cur.execute(
            "SELECT team_id, defense_player, attack_player FROM teams WHERE defense_player=:defense_player AND attack_player=:attack_player",
            team_dict_sql)
        team_exists = cur.fetchone()
        if team_exists:
            team_id, _, _ = team_exists
            return Team(team_id=team_id, **team_dict)
        else:
            cur.execute("INSERT INTO teams(defense_player, attack_player) VALUES(:defense_player, :attack_player)",
                        team_dict_sql)
            self.con.commit()
            team_id = cur.lastrowid
            return Team(team_id=team_id, **team_dict)

    def get_all_games(self):
        cur = self.con.cursor()
        cur.execute(
            "SELECT game_id, timestamp, team_left, team_right, score_left, score_right, ended FROM games ORDER BY TIMESTAMP DESC")

        all_games = list(cur.fetchall())
        return [Game(game_id=game_id, timestamp=timestamp,
                     team_left=self.get_team(team_left_id), team_right=self.get_team(team_right_id),
                     score_left=score_left, score_right=score_right, ended=ended)
                for game_id, timestamp, team_left_id, team_right_id, score_left, score_right, ended in all_games]

    def get_game_by_timestamp(self, timestamp):
        cur = self.con.cursor()

        cur.execute("SELECT game_id, timestamp, team_left, team_right, score_left, score_right, ended " +
                    "FROM games WHERE timestamp=:timestamp", dict(timestamp=timestamp))
        game_exists = cur.fetchone()
        if game_exists:
            game_id, _, team_left_id, team_right_id, score_left, score_right, ended = game_exists
            game = Game(game_id=game_id, timestamp=timestamp,
                        team_left=self.get_team(team_left_id), team_right=self.get_team(team_right_id),
                        score_left=score_left, score_right=score_right, ended=ended)

            if game.game_should_end():
                self.end_game(game)
            return game
        else:
            return None

    def create_update_game(self, timestamp, team_left, team_right, score_left=0, score_right=0, ended=0):
        cur = self.con.cursor()
        # todo: check some sort of upsert

        game_dict = dict(timestamp=timestamp, team_left=team_left.team_id, team_right=team_right.team_id,
                         score_left=score_left, score_right=score_right, ended=ended)

        previous_game = self.get_game_by_timestamp(timestamp=timestamp)
        if previous_game:
            cur.execute("UPDATE games SET timestamp = :timestamp, team_left = :team_left, team_right = :team_right, " +
                        "score_left = :score_left, score_right = :score_right, ended = :ended " +
                        "WHERE game_id = :game_id",
                        dict(game_id=previous_game.game_id, **game_dict))
            self.con.commit()
            game_id = previous_game.game_id
        else:
            self.end_all_opened_games()
            cur.execute("INSERT INTO games(timestamp, team_left, team_right, score_left, score_right, ended) " +
                        "VALUES(:timestamp, :team_left, :team_right, :score_left, :score_right, :ended)", game_dict)

            self.con.commit()
            game_id = cur.lastrowid

    def end_all_opened_games(self):
        cur = self.con.cursor()

        cur.execute("SELECT game_id, timestamp, team_left, team_right, score_left, score_right, ended " +
                    "FROM games WHERE ended=:ended", dict(ended=0))
        open_games = list(cur.fetchall())
        for (game_id, timestamp, _, _, score_left, score_right, ended) in open_games:
            cur.execute("UPDATE games SET ended = :ended WHERE game_id = :game_id",
                        dict(game_id=game_id, ended=1))
            self.con.commit()

    def _end_games_that_shouldnt_be_open(self):
        cur = self.con.cursor()

        cur.execute("SELECT game_id, timestamp, team_left, team_right, score_left, score_right, ended " +
                    "FROM games WHERE ended=:ended", dict(ended=0))
        open_games = list(cur.fetchall())
        for (game_id, timestamp, _, _, score_left, score_right, ended) in open_games:
            game = Game(game_id=game_id, team_left=None, team_right=None, timestamp=timestamp, score_left=score_left,
                        score_right=score_right, ended=ended)
            if game.game_should_end():
                self.end_game(game)

    def get_open_game(self):
        self._end_games_that_shouldnt_be_open()

        cur = self.con.cursor()

        cur.execute("SELECT game_id, timestamp, team_left, team_right, score_left, score_right, ended " +
                    "FROM games WHERE ended=:ended ORDER BY game_id desc", dict(ended=0))

        open_game = cur.fetchone()
        if open_game:
            game_id, timestamp, team_left_id, team_right_id, score_left, score_right, ended = open_game
            return Game(game_id=game_id, timestamp=timestamp,
                        team_left=self.get_team(team_left_id), team_right=self.get_team(team_right_id),
                        score_left=score_left, score_right=score_right, ended=ended)
        else:
            return None

    def goal(self, side, value=1):
        open_game = self.get_open_game()
        open_game.goal_scored(side=side, value=value)

        cur = self.con.cursor()

        cur.execute("UPDATE games SET score_left = :score_left, score_right = :score_right, ended = :ended " +
                    "WHERE game_id = :game_id",
                    dict(game_id=open_game.game_id,
                         score_left=open_game.score_left,
                         score_right=open_game.score_right,
                         ended=open_game.ended))
        self.con.commit()

        if open_game.game_should_end():
            self.end_game(open_game)

    def end_game(self, game):
        cur = self.con.cursor()
        cur.execute("UPDATE games SET ended = :ended WHERE game_id = :game_id",
                    dict(game_id=game.game_id, ended=1))
        self.con.commit()
