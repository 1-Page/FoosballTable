from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask.ext.uploads import UploadSet, IMAGES, configure_uploads, UploadNotAllowed


from model import Player, Team, Game, AFL_DB
import config
import tools

app = Flask(__name__)
Bootstrap(app)

db = AFL_DB(database=config.DBNAME)

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


@app.route('/players/<name>', methods=['GET', 'DELETE', 'PUT'])
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


@app.route('/teams/<team_id>', methods=['GET'])
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

        timestamp = tools.get_timestamp_for_now()
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


@app.route('/games/<timestamp>', methods=['GET', 'PUT', 'DELETE', 'POST'])
def games_get(timestamp):
    all_players = db.get_all_players()
    game = db.get_game_by_timestamp(timestamp)
    return render_template('game.html', game=game, players=all_players)


@app.route('/games/ajax/<timestamp>', methods=['GET', 'PUT', 'DELETE', 'POST'])
def games_get_score_and_time(timestamp):
    game = db.get_game_by_timestamp(timestamp)
    output = {'score': "{} x {}".format(game.score_left, game.score_right),
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
    db.goal(side=side)
    print "Received" + request.data
    return "OK"


@app.route('/is_game_on', methods=['GET'])
def is_game_on():
    game = db.get_open_game()
    if game:
        return "Yes"
    else:
        return "No"


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
