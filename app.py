from flask import Flask, session, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
import json
import uuid
from datetime import datetime
from scraper import fetch_questions_from_web
import re

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-echoquest-2024'
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please login to access this page!"

DATABASE = 'db.sqlite3'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, score, quizzes_taken):
        self.id = id
        self.username = username
        self.email = email
        self.score = score
        self.quizzes_taken = quizzes_taken

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[5], user[6])
    return None

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table (enhanced)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_score INTEGER DEFAULT 0,
            quizzes_taken INTEGER DEFAULT 0,
            avatar TEXT DEFAULT '🐱',
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0
        )
    ''')
    
    # Topics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT UNIQUE,
            search_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Quiz sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT UNIQUE,
            topic TEXT,
            score INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 20,
            completed BOOLEAN DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            topic TEXT,
            question_text TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_answer TEXT,
            explanation TEXT,
            difficulty TEXT,
            question_number INTEGER
        )
    ''')
    
    # User responses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT,
            question_id INTEGER,
            user_answer TEXT,
            is_correct BOOLEAN,
            time_taken INTEGER,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Leaderboard
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            topic TEXT,
            score INTEGER,
            total_questions INTEGER,
            percentage REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Username can only contain letters, numbers, and underscore")
        if not email or '@' not in email:
            errors.append("Valid email is required")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters")
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if errors:
            return render_template('register.html', errors=errors)
        
        # Check if user exists
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return render_template('register.html', error="Username or email already exists!")
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (username, email, hashed_password))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['email'], user['total_score'], user['quizzes_taken'])
            login_user(user_obj)
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password!")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user stats
    cursor.execute('''
        SELECT COUNT(*) as total_quizzes, SUM(score) as total_score 
        FROM quiz_sessions 
        WHERE user_id = ? AND completed = 1
    ''', (current_user.id,))
    stats = cursor.fetchone()
    
    # Get recent quizzes
    cursor.execute('''
        SELECT topic, score, total_questions, completed_at 
        FROM quiz_sessions 
        WHERE user_id = ? AND completed = 1 
        ORDER BY completed_at DESC LIMIT 5
    ''', (current_user.id,))
    recent_quizzes = cursor.fetchall()
    
    # Get achievements
    cursor.execute('''
        SELECT topic, COUNT(*) as times_played, AVG(percentage) as avg_score
        FROM leaderboard 
        WHERE user_id = ? 
        GROUP BY topic 
        ORDER BY times_played DESC LIMIT 5
    ''', (current_user.id,))
    favorite_topics = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_quizzes=recent_quizzes,
                         favorite_topics=favorite_topics)

@app.route('/search_topic', methods=['GET', 'POST'])
@login_required
def search_topic():
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        
        if not topic:
            flash('Please enter a topic!', 'error')
            return redirect(url_for('search_topic'))
        
        # Store in session
        session['current_topic'] = topic
        session['score'] = 0
        session['current_q_num'] = 1
        session['questions'] = []
        
        # Update topic count
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO topics (topic_name) VALUES (?)', (topic,))
        cursor.execute('UPDATE topics SET search_count = search_count + 1 WHERE topic_name = ?', (topic,))
        conn.commit()
        
        # Fetch questions
        questions = fetch_questions_from_web(topic)
        
        if not questions:
            questions = generate_fallback_questions(topic)
        
        # Create quiz session
        session_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO quiz_sessions (user_id, session_id, topic, total_questions)
            VALUES (?, ?, ?, ?)
        ''', (current_user.id, session_id, topic, len(questions[:20])))
        session['quiz_session_id'] = session_id
        
        # Store questions
        for i, q in enumerate(questions[:20]):
            cursor.execute('''
                INSERT INTO quiz_questions (session_id, topic, question_text, option_a, option_b, 
                                           option_c, option_d, correct_answer, explanation, difficulty, question_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, topic, q['text'], q['options'][0], q['options'][1], 
                  q['options'][2], q['options'][3], q['correct'], q.get('explanation', ''), 
                  q.get('difficulty', 'medium'), i+1))
            
            session['questions'].append({
                'id': cursor.lastrowid,
                'text': q['text'],
                'options': q['options'],
                'correct': q['correct'],
                'explanation': q.get('explanation', ''),
                'difficulty': q.get('difficulty', 'medium')
            })
        
        conn.commit()
        conn.close()
        
        session['total_questions'] = len(questions[:20])
        
        return redirect(url_for('quiz'))
    
    # GET request - show search page
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT topic_name, search_count FROM topics ORDER BY search_count DESC LIMIT 10')
    popular_topics = cursor.fetchall()
    conn.close()
    
    return render_template('search.html', popular_topics=popular_topics)

@app.route('/quiz')
@login_required
def quiz():
    if 'current_topic' not in session:
        flash('Please search for a topic first!', 'warning')
        return redirect(url_for('search_topic'))
    
    return render_template('quiz.html', 
                         topic=session['current_topic'],
                         username=current_user.username,
                         total_questions=session.get('total_questions', 20))

@app.route('/get_current_question')
@login_required
def get_current_question():
    q_num = session.get('current_q_num', 1)
    questions = session.get('questions', [])
    
    if q_num <= len(questions):
        question = questions[q_num - 1]
        return jsonify({
            'id': question['id'],
            'question_number': q_num,
            'total': len(questions),
            'text': question['text'],
            'options': question['options'],
            'difficulty': question['difficulty']
        })
    else:
        return jsonify({'quiz_ended': True})

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    data = request.json
    q_num = session.get('current_q_num', 1)
    user_answer = data.get('answer', '')
    time_taken = data.get('time_taken', 0)
    
    questions = session.get('questions', [])
    
    if q_num <= len(questions):
        question = questions[q_num - 1]
        is_correct = (user_answer == question['correct'])
        
        points = 10 if is_correct else 0
        if is_correct and time_taken < 5:
            points += 5
        elif is_correct and time_taken < 10:
            points += 2
        
        if is_correct:
            session['score'] = session.get('score', 0) + points
        
        # Store response
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_responses (user_id, session_id, question_id, user_answer, is_correct, time_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_user.id, session['quiz_session_id'], question['id'], user_answer, is_correct, time_taken))
        conn.commit()
        conn.close()
        
        session['current_q_num'] = q_num + 1
        quiz_ended = session['current_q_num'] > len(questions)
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': question['correct'],
            'explanation': question['explanation'],
            'points_earned': points if is_correct else 0,
            'score': session['score'],
            'quiz_ended': quiz_ended,
            'next_q_num': session['current_q_num']
        })
    else:
        return jsonify({'quiz_ended': True})

@app.route('/end_quiz', methods=['POST'])
@login_required
def end_quiz():
    score = session.get('score', 0)
    total = session.get('total_questions', 20)
    percentage = (score / (total * 10)) * 100
    
    # Update quiz session
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE quiz_sessions 
        SET score = ?, completed = 1, completed_at = CURRENT_TIMESTAMP
        WHERE session_id = ?
    ''', (score, session['quiz_session_id']))
    
    # Update user stats
    cursor.execute('''
        UPDATE users 
        SET total_score = total_score + ?, quizzes_taken = quizzes_taken + 1
        WHERE id = ?
    ''', (score, current_user.id))
    
    # Update XP and level
    cursor.execute('SELECT xp, level FROM users WHERE id = ?', (current_user.id,))
    user_data = cursor.fetchone()
    new_xp = user_data['xp'] + score
    new_level = user_data['level']
    if new_xp >= new_level * 100:
        new_level += 1
        new_xp = 0
    
    cursor.execute('UPDATE users SET xp = ?, level = ? WHERE id = ?', (new_xp, new_level, current_user.id))
    
    # Add to leaderboard
    cursor.execute('''
        INSERT INTO leaderboard (user_id, user_name, topic, score, total_questions, percentage)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, current_user.username, session['current_topic'], score, total, percentage))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/result')
@login_required
def result():
    return render_template('result.html', 
                         score=session.get('score', 0),
                         total=session.get('total_questions', 20),
                         topic=session.get('current_topic', ''),
                         username=current_user.username)

@app.route('/leaderboard')
def leaderboard():
    topic = request.args.get('topic', '')
    conn = get_db()
    cursor = conn.cursor()
    
    if topic:
        cursor.execute('''
            SELECT user_name, score, total_questions, percentage, created_at
            FROM leaderboard
            WHERE topic = ?
            ORDER BY percentage DESC
            LIMIT 50
        ''', (topic,))
    else:
        cursor.execute('''
            SELECT user_name, topic, score, total_questions, percentage, created_at
            FROM leaderboard
            ORDER BY percentage DESC
            LIMIT 50
        ''')
    
    leaders = cursor.fetchall()
    conn.close()
    
    return render_template('leaderboard.html', leaders=leaders, selected_topic=topic)

def generate_fallback_questions(topic):
    questions = []
    for i in range(20):
        questions.append({
            'text': f'Question {i+1}: What is an important concept in {topic}?',
            'options': [f'Key aspect of {topic}', f'Related concept', f'Advanced topic', f'Basic principle'],
            'correct': 'A',
            'explanation': f'This is fundamental to understanding {topic}.',
            'difficulty': 'medium'
        })
    return questions

if __name__ == '__main__':
    app.run(debug=True, port=5000)