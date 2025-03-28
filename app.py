import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import dns  # required for mongodb+srv:// URIs
from production_overview import production_overview
from equipment_performance import equipment_performance
from quality_control import quality_control
from customer_satisfaction import customer_satisfaction

app = Flask(__name__)
app.config['SECRET_KEY'] = 'no_secret_key_right_now'
app.register_blueprint(production_overview)
app.register_blueprint(equipment_performance)
app.register_blueprint(quality_control)
app.register_blueprint(customer_satisfaction)
bcrypt = Bcrypt(app)

# MongoDB Atlas connection string
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://nikhilvjagtap2003:ra9be97kyhd8wsR9@cluster0.vrqby.mongodb.net/QualityOperations?retryWrites=true&w=majority')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info() 
    db = client.get_database('QualityOperations')
    print("Connected to MongoDB successfully!")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None

def is_valid_email(email):
    email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    return email_regex.match(email)

def is_valid_password(password):
    password_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    return password_regex.match(password)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if db is None:
            flash('Database connection error. Please try again later.', 'error')
            return render_template('login.html')
        
        user = db.users.find_one({'email': request.form['email']})
        if user and bcrypt.check_password_hash(user['password'], request.form['password']):
            session['user_id'] = str(user['_id'])
            flash('Logout successful', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if db is None:
            flash('Database connection error. Please try again later.', 'error')
            return render_template('signup.html')
        
        email = request.form['email']
        password = request.form['password']
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('signup.html')
        
        if not is_valid_password(password):
            flash('Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.', 'error')
            return render_template('signup.html')
        
        existing_user = db.users.find_one({'email': email})
        if existing_user is None:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            try:
                db.users.insert_one({
                    'firstname': request.form['firstname'],
                    'lastname': request.form['lastname'],
                    'role': request.form['role'],
                    'email': email,
                    'password': hashed_password
                })
                flash('Account created successfully', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
        else:
            flash('Email already exists', 'error')
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if db is None:
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('login'))
    
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/api/user')
def get_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    if user:
        return jsonify({
            'firstname': user['firstname'],
            'lastname': user['lastname'],
            'role': user['role']
        })
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)

