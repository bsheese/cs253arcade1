from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
from random import randint


import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, g, redirect, url_for, render_template, flash


app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'scores.db'),
    DEBUG=True,
    SECRET_KEY='development key',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()







def add_score(name, score):
    conn = get_db_connection()
    conn.execute('INSERT INTO high_scores (name, score) VALUES (?, ?)', (name, score))
    conn.commit()
    conn.close()

def get_high_scores(limit=10):
    conn = get_db_connection()
    scores = conn.execute('SELECT name, score FROM high_scores ORDER BY score DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return scores

# Manually pushing the application context
with app.app_context():
    init_db()

@app.route('/add_score', methods=['POST'])
def add_score_route():
    score_data = request.json
    add_score(score_data['name'], score_data['score'])
    return jsonify({'message': 'Score added successfully!'}), 201

@app.route('/high_scores', methods=['GET'])
def get_high_scores_route():
    scores = get_high_scores()
    return jsonify([{'name': row['name'], 'score': row['score']} for row in scores])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/snake')
def snake():
    return render_template('snake.html')

@app.route('/hilo')
def hilo():
    # Initialize points to 100 if it's not already in the session
    if 'hilo_points' not in session:
        session['hilo_points'] = 100

    # Retrieve points from session
    points = session['hilo_points']

    if 'hilo_errors' not in session:
        session['hilo_errors'] = 3

    errors = session['hilo_errors']
    if errors == 0:
        final_points = session['hilo_points']
        session['hilo_points'] = 100 # reset game points
        session['hilo_errors'] = 3 # reset errors
        top_scores = get_high_scores()
        return render_template('hilo_gameover.html',
                               points = final_points,
                               top_scores = top_scores)

    while True:
        number_first = randint(1,10)
        number_second = randint(1,10)
        if number_first != number_second:
            break

    return render_template('hilo.html',
                           points=points,
                           errors = errors,
                           number_first = number_first,
                           number_second = number_second)


@app.route('/hilo_guess', methods=['POST'])
def hilo_guess():
    number_first = int(request.form.get('number_first'))
    number_second = int(request.form.get('number_second'))
    guess = request.form.get('guess')
    points = int(request.form.get('points'))

    # Update points and determine result based on the guess
    if guess == 'Higher' and number_second > number_first:
        result = 'correct'
        session['hilo_points'] += 50
    elif guess == 'Lower' and number_second < number_first:
        result = 'correct'
        session['hilo_points'] += 50
    else:
        result = 'incorrect'
        session['hilo_points'] -= 50
        session['hilo_errors'] -= 1

    return render_template('hilo_result.html',
                           number_first = number_first,
                           number_second = number_second,
                           result = result)


if __name__ == '__main__':
    app.run(debug=True)
