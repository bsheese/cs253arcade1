-- Schema for High Scores Table
CREATE TABLE IF NOT EXISTS high_scores (
    id INTEGER PRIMARY KEY,
    name TEXT,
    game TEXT,
    score INTEGER
);
