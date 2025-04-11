import os
import random
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
app.config['DATABASE'] = os.path.join(app.instance_path, 'chatbot.sqlite')
app.config['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', '')

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Configure Gemini API
genai.configure(api_key=app.config['GEMINI_API_KEY'])

# Database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Initialize the database
def init_db():
    db = get_db()
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

# Add this function after init_db() function
def create_admin_user():
    """Create admin user if it doesn't exist."""
    db = get_db()
    admin = db.execute('SELECT * FROM users WHERE email = ?', ('admin@example.com',)).fetchone()
    if admin is None:
        db.execute(
            'INSERT INTO users (email, password_hash, role, is_active, daily_limit) VALUES (?, ?, ?, ?, ?)',
            ('admin@example.com', generate_password_hash('admin'), 'admin', 1, 999)
        )
        db.commit()
        print('Admin user created.')

# Modify the init_db_command function to call create_admin_user
@app.cli.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    create_admin_user()
    print('Initialized the database.')

# Add a new command to create admin user without reinitializing the database
@app.cli.command('create-admin')
def create_admin_command():
    """Create admin user if it doesn't exist."""
    create_admin_user()

# Register database functions with the Flask app
app.teardown_appcontext(close_db)

# Decorators for authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE id = ?', (session['user_id'],)
        ).fetchone()
        
        if user['role'] != 'admin':
            flash('You do not have permission to access this page.')
            return redirect(url_for('chat'))
        
        return f(*args, **kwargs)
    return decorated_function

# Authentication routes
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone() is not None:
            error = f'User with email {email} is already registered.'

        if error is None:
            db.execute(
                'INSERT INTO users (email, password_hash, role, is_active, daily_limit) VALUES (?, ?, ?, ?, ?)',
                (email, generate_password_hash(password), 'user', 1, 10)
            )
            db.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))

        flash(error)

    return render_template('auth/register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()

        if user is None:
            error = 'Incorrect email.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'
        elif user['is_active'] == 0:
            error = 'This account has been deactivated.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('chat'))

        flash(error)

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# User routes
@app.route('/profile', methods=('GET', 'POST'))
@login_required
def profile():
    db = get_db()
    user = db.execute(
        'SELECT * FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        error = None

        if not check_password_hash(user['password_hash'], current_password):
            error = 'Current password is incorrect.'
        
        if error is None:
            db.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (generate_password_hash(new_password), session['user_id'])
            )
            db.commit()
            flash('Password updated successfully.')
            return redirect(url_for('profile'))
        
        flash(error)
    
    return render_template('profile.html', user=user)

# Chat routes
@app.route('/')
@app.route('/chat')
@login_required
def chat():
    # Get random mind logo
    mind_logos = ['mind1.svg', 'mind2.svg', 'mind3.svg']
    random_logo = random.choice(mind_logos)
    
    # Get chat history - Changed to ASC order to show oldest messages first
    db = get_db()
    chat_history = db.execute(
        'SELECT * FROM messages WHERE user_id = ? ORDER BY timestamp ASC',
        (session['user_id'],)
    ).fetchall()
    
    return render_template('chat.html', chat_history=chat_history, logo=random_logo)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message = request.form['message']
    db = get_db()
    
    # Check daily message limit
    today = datetime.now().strftime('%Y-%m-%d')
    message_count = db.execute(
        'SELECT COUNT(*) FROM messages WHERE user_id = ? AND DATE(timestamp) = ?',
        (session['user_id'], today)
    ).fetchone()[0]
    
    user = db.execute(
        'SELECT daily_limit FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    if message_count >= user['daily_limit']:
        flash('You have reached your daily message limit.')
        return redirect(url_for('chat'))
    
    # Generate response using Gemini API
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(message)
        response_text = response.text
    except Exception as e:
        response_text = f"Error generating response: {str(e)}"
    
    # Save message and response to database
    db.execute(
        'INSERT INTO messages (user_id, message, response, timestamp) VALUES (?, ?, ?, ?)',
        (session['user_id'], message, response_text, datetime.now())
    )
    db.commit()
    
    return redirect(url_for('chat'))

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    user_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    message_count = db.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
    
    return render_template('admin/dashboard.html', user_count=user_count, message_count=message_count)

@app.route('/admin/users')
@admin_required
def admin_users():
    db = get_db()
    users = db.execute('SELECT * FROM users').fetchall()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>/chats')
@admin_required
def admin_user_chats(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    chats = db.execute(
        'SELECT * FROM messages WHERE user_id = ? ORDER BY timestamp DESC',
        (user_id,)
    ).fetchall()
    
    return render_template('admin/user_chats.html', user=user, chats=chats)

@app.route('/admin/user/<int:user_id>/toggle_status')
@admin_required
def admin_toggle_user_status(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    new_status = 0 if user['is_active'] == 1 else 1
    db.execute(
        'UPDATE users SET is_active = ? WHERE id = ?',
        (new_status, user_id)
    )
    db.commit()
    
    status_text = 'activated' if new_status == 1 else 'deactivated'
    flash(f'User {user["email"]} has been {status_text}.')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/set_limit', methods=['POST'])
@admin_required
def admin_set_user_limit(user_id):
    new_limit = request.form['daily_limit']
    db = get_db()
    
    db.execute(
        'UPDATE users SET daily_limit = ? WHERE id = ?',
        (new_limit, user_id)
    )
    db.commit()
    
    flash(f'Daily message limit updated to {new_limit}.')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/delete')
@admin_required
def admin_delete_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    # Delete user's messages first (foreign key constraint)
    db.execute('DELETE FROM messages WHERE user_id = ?', (user_id,))
    # Then delete the user
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    
    flash(f'User {user["email"]} has been deleted.')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    app.run(debug=True)
