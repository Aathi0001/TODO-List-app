from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import os
import sqlite3
import json

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key

# Database path
DATABASE = 'todo.db'

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Create the User and Task tables if they don't exist
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS User (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_time TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES User(id)
            )
        ''')
    print("Database initialized.")

# Initialize the database
init_db()

# Home route to display tasks
@app.route('/')
def index():
    if 'user_id' in session:
        with get_db_connection() as conn:
            tasks = conn.execute('SELECT * FROM Task WHERE user_id = ?', (session['user_id'],)).fetchall()
    else:
        tasks = []  # Empty list for unauthenticated users
    return render_template('index.html', tasks=tasks)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_db_connection() as conn:
            try:
                conn.execute('INSERT INTO User (username, password) VALUES (?, ?)', (username, password))
                flash('Registration successful. Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists. Please choose another one.', 'error')

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM User WHERE username = ? AND password = ?', (username, password)).fetchone()
            if user:
                session['user_id'] = user['id']
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Login failed. Check your credentials and try again.', 'error')

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# Add task route
@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form.get('description')
    due_time = request.form.get('due_time')

    if 'user_id' in session:
        user_id = session['user_id']
        with get_db_connection() as conn:
            conn.execute('INSERT INTO Task (title, description, due_time, user_id) VALUES (?, ?, ?, ?)',
                         (title, description, due_time, user_id))
    else:
        # Store the task in local storage format if the user is not logged in
        task_data = {
            "title": title,
            "description": description,
            "due_time": due_time
        }
        return json.dumps(task_data)  # Return task data as JSON for localStorage

    return redirect(url_for('index'))

# Delete task route
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM Task WHERE id = ?', (task_id,))
    return redirect(url_for('index'))

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
