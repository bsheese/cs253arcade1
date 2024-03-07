from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
from random import randint

app = Flask(__name__)
app.secret_key = 'your_secret_key' # Required for session management

DATABASE = 'highscores.db'
quiz_database = 'quiz.db'
quiz_score_database = 'quiz_score.db'
id_list = []


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    quiz = sqlite3.connect(quiz_database)
    quiz.row_factory = sqlite3.Row
    quiz_scores = sqlite3.connect(quiz_score_database)
    quiz_scores.row_factory = sqlite3.Row
    return conn, quiz, quiz_scores

def init_db():
    dbs = get_db_connection()
    db = dbs[0]
    db2 = dbs[1]
    db3 = dbs[2]
    db.execute('''
        CREATE TABLE IF NOT EXISTS high_scores (
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            score INTEGER
        )
    ''')
    db2.execute('''
        CREATE TABLE IF NOT EXISTS quiz (
            id INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            score INTEGER)''')
    db3.execute('''
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            score INTEGER
            )
        ''')
    db.commit()
    db.close()
    db2.commit()
    db2.close()
    db3.commit()
    db3.close()

# Manually pushing the application context
with app.app_context():
    init_db()


def add_score(name, score):
    conn = get_db_connection()[0]
    conn.execute('INSERT INTO high_scores (name, score) VALUES (?, ?)', (name, score))
    conn.commit()
    conn.close()

def get_high_scores(limit=10):
    conn = get_db_connection()[0]
    scores = conn.execute('SELECT name, score FROM high_scores ORDER BY score DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return scores

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



@app.route('/quiz')
def quiz():
    quiz = get_db_connection()[1]
    quiz_score = get_db_connection()[2]
    top_score_row = quiz_score.execute('SELECT * FROM quiz_scores ORDER BY score DESC LIMIT 1').fetchall()
    top_score = top_score_row[0][2]
    add_quiz_questions()
    if 'quiz_points' not in session:
        session['quiz_points'] = 0
    points = session['quiz_points']
    #
    if 'quiz_errors' not in session:
        session['quiz_errors'] = 3
    errors = session['quiz_errors']
    #
    if errors == 0:
        id_list.clear()
        final_points = session['quiz_points']
        session['quiz_points'] = 0 # reset game points
        session['quiz_errors'] = 3 # reset errors
        top_scores_quiz = get_high_scores_quiz()
        return render_template('quiz_gameover.html',
                               points=final_points,
                               top_scores=top_scores_quiz,
                               )
    if len(id_list) > 9:
        id_list.clear()
        final_points = session['quiz_points']
        session['quiz_points'] = 0  # reset game points
        session['quiz_errors'] = 3  # reset errors
        top_scores_quiz = get_high_scores_quiz()
        return render_template('quiz_gameover.html',
                               points=final_points,
                               top_scores=top_scores_quiz,
                               )
    id = randint(1,10)
    if id in id_list:
        id = randint(1,10)
        while id in id_list:
            id = randint(1,10)
        id_list.append(id)
    else:
        id_list.append(id)
    questions = quiz.execute('SELECT * FROM quiz WHERE id = ? ORDER BY id', [id]).fetchall()
    quiz_question = questions[0][1]
    quiz.close()
    if len(id_list) <= 10:
        return render_template('quiz.html', id=id, errors = errors, points=points,quiz_question = quiz_question, top_score=top_score)

def add_quiz_questions():
    quiz = get_db_connection()[1]
    quiz.execute('DELETE FROM quiz')
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)',
                 ["How many times more likely are giraffes to get hit by lightning than people?", "30"])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['Do identical twins have the same fingerprints?', 'no'])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['What is the tallest mountain on Earth?', 'mount everest'])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['Do Ants have lungs?', 'No'])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['Which type of commonly eaten fruit is radioactive?', 'bananas'])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['According to the World Happiness Report, what country is the happiest?', 'finland'])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['Can hippos swim?', 'no'])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['Can you yo-yo in space?', 'yes'])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['The biggest butterfly in the world has a wingspan of how many cm?', '31cm'])
    quiz.execute('INSERT INTO quiz (question, answer) VALUES (?, ?)', ['What color are Falmingoes born? (Hint: not pink!)', 'white'])
    quiz.commit()
    quiz.close()



@app.route('/quiz_guess', methods=['POST'])
def quiz_guess():
    quiz = get_db_connection()[1]
    answer = str(request.form.get('answer'))
    id = request.form.get('id')
    points = int(request.form.get('points'))
    questions = quiz.execute('SELECT * FROM quiz WHERE id = ? ORDER BY id', [id]).fetchall()
    quiz_question = questions[0][1]
    quiz_answer = questions[0][2]


    if answer.lower() == str(quiz_answer).lower():
        result = 'correct'
        session['quiz_points'] += 50
    else:
        result = 'incorrect'
        session['quiz_points'] -= 50
        session['quiz_errors'] -= 1
    quiz.close()

    return render_template('quiz_resutl.html',
                           result=result, quiz_answer=quiz_answer, points=points, quiz_question=quiz_question)

def add_score_quiz(name, score):
    quiz_score = get_db_connection()[2]
    quiz_score.execute('INSERT INTO quiz_scores (name, score) VALUES (?, ?)', (name, score))
    quiz_score.commit()
    quiz_score.close()

def get_high_scores_quiz(limit=10):
    quiz_score = get_db_connection()[2]
    q_scores = quiz_score.execute('SELECT name, score FROM quiz_scores ORDER BY score DESC LIMIT ?', (limit,)).fetchall()
    quiz_score.close()
    return q_scores

@app.route('/add_score_quiz', methods=['POST'])
def add_score_quiz_route():
    score_data = request.json
    add_score_quiz(score_data['name'], score_data['score'])
    return jsonify({'message': 'Score added successfully!'}), 201

@app.route('/high_scores_quiz', methods=['GET'])
def get_high_scores_quiz_route():
    scores = get_high_scores_quiz()
    return jsonify([{'name': row['name'], 'score': row['score']} for row in scores])



if __name__ == '__main__':
    app.run(debug=True)
