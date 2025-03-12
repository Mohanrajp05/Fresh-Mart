import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from bson.objectid import ObjectId

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# MongoDB Connection
app.config["MONGO_URI"] = "mongodb+srv://Mohan7676:Mohan123@cluster0.lchvw.mongodb.net/shop_db?retryWrites=true&w=majority"
# Set SSL config as separate parameters
app.config['MONGO_SSL'] = True
app.config['MONGO_SSL_CERT_REQS'] = None  # Don't validate cert - option CERT_NONE in ssl module
mongo = PyMongo(app)

def load_products():
    with open('static/data/products.json', 'r') as f:
        return json.load(f)

@app.route('/')
def index():
    products = load_products()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = mongo.db.users.find_one({"email": email})
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('index'))

        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if mongo.db.users.find_one({"email": email}):
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        user_id = mongo.db.users.insert_one({
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password)
        }).inserted_id

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Process the payment (mock)
        flash('Payment processed successfully!', 'success')
        return redirect(url_for('success'))
    return render_template('checkout.html')

@app.route('/success')
def success():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('success.html')

# Create indexes and initial collections if they don't exist
try:
    with app.app_context():
        # Create unique indexes
        mongo.db.users.create_index('email', unique=True)
        mongo.db.users.create_index('username', unique=True)
        app.logger.info("Successfully connected to MongoDB")
except Exception as e:
    app.logger.error(f"MongoDB connection failed: {str(e)}")
    app.logger.info("Using in-memory mode")
    # Fallback to in-memory user storage
    from werkzeug.local import LocalProxy
    
    class MemoryUserStore:
        def __init__(self):
            self.users = {}
            self.next_id = 1
            
        def find_one(self, query):
            if 'email' in query:
                for user in self.users.values():
                    if user['email'] == query['email']:
                        return user
            return None
            
        def insert_one(self, user_data):
            user_id = str(self.next_id)
            self.next_id += 1
            user_data['_id'] = user_id
            self.users[user_id] = user_data
            class Result:
                def __init__(self, id):
                    self.inserted_id = id
            return Result(user_id)
            
    # Replace mongo.db.users with in-memory store
    class FakeDb:
        def __init__(self):
            self.users = MemoryUserStore()
            
    mongo.db = FakeDb()