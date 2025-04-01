from flask import Flask, request, render_template, redirect, url_for, session
import hashlib
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')  # Use Railway env var

DB_FILE = 'data.db'
ARCHIVE_DIR = 'archives/'

# Ensure archive directory exists
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        is_admin INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS player_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        rank TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return "Login failed!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/archive')
def archive():
    if 'user' not in session:
        return redirect(url_for('login'))

    files = os.listdir(ARCHIVE_DIR)
    return render_template('archive.html', files=files)

@app.route('/view_players')
def view_players():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, rank FROM player_data")
    players = cursor.fetchall()
    conn.close()

    return render_template('view_players.html', players=players)

@app.route('/edit_file/<filename>', methods=['GET', 'POST'])
def edit_file(filename):
    file_path = os.path.join(ARCHIVE_DIR, filename)
    if not os.path.exists(file_path):
        return "File not found", 404

    if request.method == 'POST':
        content = request.form['content']
        with open(file_path, 'w') as f:
            f.write(content)
        return redirect(url_for('archive'))

    with open(file_path, 'r') as f:
        content = f.read()

    return render_template('edit_file.html', filename=filename, content=content)

@app.route('/download_file/<filename>')
def download_file(filename):
    file_path = os.path.join(ARCHIVE_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
