from flask import Flask, request, render_template, redirect, url_for, Response
from flask_bootstrap import Bootstrap

from model import Player, Team, Game, AFL_DB
import config
import tools
import time

import json
from gevent.queue import Queue

app = Flask(__name__)
Bootstrap(app)

db = AFL_DB(database=config.DBNAME)


#queue = Queue()


@app.errorhandler(405)
def method_not_allowed(error=None):
    app.logger.warning('Method Not Allowed: ' + request.method, )

    message = 'Method Not Allowed: ' + request.method,

    return message


@app.route('/')
def home_page():
    game = db.get_open_game()
    if not game:
        return redirect(url_for("games_get_post"))
    else:
        return redirect(url_for('games_get', timestamp=game.timestamp))

@app.route('/players',methods=['GET', 'POST'])
def players_get_post():
    if request.method == 'POST':
        name = request.form['name']
        db.create_player(name=name)

    all_players = db.get_all_players()

    return render_template('players.html', players=all_players)

@app.route('/players/<name>',methods=['GET', 'DELETE', 'PUT'])
def players_name_get_delete_put(name):
    if request.method == 'GET':
        player = db.get_player_by_name(name=name)
        return render_template('player_page.html', player=player)
    elif request.method == 'DELETE':
        return "DELETE {name}: NOT IMPLEMENTED YET ".format(name=name)
    elif request.method == 'PUT':
        player = db.create_player(name)
        return "PUT {name}: NOT IMPLEMENTED YET ".format(name=name)
    else:
        return method_not_allowed()

@app.route('/teams')
def teams_get():
    all_teams = db.get_all_teams()
    return render_template('teams.html', teams=all_teams)

@app.route('/teams/<team_id>',methods=['GET'])
def teams_name_get(team_id):
    team = db.get_team(team_id=team_id)
    return render_template('team_page.html', team=team)

@app.route('/games', methods=['GET', 'POST'])
def games_get_post():

    all_players = db.get_all_players()

    if request.method == 'POST':
        left_defense_player_name = request.form['left_defense_player_name']
        left_attack_player_name = request.form['left_attack_player_name']
        right_defense_player_name = request.form['right_defense_player_name']
        right_attack_player_name = request.form['right_attack_player_name']

        timestamp = tools.getTimestampForNow()
        team_left = db.create_team(defense_player=db.get_player_by_name(left_defense_player_name),
                                   attack_player=db.get_player_by_name(left_attack_player_name))
        team_right = db.create_team(defense_player=db.get_player_by_name(right_defense_player_name),
                                   attack_player=db.get_player_by_name(right_attack_player_name))

        print "RIGHT", team_right.summary()
        print "LEFT", team_left.summary()

        game = db.create_update_game(timestamp=timestamp, team_left=team_left, team_right=team_right)
        return redirect(url_for('games_get', timestamp=timestamp))

    else:
        all_games = db.get_all_games()
        return render_template('games.html', players=all_players, games=all_games)



@app.route('/games/<timestamp>',methods=['GET'])
def games_get(timestamp):
    all_players = db.get_all_players()
    game = db.get_game_by_timestamp(timestamp)
    return render_template('game.html', game=game, players=all_players)


def yield_game_score(timestamp):
    previous_game_json = ""
    game = db.get_game_by_timestamp(timestamp)
    game_json = game.to_json()
    while not game.ended:

        if game != previous_game_json:
            previous_game_json = game_json
            yield "data: "+game_json+"\n\n"

        else:
            time.sleep(1)
            game = db.get_game_by_timestamp(timestamp)
            game_json = game.to_json()
        #todo: rethink this by adding a message between POST goal and yield


@app.route('/games/<timestamp>/score')
def get_game_score(timestamp):
    return Response(yield_game_score(timestamp), mimetype="text/event-stream")

@app.route('/games/<timestamp>/end',methods=['GET'])
def end_game(timestamp):
    # ignoring timestamp, close everything
    db._end_all_opened_games()
    return redirect(url_for('games_get', timestamp=timestamp))

@app.route('/goal/<side>',methods=['POST'])
def goal(side):
    db.goal(side=side)
    #queue.put(1)
    print "Received"+request.data
    return "OK"

@app.route('/is_game_on',methods=['GET'])
def is_game_on():
    game = db.get_open_game()
    if game:
        return "Yes"
    else:
        return "No"



"""
import socket
import SocketServer

def patched_finish(self):
    try:
        if not self.wfile.closed:
            self.wfile.flush()
            self.wfile.close()
    except socket.error:
        # Remove this code, if you don't need access to the Request object
            # More cleanup code...
        pass
    self.rfile.close()

SocketServer.StreamRequestHandler.finish = patched_finish
"""

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', threaded=True, port=7008)
