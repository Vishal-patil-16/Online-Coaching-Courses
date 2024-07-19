from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify  # type: ignore
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

DATABASE = 'users.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone_number TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL,
                course_name TEXT NOT NULL,
                message TEXT,
                additional_details TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    phone_number = data['phone_number']
    password = data['password']

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (first_name, last_name, email, phone_number, password)
                VALUES (?, ?, ?, ?, ?)
            ''', (first_name, last_name, email, phone_number, hashed_password))
            conn.commit()
            return jsonify({'message': 'Registration successful'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'message': 'Registration failed, email already exists'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[5], password):
            session['user_id'] = user[0]
            session['email'] = user[3]
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'message': 'Login failed'}), 401

@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/book_course', methods=['POST'])
def book_course():
    data = request.form
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    course_name = data['course_name']
    message = data['message']
    additional_details = data['additional_details']

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM course_bookings WHERE email = ? AND course_name = ?', (email, course_name))
        existing_booking = cursor.fetchone()

        if existing_booking:
            return jsonify({'message': 'You have already booked this course'}), 400

        cursor.execute('''
            INSERT INTO course_bookings (first_name, last_name, email, course_name, message, additional_details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, course_name, message, additional_details))
        conn.commit()

    return jsonify({'message': 'Course booking successful'}), 201

@app.route('/blogs', methods=['GET'])
def get_blogs():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM blogs')
        blogs = cursor.fetchall()
        return jsonify([{"id": blog[0], "title": blog[1], "content": blog[2]} for blog in blogs])

@app.route('/blogs', methods=['POST'])
def add_blog():
    data = request.get_json()
    title = data['title']
    content = data['content']

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO blogs (title, content)
            VALUES (?, ?)
        ''', (title, content))
        conn.commit()
        return jsonify({'message': 'Blog added successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)
