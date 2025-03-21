from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime



# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.route('/')
def index():
    return render_template('index.html')  # Make sure 'index.html' exists in the 'templates' folder

@app.route('/founders')
def founders():
    return render_template('founders.html')  # Make sure 'founders.html' exists in 'templates/'



db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --------------------------
#  BASE MODEL (No Metaclass Conflict)
# --------------------------
class BaseModel:
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

# --------------------------
#  USER MODEL
# --------------------------
class User(UserMixin, BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    __password_hash = db.Column(db.String(128), nullable=False)  # Encapsulation (private)

    journal_entries = db.relationship('JournalEntry', backref='author', lazy=True)
    bucket_list_items = db.relationship('BucketListItem', backref='user', lazy=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.__password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.__password_hash, password)

    @staticmethod
    def get_user_by_username(username):
        return User.query.filter_by(username=username).first()

# --------------------------
#  JOURNAL ENTRY MODEL
# --------------------------
class JournalEntry(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --------------------------
#  BUCKET LIST MODEL
# --------------------------
class BucketListItem(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --------------------------
#  DESTINATION MODEL
# --------------------------
class Destination(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    subcategories = db.relationship('Subcategory', backref='destination', lazy=True)

# --------------------------
#  AUTHENTICATION ROUTES
# --------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.get_user_by_username(username)
            if user and user.check_password(password):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            flash('Invalid username or password', 'error')

    except SQLAlchemyError:
        flash('Database error occurred. Please try again later.', 'danger')

    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            if User.get_user_by_username(username):
                flash('Username already exists', 'error')
                return redirect(url_for('register'))

            user = User(username, email, password)
            user.save()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))

    except SQLAlchemyError:
        flash('Database error occurred. Please try again later.', 'danger')

    return render_template('auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# --------------------------
#  STATIC METHOD EXAMPLE
# --------------------------
class TravelAgency:
    agency_name = "Global Travels"  # Class Variable

    @staticmethod
    def currency_converter(amount, rate):
        return amount * rate

# --------------------------
#  RUN APP
# --------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

