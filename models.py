import config
import tools
import elo


class Player(object):
    def __init__(self, player_id, name, photo, player_stats, attack_stats, defense_stats):
        self.player_id = player_id
        self.name = name
        self.photo = photo
        self.player_stats = player_stats
        self.attack_stats = attack_stats
        self.defense_stats = defense_stats

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Team(object):
    def __init__(self, team_id, defense_player, attack_player, team_stats):
        self.team_id = team_id
        self.defense_player = defense_player
        self.attack_player = attack_player
        self.team_stats = team_stats

    def summary(self):
        if self.defense_player == self.attack_player:
            return "{defense}".format(defense=self.defense_player.name)
        else:
            return "{defense}+{attack}".format(defense=self.defense_player.name, attack=self.attack_player.name)


class Game(object):
    def __init__(self, game_id, timestamp, left_team, right_team, left_score=0, right_score=0, ended=0):
        self.game_id = game_id
        self.timestamp = timestamp
        self.left_team = left_team
        self.right_team = right_team
        self.left_score = left_score
        self.right_score = right_score
        self.ended = ended

    def goal_scored(self, side, value=1):
        if side == config.RIGHT:
            self.right_score += value
            return self.right_score
        elif side == config.LEFT:
            self.left_score += value
            return self.left_score
        else:
            return 0

    def time_left(self):
        return config.GAME_TIME_LIMIT - tools.get_seconds_from_timestamp(self.timestamp)

    def time_left_string(self):
        return tools.seconds_string(self.time_left())

    def game_should_end(self):
        should_end = (not self.ended) and ((((self.left_score >= config.GAME_GOAL_LIMIT) or \
                                             (self.right_score >= config.GAME_GOAL_LIMIT)) or \
                                            (self.time_left() < 0)))

        if should_end:
            self.ended = 1

        return should_end

    def summary(self):
        sum_dict = dict(tleft=self.left_team.summary(), tright=self.right_team.summary(), sleft=self.left_score, sright=self.right_score)

        if self.ended == 0:
            return "Game in progress between {tleft} and {tright} the score is {sleft}x{sright}".format(**sum_dict)
        elif self.left_score == self.right_score:
            return "Draw between {tleft} and {tright} the score was {sleft}x{sright}".format(**sum_dict)
        elif self.right_score < self.left_score:
            return "{tleft} defeated {tright} with the score {sleft}x{sright}".format(**sum_dict)
        else:
            return "{tright} defeated {tleft} with the score {sright}x{sleft}".format(**sum_dict)



class Stats:
    def __init__(self,
                 stats_id=None,
                 player_id=None,
                 attack_player_id=None,
                 defense_player_id=None,
                 team_id=None,
                 wins=0, draws=0, losses=0,
                 goals_pro=0, goals_against=0,
                 elo_rating=elo.INITIAL_RATING,
                 timestamp=tools.get_timestamp_for_now()):

        self.stats_id = stats_id

        assert 1 == (player_id is not None) + (attack_player_id is not None) + (defense_player_id is not None) + (team_id is not None), "Use only one of these (player_id, attacker_id, defender_id, team_id)"
        self.player_id = player_id
        self.attack_player_id = attack_player_id
        self.defense_player_id = defense_player_id
        self.team_id = team_id

        self.wins = wins
        self.draws = draws
        self.losses = losses

        self.goals_pro = goals_pro
        self.goals_against = goals_against

        self.elo_rating = elo_rating

        self.timestamp = timestamp

    def elo_rating_str(self):
        return "%2.0f"%self.elo_rating

    def update(self, i_wins=0, i_draws=0, i_losses=0, i_goals_pro=0, i_goals_against=0, i_elo_rating=0, timestamp=tools.get_timestamp_for_now()):
        self.wins += i_wins
        self.draws += i_draws
        self.losses += i_losses
        self.goals_pro += i_goals_pro
        self.goals_against += i_goals_against
        self.elo_rating += i_elo_rating
        self.timestamp = timestamp