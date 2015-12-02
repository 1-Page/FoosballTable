from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask.ext.uploads import UploadSet, IMAGES, configure_uploads, UploadNotAllowed

from models import Player, Team, Game, Stats
from db_access import DBAccess
import config
import tools

app = Flask(__name__)
Bootstrap(app)

db = DBAccess(database=config.DBNAME)

app.config['UPLOADS_DEFAULT_DEST'] = 'static/uploads'
#app.config['UPLOADS_DEFAULT_URL'] = ''

photos = UploadSet('photos', IMAGES)
configure_uploads(app, (photos,))


@app.errorhandler(405)
def method_not_allowed(error=None):
    app.logger.warning('Method Not Allowed: ' + request.method, )

    message = {
        'status': 405,
        'message': 'Method Not Allowed: ' + request.method,
    }
    resp = jsonify(message)
    resp.status_code = 405

    return resp


@app.route('/')
def home_page():
    game = db.get_open_game()
    if not game:
        return redirect(url_for("games_get_post"))
    else:
        return redirect(url_for('games_get', timestamp=game.timestamp))


@app.route('/players', methods=['GET', 'POST'])
def players_get_post():
    if request.method == 'POST':
        name = request.form['name']
        photoUrl = url_for('static', filename=config.DEFAULT_IMAGE)
        if 'photo' in request.files:
            fileStorage = request.files['photo']
            if fileStorage.filename != "":
                try:
                    photoName = photos.save(fileStorage)
                    photoUrl = photos.url(photoName)
                except UploadNotAllowed:
                    photoUrl = url_for('static', filename=config.DEFAULT_IMAGE)

        db.create_player(name=name, photo=photoUrl)

    all_players = db.get_all_players()


    return render_template('players.html', players=all_players)


@app.route('/players/<name>')
def players_name_get(name):
    player = db.get_player_by_name(name=name)
    player_stats = db.get_all_stats(player_id=player.player_id)
    attacker_stats = db.get_all_stats(attack_player_id=player.player_id)
    defender_stats = db.get_all_stats(defense_player_id=player.player_id)
    return render_template('player_page.html', player=player, player_stats=player_stats, attacker_stats=attacker_stats, defender_stats=defender_stats)


@app.route('/players/<name>/edit', methods=['POST', 'GET'])
def player_name_edit(name):
    if request.method == 'GET':
        redirect(url_for('players_name_get', name=name))

    player = db.get_player_by_name(name=name)


    new_name = request.form['name']
    photoUrl = player.photo
    if 'photo' in request.files:
        fileStorage = request.files['photo']
        if fileStorage.filename != "":
            try:
                photoName = photos.save(fileStorage)
                photoUrl = photos.url(photoName)
            except UploadNotAllowed:
                #return to default if wrong file is given
                photoUrl = url_for('static', filename=config.DEFAULT_IMAGE)

    edited_player = db.edit_player(player_name=name, new_player_name=new_name, new_player_photo=photoUrl)
    return redirect(url_for('players_name_get', name=edited_player.name))

@app.route('/teams')
def teams_get():
    all_teams = db.get_all_teams()
    return render_template('teams.html', teams=all_teams)


@app.route('/teams/<team_id>', methods=['GET'])
def teams_name_get(team_id):
    team = db.get_team(team_id=team_id)
    team_stats = db.get_all_stats(team_id=team_id)
    return render_template('team_page.html', team=team, team_stats=team_stats)


@app.route('/games', methods=['GET', 'POST'])
def games_get_post():
    all_players = db.get_all_players()

    if request.method == 'POST':
        left_defense_player_name = request.form['left_defense_player_name']
        left_attack_player_name = request.form['left_attack_player_name']
        right_defense_player_name = request.form['right_defense_player_name']
        right_attack_player_name = request.form['right_attack_player_name']

        timestamp = tools.get_timestamp_for_now()
        left_team = db.create_team(defense_player=db.get_player_by_name(left_defense_player_name),
                                   attack_player=db.get_player_by_name(left_attack_player_name))
        right_team = db.create_team(defense_player=db.get_player_by_name(right_defense_player_name),
                                    attack_player=db.get_player_by_name(right_attack_player_name))

        game = db.create_update_game(timestamp=timestamp, left_team=left_team, right_team=right_team)
        return redirect(url_for('games_get', timestamp=game.timestamp))

    else:
        all_games = db.get_all_games()
        return render_template('games.html', players=all_players, games=all_games)


@app.route('/games/<timestamp>', methods=['GET', 'PUT', 'DELETE', 'POST'])
def games_get(timestamp):
    all_players = db.get_all_players()
    game = db.get_game_by_timestamp(timestamp)
    return render_template('game_page.html', game=game, players=all_players)


@app.route('/games/<timestamp>/delete', methods=['POST'])
def game_timestamp_delete(timestamp):
    if request.method == 'GET':
        redirect(url_for('games_get', timestamp=timestamp))

    db.delete_game_by_timestamp(timestamp)
    return redirect(url_for('games_get_post'))




@app.route('/games/ajax/<timestamp>', methods=['GET', 'PUT', 'DELETE', 'POST'])
def games_get_score_and_time(timestamp):
    game = db.get_game_by_timestamp(timestamp)
    output = {'score': "{} x {}".format(game.left_score, game.right_score),
              'time': game.time_left_string(),
              'ended': bool(game.ended)}
    return jsonify(output)


@app.route('/games/<timestamp>/end', methods=['GET'])
def end_game(timestamp):
    # ignoring timestamp, close everything
    db.end_all_opened_games()
    return redirect(url_for('games_get', timestamp=timestamp))


@app.route('/goal/<side>', methods=['POST'])
def goal(side):
    goal_value(side, value=1)
    print "Received" + request.data
    return "OK"

@app.route('/goal/<side>/<value>', methods=['POST'])
def goal_value(side, value):
    db.goal(side=side, value=int(value))
    print "Received" + request.data
    return "OK"


@app.route('/is_game_on', methods=['GET'])
def is_game_on():
    game = db.get_open_game()
    if game:
        return "Yes"
    else:
        return "No"

@app.route('/stats', methods=['GET'])
def stats_get():
    all_players = db.get_all_players()

    players_ranking = list(enumerate(sorted(all_players, key=lambda p: p.player_stats.elo_rating, reverse=True)))
    attack_ranking = list(enumerate(sorted(all_players, key=lambda p: p.attack_stats.elo_rating, reverse=True)))
    defense_ranking = list(enumerate(sorted(all_players, key=lambda p: p.defense_stats.elo_rating, reverse=True)))
    win_perc_ranking = list(enumerate(sorted(all_players, key=lambda p: p.player_stats.perc_win(), reverse=True)))

    all_teams = db.get_all_teams()
    team_ranking = list(enumerate(sorted(all_teams, key=lambda t: t.team_stats.elo_rating, reverse=True)))
    return render_template('stats_page.html', players_ranking=players_ranking, attack_ranking=attack_ranking, defense_ranking=defense_ranking, team_ranking=team_ranking, win_perc_ranking=win_perc_ranking)



@app.route('/redo_stats', methods=['GET'])
def redo_stats():
    db.recalculate_stats()
    return "Stats recalculated"


photos = UploadSet('photos', IMAGES)

@app.route('/photo/<id>')
def show(id):
    photo = Photo.load(id)
    if photo is None:
        abort(404)
    url = photos.url(photo.filename)
    return render_template('show.html', url=url, photo=photo)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=False, port=7008)
