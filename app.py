from flask import Flask, request, jsonify, render_template, session, g
import sqlite3
import os
from random import randint

# Create an instance of the Flask class
app = Flask(__name__)

# Load default configuration settings and override them with values from an environment variable, if it exists
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'scores.db'),  # Path to the SQLite database file
    DEBUG=True,  # Enable debug mode for detailed error messages and auto-reloading
    SECRET_KEY='development key',  # Secret key for session management and other security-related needs
))
app.config.from_envvar('FLASKR_SETTINGS',
                       silent=True)  # Load additional configuration from a specified environment variable, if set


# Function to connect to the database
def connect_db():
    """Connects to the specific database.

    This function creates a connection to the SQLite database specified in the app configuration.
    It sets the row factory to sqlite3.Row to access columns by name.

    Returns:
        sqlite3.Connection: A connection object to interact with the database.
    """
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row  # Allows accessing columns by name
    return rv


# Function to initialize the database
def init_db():
    """Initializes the database.

    This function initializes the database by executing the schema script located in 'schema.sql'.
    It sets up the necessary tables and their structure in the database.
    """
    db = get_db()  # Get a database connection
    with app.open_resource('schema.sql', mode='r') as f:  # Open the schema script
        db.cursor().executescript(f.read())  # Execute the script to create tables
    db.commit()  # Commit the changes


# Command to initialize the database from the command line
@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables.

    This command-line command initializes the database by calling the init_db function.
    It prints a confirmation message once the initialization is complete.
    """
    init_db()  # Initialize the database
    print('Initialized the database.')  # Print confirmation message


# Function to get a database connection
def get_db():
    """Opens a new database connection if there is none yet for the current application context.

    This function checks if a database connection already exists for the current application context.
    If not, it establishes a new connection and stores it in the application context.

    Returns:
        sqlite3.Connection: A connection object to interact with the database.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()  # Establish a new database connection
    return g.sqlite_db  # Return the connection


# Function to close the database connection
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request.

    This function closes the database connection at the end of the request.
    It ensures that the connection is properly closed to avoid resource leaks.

    Args:
        error (Optional[Exception]): An optional error that may have occurred during the request.
    """
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()  # Close the database connection if it exists


# Function to add a score to the database
def add_score(name, score):
    """Inserts a new score into the database.

    Args:
        name (str): The name of the player.
        score (int): The score of the player.
    """
    conn = get_db()  # Get a database connection
    conn.execute('INSERT INTO scores (name, score) VALUES (?, ?)', (name, score))  # Insert the score into the database
    conn.commit()  # Commit the transaction
    conn.close()  # Close the connection


# Function to retrieve high scores from the database
def get_high_scores(limit=10):
    """Retrieves high scores from the database.

    Args:
        limit (int, optional): The number of top scores to retrieve. Defaults to 10.

    Returns:
        list: A list of tuples containing the name and score of the top players.
    """
    conn = get_db()  # Get a database connection
    scores = conn.execute('SELECT name, score FROM scores ORDER BY score DESC LIMIT ?',
                          (limit,)).fetchall()  # Retrieve the top scores
    conn.close()  # Close the connection
    return scores  # Return the scores


# Manually push the application context to initialize the database
with app.app_context():
    init_db()


# Route to add a score
@app.route('/add_score', methods=['POST'])
def add_score_route():
    """Handles the POST request to add a score.

    This route receives JSON data containing the name and score of a player,
    adds the score to the database, and returns a success message.

    Returns:
        Response: A JSON response indicating success.
    """
    score_data = request.json  # Get the JSON data from the request
    add_score(score_data['name'], score_data['score'])  # Add the score to the database
    return jsonify({'message': 'Score added successfully!'}), 201  # Return a success message


# Route to get high scores
@app.route('/high_scores', methods=['GET'])
def get_high_scores_route():
    """Handles the GET request to retrieve high scores.

    This route retrieves the top scores from the database and returns them as JSON data.

    Returns:
        Response: A JSON response containing the top scores.
    """
    scores = get_high_scores()  # Retrieve the top scores from the database
    return jsonify([{'name': row['name'], 'score': row['score']} for row in scores])  # Return the scores as JSON


# Route for the home page
@app.route('/')
def index():
    """Renders the home page.

    This route renders the 'index.html' template.

    Returns:
        Response: The rendered HTML of the home page.
    """
    return render_template('index.html')


# Route for the snake game page
@app.route('/snake')
def snake():
    """Renders the snake game page.

    This route renders the 'snake.html' template.

    Returns:
        Response: The rendered HTML of the snake game page.
    """
    return render_template('snake.html')


# Route for the Hi-Lo game page
@app.route('/hilo')
def hilo():
    """Renders the Hi-Lo game page and initializes game settings.

    This route initializes the game points and errors in the session if not already set.
    It generates two random numbers and renders the 'hilo.html' template with game data.

    Returns:
        Response: The rendered HTML of the Hi-Lo game page.
    """
    if 'hilo_points' not in session:
        session['hilo_points'] = 100  # Initialize points to 100 if not set

    points = session['hilo_points']  # Retrieve points from session

    if 'hilo_errors' not in session:
        session['hilo_errors'] = 3  # Initialize errors to 3 if not set

    errors = session['hilo_errors']
    if errors == 0:
        final_points = session['hilo_points']
        session['hilo_points'] = 100  # Reset game points
        session['hilo_errors'] = 3  # Reset errors
        top_scores = get_high_scores()  # Get high scores
        return render_template('hilo_gameover.html',
                               points=final_points,
                               top_scores=top_scores)  # Render game over template

    while True:
        number_first = randint(1, 10)  # Generate the first random number
        number_second = randint(1, 10)  # Generate the second random number
        if number_first != number_second:
            break

    return render_template('hilo.html',
                           points=points,
                           errors=errors,
                           number_first=number_first,
                           number_second=number_second)  # Render the game page with data


# Route to handle Hi-Lo game guesses
@app.route('/hilo_guess', methods=['POST'])
def hilo_guess():
    """Handles the POST request for Hi-Lo game guesses.

    This route processes the player's guess, updates the points and errors in the session,
    and renders the result template with the game data.

    Returns:
        Response: The rendered HTML of the result page.
    """
    number_first = int(request.form.get('number_first'))  # Get the first number from the form
    number_second = int(request.form.get('number_second'))  # Get the second number from the form
    guess = request.form.get('guess')  # Get the player's guess from the form
    points = int(request.form.get('points'))  # Get the points from the form

    if guess == 'Higher' and number_second > number_first:
        result = 'correct'
        session['hilo_points'] += 50  # Increase points if guess is correct
    elif guess == 'Lower' and number_second < number_first:
        result = 'correct'
        session['hilo_points'] += 50  # Increase points if guess is correct
    else:
        result = 'incorrect'
        session['hilo_points'] -= 50  # Decrease points if guess is incorrect
        session['hilo_errors'] -= 1  # Decrease errors if guess is incorrect

    return render_template('hilo_result.html',
                           number_first=number_first,
                           number_second=number_second,
                           result=result)  # Render the result page with data


# Run the application
if __name__ == '__main__':
    app.run(debug=True)  # Run the app in debug mode
