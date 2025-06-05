from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 1800
db = SQLAlchemy(app)

HIGH_SCORES_FILE = 'data/high_scores.json'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    options = db.Column(db.String(500), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)

if not os.path.exists('data'):
    os.makedirs('data')
if not os.path.exists(HIGH_SCORES_FILE):
    with open(HIGH_SCORES_FILE, 'w') as f:
        json.dump({}, f)

def load_high_scores():
    try:
        with open(HIGH_SCORES_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {}

def save_high_scores(high_scores):
    with open(HIGH_SCORES_FILE, 'w') as f:
        json.dump(high_scores, f, indent=4)

def preload_quizzes():
    quizzes = [
        {
            "title": "Operating Systems",
            "time_limit": 300,
            "questions": [
                {"text": "What is the primary function of an operating system?", "options": "Manage hardware,Run applications,User interface,All of the above", "correct_option": 3},
                {"text": "Which scheduling algorithm is used in Round Robin?", "options": "FCFS,SJF,Priority,Time-sharing", "correct_option": 3},
                {"text": "What is a deadlock in OS?", "options": "Process termination,Resource contention,Memory leak,Thread failure", "correct_option": 1},
                {"text": "What does CPU scheduling aim to achieve?", "options": "Maximize CPU utilization,Minimize memory usage,Increase I/O operations,Reduce network latency", "correct_option": 0},
                {"text": "What is paging in OS?", "options": "Memory allocation,Process scheduling,Virtual memory management,File system organization", "correct_option": 2},
                {"text": "Which OS uses a microkernel architecture?", "options": "Windows,Linux,macOS,Minix", "correct_option": 3},
                {"text": "What is the purpose of a semaphore?", "options": "Memory allocation,Process synchronization,File handling,Interrupt handling", "correct_option": 1},
                {"text": "What is thrashing in OS?", "options": "High CPU usage,Excessive paging,Low memory usage,Network congestion", "correct_option": 1},
                {"text": "Which file system is used by Windows?", "options": "ext4,NTFS,FAT32,Both NTFS and FAT32", "correct_option": 3},
                {"text": "What is a thread in OS?", "options": "A process,A lightweight process,A memory block,A file", "correct_option": 1},
            ]
        },
        {
            "title": "Java Programming",
            "time_limit": 300,
            "questions": [
                {"text": "What is the default value of an int in Java?", "options": "0,1,null,undefined", "correct_option": 0},
                {"text": "Which keyword is used to inherit a class in Java?", "options": "extends,implements,super,this", "correct_option": 0},
                {"text": "What is the purpose of the 'final' keyword?", "options": "To make a variable constant,To create a loop,To define a method,To initialize a class", "correct_option": 0},
                {"text": "Which of these is a Java access modifier?", "options": "public,static,final,abstract", "correct_option": 0},
                {"text": "What is the output of System.out.println(5 + 3 + \"Java\")?", "options": "8Java,53Java,Java8,Java53", "correct_option": 0},
                {"text": "Which collection class is synchronized?", "options": "ArrayList,HashMap,Vector,LinkedList", "correct_option": 2},
                {"text": "What does JVM stand for?", "options": "Java Virtual Machine,Java Variable Manager,Java Version Manager,Java Visual Machine", "correct_option": 0},
                {"text": "Which exception is thrown by parseInt()?", "options": "IOException,NumberFormatException,ClassNotFoundException,SQLException", "correct_option": 1},
                {"text": "What is the purpose of the 'super' keyword?", "options": "To call the parent class constructor,To create an object,To define a static method,To handle exceptions", "correct_option": 0},
                {"text": "Which loop is guaranteed to execute at least once?", "options": "for,while,do-while,foreach", "correct_option": 2},
            ]
        },
        {
            "title": "C++ Programming",
            "time_limit": 300,
            "questions": [
                {"text": "What is the size of an int in C++ (typically)?", "options": "2 bytes,4 bytes,8 bytes,16 bytes", "correct_option": 1},
                {"text": "Which operator is used for dynamic memory allocation in C++?", "options": "malloc,new,alloc,calloc", "correct_option": 1},
                {"text": "What is the purpose of a virtual function?", "options": "To enable polymorphism,To reduce memory usage,To increase speed,To handle errors", "correct_option": 0},
                {"text": "Which of these is a C++ standard library container?", "options": "ArrayList,Vector,HashMap,TreeSet", "correct_option": 1},
                {"text": "What is the output of cout << (5 > 3 ? 1 : 0);?", "options": "0,1,5,3", "correct_option": 1},
                {"text": "What does the 'const' keyword do in C++?", "options": "Makes a variable immutable,Defines a loop,Declares a class,Handles exceptions", "correct_option": 0},
                {"text": "Which of these is a C++ access specifier?", "options": "public,static,final,abstract", "correct_option": 0},
                {"text": "What is the purpose of a destructor in C++?", "options": "To allocate memory,To initialize objects,To free resources,To define a method", "correct_option": 2},
                {"text": "Which header file is required for file handling in C++?", "options": "iostream,fstream,string,vector", "correct_option": 1},
                {"text": "What is the output of int x = 5; cout << x++;?", "options": "5,6,4,7", "correct_option": 0},
            ]
        },
        {
            "title": "Database Management Systems (DBMS)",
            "time_limit": 300,
            "questions": [
                {"text": "What does SQL stand for?", "options": "Structured Query Language,Simple Query Language,Standard Query Language,Sequential Query Language", "correct_option": 0},
                {"text": "Which of these is a type of database key?", "options": "Primary key,Foreign key,Candidate key,All of the above", "correct_option": 3},
                {"text": "What is the purpose of a JOIN in SQL?", "options": "To combine rows from two tables,To delete records,To update records,To create a table", "correct_option": 0},
                {"text": "What does ACID stand for in DBMS?", "options": "Atomicity Consistency Isolation Durability,Accuracy Completeness Integrity Dependability,Availability Consistency Integrity Durability,Atomicity Completeness Isolation Dependability", "correct_option": 0},
                {"text": "Which SQL command is used to retrieve data?", "options": "INSERT,UPDATE,SELECT,DELETE", "correct_option": 2},
                {"text": "What is normalization in DBMS?", "options": "Reducing redundancy,Increasing redundancy,Encrypting data,Backing up data", "correct_option": 0},
                {"text": "Which of these is a type of database model?", "options": "Relational,Hierarchical,Network,All of the above", "correct_option": 3},
                {"text": "What is a transaction in DBMS?", "options": "A single query,A sequence of operations, A table, A database", "correct_option": 1},
                {"text": "Which SQL clause is used to filter records?", "options": "WHERE,FROM,SELECT,ORDER BY", "correct_option": 0},
                {"text": "What is the purpose of an index in DBMS?", "options": "To speed up queries,To store data,To define relationships,To encrypt data", "correct_option": 0},
            ]
        }
    ]
    
    with app.app_context():
        db.create_all()
        if not Quiz.query.first():
            for quiz_data in quizzes:
                quiz = Quiz(title=quiz_data['title'], time_limit=quiz_data['time_limit'])
                db.session.add(quiz)
                db.session.flush()
                for q in quiz_data['questions']:
                    question = Question(quiz_id=quiz.id, text=q['text'], options=q['options'], correct_option=q['correct_option'])
                    db.session.add(question)
            db.session.commit()

@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return datetime.fromtimestamp(timestamp, tz=ist_tz).strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def home():
    session.permanent = False
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        session.clear()
        flash('Session expired or invalid. Please log in again.', 'danger')
        return redirect(url_for('login'))
    quizzes = Quiz.query.all()
    high_scores = load_high_scores()
    user_high_scores = high_scores.get(str(user_id), {}) if user_id is not None else {}
    return render_template('quiz_list.html', quizzes=quizzes, user_high_scores=user_high_scores)

@app.route('/register', methods=['GET', 'POST'])
def register():
    session.permanent = False
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, is_admin=(username == 'admin'))
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Username already exists.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.permanent = False
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    session.permanent = False
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required.', 'danger')
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        time_limit = int(request.form['time_limit'])
        questions = []
        for i in range(1, int(request.form['question_count']) + 1):
            text = request.form[f'question_{i}']
            options = ','.join([
                request.form[f'option_{i}_1'],
                request.form[f'option_{i}_2'],
                request.form[f'option_{i}_3'],
                request.form[f'option_{i}_4']
            ])
            correct_option = int(request.form[f'correct_option_{i}']) - 1
            questions.append((text, options, correct_option))
        quiz = Quiz(title=title, time_limit=time_limit)
        db.session.add(quiz)
        db.session.commit()
        for text, options, correct_option in questions:
            question = Question(quiz_id=quiz.id, text=text, options=options, correct_option=correct_option)
            db.session.add(question)
        db.session.commit()
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('admin_create_quiz.html')

@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    session.permanent = False
    if 'user_id' not in session:
        flash('Please log in to take the quiz.', 'danger')
        return redirect(url_for('login'))
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    if request.method == 'POST':
        try:
            score = 0
            user_answers = []
            for question in questions:
                user_answer = int(request.form.get(f'question_{question.id}', -1))
                user_answers.append(user_answer)
                if user_answer == question.correct_option:
                    score += 1
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            score_entry = Score(user_id=session['user_id'], quiz_id=quiz_id, score=score, timestamp=int(datetime.now(ist_tz).timestamp()))
            db.session.add(score_entry)
            db.session.commit()
            high_scores = load_high_scores()
            user_id_str = str(session['user_id'])
            if user_id_str not in high_scores:
                high_scores[user_id_str] = {}
            quiz_id_str = str(quiz_id)
            current_high = high_scores[user_id_str].get(quiz_id_str, 0)
            if score > current_high:
                high_scores[user_id_str][quiz_id_str] = score
                save_high_scores(high_scores)
            question_answer_pairs = list(zip(questions, user_answers))
            return render_template('results.html', quiz=quiz, question_answer_pairs=question_answer_pairs, score=score, total_questions=len(questions))
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting quiz: {str(e)}", 'danger')
            return redirect(url_for('home'))
    return render_template('quiz_take.html', quiz=quiz, questions=questions)

@app.route('/admin_analytics')
def admin_analytics():
    session.permanent = False
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required.', 'danger')
        return redirect(url_for('home'))
    try:
        total_users = User.query.count()
        total_quizzes_taken = Score.query.count()
        quizzes = Quiz.query.all()
        quiz_stats = []
        for quiz in quizzes:
            scores = Score.query.filter_by(quiz_id=quiz.id).all()
            if scores:
                avg_score = sum(score.score for score in scores) / len(scores)
                total_questions = Question.query.filter_by(quiz_id=quiz.id).count()
                avg_percentage = (avg_score / total_questions) * 100 if total_questions else 0
                quiz_stats.append({
                    'title': quiz.title,
                    'avg_score': round(avg_score, 2),
                    'avg_percentage': round(avg_percentage, 2),
                    'total_attempts': len(scores)
                })
        top_users = []
        users = User.query.all()
        for user in users:
            scores = Score.query.filter_by(user_id=user.id).all()
            if scores:
                total_attempts = len(scores)
                avg_score = sum(score.score for score in scores) / total_attempts
                total_percentages = 0
                for score in scores:
                    total_questions = Question.query.filter_by(quiz_id=score.quiz_id).count()
                    percentage = (score.score / total_questions * 100) if total_questions else 0
                    total_percentages += percentage
                avg_percentage = total_percentages / total_attempts if total_attempts else 0
                top_users.append({
                    'username': user.username,
                    'total_attempts': total_attempts,
                    'avg_score': round(avg_score, 2),
                    'avg_percentage': round(avg_percentage, 2)
                })
        top_users = sorted(top_users, key=lambda x: x['avg_percentage'], reverse=True)[:5]
        return render_template('admin_analytics.html',
                              total_users=total_users,
                              total_quizzes_taken=total_quizzes_taken,
                              quiz_stats=quiz_stats,
                              top_users=top_users)
    except Exception as e:
        flash(f"Error loading analytics: {str(e)}", 'danger')
        return redirect(url_for('home'))

if __name__ == '__main__':
    preload_quizzes()
    app.run(debug=True)