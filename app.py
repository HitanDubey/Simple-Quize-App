from flask import Flask, session, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
import json
import uuid
from datetime import datetime
from scraper import fetch_questions_from_web, generate_fallback_questions
import re
import os
import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-super-secret-key-echoquest-2024')
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please login to access this page!"

DATABASE = 'db.sqlite3'

# Updated User class with all properties
class User(UserMixin):
    def __init__(self, id, username, email, total_score, quizzes_taken, level=1, xp=0, avatar='🐱'):
        self.id = id
        self.username = username
        self.email = email
        self.total_score = total_score
        self.quizzes_taken = quizzes_taken
        self.level = level
        self.xp = xp
        self.avatar = avatar

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(
            id=user[0], 
            username=user[1], 
            email=user[2], 
            total_score=user[5] if len(user) > 5 else 0,
            quizzes_taken=user[6] if len(user) > 6 else 0,
            level=user[8] if len(user) > 8 else 1,
            xp=user[9] if len(user) > 9 else 0,
            avatar=user[7] if len(user) > 7 else '🐱'
        )
    return None

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
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
            difficulty TEXT DEFAULT 'mixed',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if difficulty column exists, add if not
    cursor.execute("PRAGMA table_info(quiz_sessions)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'difficulty' not in columns:
        try:
            cursor.execute("ALTER TABLE quiz_sessions ADD COLUMN difficulty TEXT DEFAULT 'mixed'")
            print("✅ Added difficulty column to quiz_sessions")
        except:
            pass
    
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
            marked_for_review BOOLEAN DEFAULT 0,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if marked_for_review column exists
    cursor.execute("PRAGMA table_info(user_responses)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'marked_for_review' not in columns:
        try:
            cursor.execute("ALTER TABLE user_responses ADD COLUMN marked_for_review BOOLEAN DEFAULT 0")
            print("✅ Added marked_for_review column to user_responses")
        except:
            pass
    
    # Leaderboard table
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

# Initialize database
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
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return render_template('register.html', error="Username or email already exists!")
        
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
            user_obj = User(
                user['id'], 
                user['username'], 
                user['email'], 
                user['total_score'], 
                user['quizzes_taken'],
                user['level'] if 'level' in user.keys() else 1,
                user['xp'] if 'xp' in user.keys() else 0
            )
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
    
    # Check if difficulty column exists
    cursor.execute("PRAGMA table_info(quiz_sessions)")
    columns = [col[1] for col in cursor.fetchall()]
    has_difficulty = 'difficulty' in columns
    
    # Get user stats
    cursor.execute('''
        SELECT COUNT(*) as total_quizzes, SUM(score) as total_score 
        FROM quiz_sessions 
        WHERE user_id = ? AND completed = 1
    ''', (current_user.id,))
    stats = cursor.fetchone()
    
    # Get recent quizzes
    if has_difficulty:
        cursor.execute('''
            SELECT topic, score, total_questions, completed_at, difficulty
            FROM quiz_sessions 
            WHERE user_id = ? AND completed = 1 
            ORDER BY completed_at DESC LIMIT 5
        ''', (current_user.id,))
    else:
        cursor.execute('''
            SELECT topic, score, total_questions, completed_at
            FROM quiz_sessions 
            WHERE user_id = ? AND completed = 1 
            ORDER BY completed_at DESC LIMIT 5
        ''', (current_user.id,))
    recent_quizzes = cursor.fetchall()
    
    # Get favorite topics
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
                         favorite_topics=favorite_topics,
                         has_difficulty=has_difficulty)

@app.route('/search_topic', methods=['GET', 'POST'])
@login_required
def search_topic():
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        num_questions = int(request.form.get('num_questions', 20))
        difficulty = request.form.get('difficulty', 'mixed')
        
        if not topic:
            flash('Please enter a topic!', 'error')
            return redirect(url_for('search_topic'))
        
        # Store in session
        session['current_topic'] = topic
        session['score'] = 0
        session['questions'] = []
        session['user_answers'] = {}
        session['marked_for_review'] = []
        session['difficulty'] = difficulty
        session['total_questions'] = num_questions
        
        # Update topic count
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO topics (topic_name) VALUES (?)', (topic,))
        cursor.execute('UPDATE topics SET search_count = search_count + 1 WHERE topic_name = ?', (topic,))
        conn.commit()
        
        # Fetch questions
        print(f"🔍 Fetching questions for topic: {topic}")
        questions = fetch_questions_from_web(topic, num_questions * 2)  # Fetch extra for filtering
        
        if not questions:
            questions = generate_fallback_questions(topic, num_questions)
        
        # Filter by difficulty if needed
        if difficulty != 'mixed':
            filtered = [q for q in questions if q.get('difficulty', 'medium') == difficulty]
            if len(filtered) >= num_questions:
                questions = filtered
            else:
                # Add fallback questions with correct difficulty
                while len(filtered) < num_questions:
                    fb = generate_fallback_questions(topic, 1)[0]
                    fb['difficulty'] = difficulty
                    filtered.append(fb)
                questions = filtered
        
        questions = questions[:num_questions]
        
        # Create quiz session
        session_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO quiz_sessions (user_id, session_id, topic, total_questions, difficulty)
            VALUES (?, ?, ?, ?, ?)
        ''', (current_user.id, session_id, topic, len(questions), difficulty))
        session['quiz_session_id'] = session_id
        
        # Store questions
        for i, q in enumerate(questions):
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
                'difficulty': q.get('difficulty', 'medium'),
                'question_number': i+1
            })
        
        conn.commit()
        conn.close()
        
        print(f"📚 Total questions prepared: {len(questions)}")
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
    
    questions = session.get('questions', [])
    total_questions = len(questions)
    
    return render_template('quiz.html', 
                         topic=session['current_topic'],
                         username=current_user.username,
                         total_questions=total_questions,
                         difficulty=session.get('difficulty', 'mixed'))

@app.route('/get_question/<int:q_num>')
@login_required
def get_question(q_num):
    """Get a specific question by number"""
    questions = session.get('questions', [])
    user_answers = session.get('user_answers', {})
    marked_for_review = session.get('marked_for_review', [])
    
    if q_num < 1 or q_num > len(questions):
        return jsonify({'error': 'Invalid question number'}), 404
    
    question = questions[q_num - 1]
    
    return jsonify({
        'id': question['id'],
        'question_number': q_num,
        'total': len(questions),
        'text': question['text'],
        'options': question['options'],
        'difficulty': question['difficulty'],
        'user_answer': user_answers.get(str(q_num), None),
        'marked_for_review': str(q_num) in marked_for_review,
        'correct_answer': question['correct'],
        'explanation': question['explanation']
    })

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    data = request.json
    q_num = data.get('question_number')
    user_answer = data.get('answer', '')
    time_taken = data.get('time_taken', 0)
    
    questions = session.get('questions', [])
    user_answers = session.get('user_answers', {})
    
    if q_num < 1 or q_num > len(questions):
        return jsonify({'error': 'Invalid question'}), 400
    
    question = questions[q_num - 1]
    is_correct = (user_answer == question['correct'])
    
    # Calculate points
    points = 10 if is_correct else 0
    if is_correct and time_taken < 5:
        points += 5
    elif is_correct and time_taken < 10:
        points += 2
    
    # Store answer
    user_answers[str(q_num)] = user_answer
    session['user_answers'] = user_answers
    
    # Calculate current score
    score = 0
    for q, ans in user_answers.items():
        q_idx = int(q) - 1
        if q_idx < len(questions):
            if ans == questions[q_idx]['correct']:
                score += 10
    
    session['score'] = score
    
    # Store in database
    conn = get_db()
    cursor = conn.cursor()
    
    marked = str(q_num) in session.get('marked_for_review', [])
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_responses 
        (user_id, session_id, question_id, user_answer, is_correct, time_taken, marked_for_review)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (current_user.id, session['quiz_session_id'], question['id'], user_answer, is_correct, time_taken, marked))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'correct': is_correct,
        'correct_answer': question['correct'],
        'explanation': question['explanation'],
        'points_earned': points if is_correct else 0,
        'current_score': score,
        'total_answered': len(user_answers)
    })

@app.route('/mark_for_review', methods=['POST'])
@login_required
def mark_for_review():
    """Mark/unmark a question for review"""
    data = request.json
    q_num = str(data.get('question_number'))
    marked = data.get('marked', True)
    
    marked_for_review = session.get('marked_for_review', [])
    
    if marked and q_num not in marked_for_review:
        marked_for_review.append(q_num)
    elif not marked and q_num in marked_for_review:
        marked_for_review.remove(q_num)
    
    session['marked_for_review'] = marked_for_review
    
    return jsonify({
        'success': True,
        'marked_for_review': marked_for_review
    })

@app.route('/get_quiz_status')
@login_required
def get_quiz_status():
    """Get current quiz status for palette"""
    questions = session.get('questions', [])
    user_answers = session.get('user_answers', {})
    marked_for_review = session.get('marked_for_review', [])
    
    status = []
    for i in range(1, len(questions) + 1):
        status.append({
            'question_number': i,
            'answered': str(i) in user_answers,
            'marked_for_review': str(i) in marked_for_review,
            'visited': True
        })
    
    return jsonify({
        'questions': status,
        'total': len(questions),
        'answered': len(user_answers),
        'marked': len(marked_for_review),
        'current_score': session.get('score', 0)
    })

@app.route('/end_quiz', methods=['POST'])
@login_required
def end_quiz():
    """End quiz and calculate final score"""
    questions = session.get('questions', [])
    user_answers = session.get('user_answers', {})
    
    # Calculate final score
    score = 0
    for q_num, answer in user_answers.items():
        q_idx = int(q_num) - 1
        if q_idx < len(questions):
            if answer == questions[q_idx]['correct']:
                score += 10
    
    total = len(questions)
    percentage = (score / (total * 10)) * 100 if total > 0 else 0
    
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
    if user_data:
        new_xp = (user_data['xp'] or 0) + score
        new_level = user_data['level'] or 1
        if new_xp >= new_level * 100:
            new_level += 1
            new_xp = new_xp - ((new_level - 1) * 100)
        
        cursor.execute('UPDATE users SET xp = ?, level = ? WHERE id = ?', (new_xp, new_level, current_user.id))
    
    # Add to leaderboard
    cursor.execute('''
        INSERT INTO leaderboard (user_id, user_name, topic, score, total_questions, percentage)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, current_user.username, session['current_topic'], score, total, percentage))
    
    conn.commit()
    conn.close()
    
    session['final_score'] = score
    session['final_percentage'] = percentage
    
    return jsonify({
        'success': True,
        'score': score,
        'total': total,
        'percentage': percentage
    })

@app.route('/result')
@login_required
def result():
    score = session.get('final_score', session.get('score', 0))
    total = session.get('total_questions', 20)
    
    return render_template('result.html', 
                         score=score,
                         total=total,
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
            ORDER BY percentage DESC, score DESC
            LIMIT 50
        ''', (topic,))
    else:
        cursor.execute('''
            SELECT user_name, topic, score, total_questions, percentage, created_at
            FROM leaderboard
            ORDER BY percentage DESC, score DESC
            LIMIT 50
        ''')
    
    leaders = cursor.fetchall()
    conn.close()
    
    return render_template('leaderboard.html', leaders=leaders, selected_topic=topic)

@app.route('/popular_topics')
def popular_topics():
    """Return popular topics as JSON"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT topic_name, search_count 
            FROM topics 
            WHERE search_count > 0 
            ORDER BY search_count DESC 
            LIMIT 10
        ''')
        topics = cursor.fetchall()
        conn.close()
        
        if not topics:
            default_topics = [
                {'topic_name': 'Python Programming', 'search_count': 150},
                {'topic_name': 'Machine Learning', 'search_count': 120},
                {'topic_name': 'Climate Change', 'search_count': 95},
                {'topic_name': 'World History', 'search_count': 80},
                {'topic_name': 'Space Exploration', 'search_count': 75},
                {'topic_name': 'Data Science', 'search_count': 70},
                {'topic_name': 'Artificial Intelligence', 'search_count': 65},
                {'topic_name': 'Cybersecurity', 'search_count': 60}
            ]
            return jsonify(default_topics)
        
        return jsonify([{'topic_name': t['topic_name'], 'search_count': t['search_count']} for t in topics])
    except Exception as e:
        print(f"Error in popular_topics: {e}")
        return jsonify([])

def generate_fallback_questions_local(topic, num_questions=20):
    """Generate fallback questions locally"""
    questions = []
    difficulties = ['easy', 'medium', 'hard']
    
    for i in range(num_questions):
        questions.append({
            'text': f'Question {i+1}: What is an important concept in {topic}?',
            'options': [
                f'Key aspect of {topic}',
                f'Related concept to {topic}',
                f'Advanced topic in {topic}',
                f'Basic principle of {topic}'
            ],
            'correct': 'A',
            'explanation': f'This is fundamental to understanding {topic}.',
            'difficulty': random.choice(difficulties)
        })
    return questions

# Import fallback from scraper
try:
    from scraper import generate_fallback_questions as scraper_fallback
except:
    scraper_fallback = generate_fallback_questions_local

def generate_fallback_questions(topic, num_questions=20):
    """Wrapper for fallback question generation"""
    return scraper_fallback(topic, num_questions)

if __name__ == '__main__':
    os.makedirs('question_cache', exist_ok=True)
    app.run(debug=True, port=5000)