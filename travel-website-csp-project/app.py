from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import os
import re
from datetime import datetime
from abc import ABC, abstractmethod  # For abstraction
from jinja2 import TemplateNotFound

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

#  REGULAR EXPRESSION VALIDATION
def validate_registration(username, email, password):
    username_pattern = r"^[a-zA-Z0-9_-]{6,16}$"
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    password_pattern = r"^(?=.[A-Za-z])(?=.\d)[A-Za-z\d@$!%*?&]{8,32}$"

    if not re.match(username_pattern, username):
        flash("Invalid username! Must be 6-16 characters with only letters, numbers, _, or -.", "error")
        return False
    if not re.match(email_pattern, email):
        flash("Invalid email format!", "error")
        return False
    if not re.match(password_pattern, password):
        flash("Password must be 8-32 characters and include letters and numbers.", "error")
        return False
    return True

#  BASE MODEL (Abstraction) and SQLalchemy error 
class BaseModel:
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database Error: {e}")

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database Error: {e}")

#  ABSTRACT CLASS (Polymorphism & Abstraction)
class TravelEntity(BaseModel, db.Model):  
    __abstract__ = True  

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    def get_details(self):  
        return f"Travel Entity: {self.name} - {self.description}"

#  USER MODEL (Encapsulation)
class User(UserMixin, BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    __password_hash = db.Column(db.String(128), nullable=False)  

    journal_entries = db.relationship('JournalEntry', backref='author', lazy=True)
    bucket_list_items = db.relationship('BucketListItem', backref='user', lazy=True)

    def __init__(self, username, email, password):
        if not validate_registration(username, email, password):
            raise ValueError("Invalid username, email, or password format")
        self.username = username
        self.email = email
        self.__password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.__password_hash, password)

    @staticmethod
    def get_user_by_username(username):
        return User.query.filter_by(username=username).first()

#  JOURNAL ENTRY MODEL
class JournalEntry(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#  BUCKET LIST MODEL
class BucketListItem(BaseModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#  DESTINATION MODEL (Encapsulation)
class Destination(TravelEntity):
    image_url = db.Column(db.String(500))
    subcategories = db.relationship('Subcategory', backref='destination', lazy=True)

    def __init__(self, name, description, image_url):
        self.name = name
        self.description = description
        self.image_url = image_url

    def get_details(self):  
        return f"Destination: {self.name} - {self.description}"
    
class Subcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'cafe', 'hotel', or 'tourist_destination'
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))

#  HOTEL MODEL (Inheritance)
class Hotel(TravelEntity):
    price_per_night = db.Column(db.Float, nullable=False)

    def __init__(self, name, description, price_per_night):
        self.name = name
        self.description = description
        self.price_per_night = price_per_night

#  FLIGHT MODEL (Inheritance)
class Flight(TravelEntity):
    airline = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Float, nullable=False)

    def __init__(self, name, description, airline, duration):
        self.name = name
        self.description = description
        self.airline = airline
        self.duration = duration

#  STATIC METHOD EXAMPLE
class TravelAgency:
    agency_name = "Global Travels"  

    @staticmethod
    def currency_converter(amount, rate):
        return amount * rate

#  AUTHENTICATION ROUTES
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

    except ValueError:
        flash("Invalid input format", "danger")
    except SQLAlchemyError:
        flash('Database error occurred. Please try again later.', 'danger')

    return render_template('auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/founders')
def founders():
    return render_template('founders.html')

@app.route('/destinations')
@login_required
def destinations():
    destinations = Destination.query.all()
    return render_template('destinations.html', destinations=destinations)

#To test for destinations
@app.route('/test')
def test_data():
    destinations = Destination.query.all()
    return f"Found {len(destinations)} destinations."

@app.route('/seed')
def seed_data():
    mumbai = Destination(
                name='Mumbai',
                description='The city of dreams, known for its vibrant culture and bustling streets.',
                image_url='https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=800'
            )
    udaipur = Destination(
                name='Udaipur',
                description='The city of lakes, famous for its royal heritage and beautiful architecture.',
                image_url='https://images.unsplash.com/photo-1598890777032-bde835ba27c2?auto=format&fit=crop&w=800'
            )
    goa = Destination(
                name='Goa',
                description='A paradise for beach lovers with amazing nightlife and Portuguese influence.',
                image_url='https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800'
            )
            
    db.session.add_all([mumbai, udaipur, goa])
    db.session.commit()
            
    # Add subcategories for Mumbai
    mumbai_places = [
        Subcategory(
            name='Leopold Cafe',
            type='cafe',
            description='Historic cafe with great food and ambiance',
            destination=mumbai,
            image_url='https://images.unsplash.com/photo-1559925393-8be0ec4767c8?auto=format&fit=crop&w=800'
        ),
        Subcategory(
            name='Taj Mahal Palace',
            type='hotel',
            description='Luxury hotel with stunning architecture',
            destination=mumbai,
            image_url='https://images.unsplash.com/photo-1566552881560-0be862a7c445?auto=format&fit=crop&w=800'
        ),
        Subcategory(
            name='Gateway of India',
            type='tourist_destination',
            description='Historic monument and must-visit landmark',
            destination=mumbai,
            image_url='https://images.unsplash.com/photo-1567157577867-05ccb1388e66?auto=format&fit=crop&w=800'
        )
    ]
    
    # Add subcategories for Udaipur
    udaipur_places = [
        Subcategory(
            name='Cafe La Comida',
            type='cafe',
            description='Rooftop cafe with lake views',
            destination=udaipur,
            image_url='https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800'
        ),
        Subcategory(
            name='Taj Lake Palace',
            type='hotel',
            description='Luxury hotel in middle of Lake Pichola',
            destination=udaipur,
            image_url='https://images.unsplash.com/photo-1566552881560-0be862a7c445?auto=format&fit=crop&w=800'
        ),
        Subcategory(
            name='City Palace',
            type='tourist_destination',
            description='Royal palace complex with museums',
            destination=udaipur,
            image_url='https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=800'
        )
    ]
        
    # Add subcategories for Goa
    goa_places = [
        Subcategory(
            name='Cafe Artjuna',
            type='cafe',
            description='Bohemian cafe with great coffee',
            destination=goa,
            image_url='https://images.unsplash.com/photo-1559925393-8be0ec4767c8?auto=format&fit=crop&w=800'
        ),
        Subcategory(
            name='W Goa',
            type='hotel',
            description='Luxury beachfront resort',
            destination=goa,
            image_url='https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800'
        ),
        Subcategory(
            name='Calangute Beach',
            type='tourist_destination',
            description='Popular beach with water sports',
            destination=goa,
            image_url='https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800'
        )
    ]

    db.session.add_all(mumbai_places + udaipur_places + goa_places)
    db.session.commit()
    return "Seeded destinations!"


@app.route('/destination/<int:destination_id>')
@login_required
def destination_detail(destination_id):
    destination = Destination.query.get_or_404(destination_id)
    # Group subcategories by type
    cafes = [s for s in destination.subcategories if s.type == 'cafe']
    hotels = [s for s in destination.subcategories if s.type == 'hotel']
    tourist_spots = [s for s in destination.subcategories if s.type == 'tourist_destination']
    return render_template('destination_detail.html', 
                         destination=destination,
                         cafes=cafes,
                         hotels=hotels,
                         tourist_spots=tourist_spots)

# Journal routes
@app.route('/journal')
@login_required
def journal():
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.date.desc()).all()
    return render_template('journal.html', entries=entries)

#With handling value error
@app.route('/add_journal_entry', methods=['POST'])
@login_required
def add_journal_entry():
    try:
        date_str = request.form.get('date')
        title = request.form.get('title')
        content = request.form.get('content')

        if not date_str or not title or not content:
            raise ValueError("All fields are required.")
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
        entry = JournalEntry(date=date, title=title, content=content, user_id=current_user.id)
        db.session.add(entry)
        db.session.commit()
    
        flash('Journal entry added successfully!', 'success')
        
    except ValueError as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('journal'))
 

#with handling Value Error 
@app.route('/edit_journal_entry/<int:entry_id>', methods=['POST'])
@login_required
def edit_journal_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('You do not have permission to edit this entry.', 'error')
        return redirect(url_for('journal'))
    
    try:
        date_str = request.form.get('date')
        title = request.form.get('title')
        content = request.form.get('content')

        if not date_str or not title or not content:
            raise ValueError("All fields are required.")
    
        entry.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        entry.title = request.form.get('title')
        entry.content = request.form.get('content')
        db.session.commit()
        
        flash('Journal entry updated successfully!', 'success')
    except ValueError as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('journal'))

@app.route('/delete_journal_entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_journal_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('You do not have permission to delete this entry.', 'error')
        return redirect(url_for('journal'))
    
    db.session.delete(entry)
    db.session.commit()
    
    flash('Journal entry deleted successfully!', 'success')
    return redirect(url_for('journal'))

# Bucket list routes
@app.route('/bucketlist')
@login_required
def bucketlist():
    items = BucketListItem.query.filter_by(user_id=current_user.id).all()
    return render_template('bucketlist.html', items=items)

@app.route('/add_bucket_list_item', methods=['POST'])
@login_required
def add_bucket_list_item():
    title = request.form.get('title')
    description = request.form.get('description')

    if not title:
        flash("Title is required!", "error")
        return redirect(url_for('bucketlist'))

    new_item = BucketListItem(
        title=title,
        description=description,
        completed=False,
        user_id=current_user.id
    )
    new_item.save()
    flash("Bucket List item added!", "success")
    return redirect(url_for('bucketlist'))

    #item = BucketListItem(title=key_value, description=description, user_id=current_user.id)
    #db.session.add(item)
    #db.session.commit()
    
    #flash('Bucket list item added successfully!', 'success')
    #return redirect(url_for('bucketlist'))

@app.route('/update_bucket_list_item/<int:item_id>', methods=['POST'])
@login_required
def update_bucket_list_item(item_id):
    item = BucketListItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to update this item.', 'error')
        return redirect(url_for('bucketlist'))
    
    if 'completed' in request.form:
        item.completed = request.form.get('completed') == 'true'
    else:
        item.title = request.form.get('title')
        item.description = request.form.get('description')
    
    db.session.commit()
    flash('Bucket list item updated successfully!', 'success')
    return redirect(url_for('bucketlist'))

@app.route('/delete_bucket_list_item/<int:item_id>', methods=['POST'])
@login_required
def delete_bucket_list_item(item_id):
    item = BucketListItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to delete this item.', 'error')
        return redirect(url_for('bucketlist'))
    
    db.session.delete(item)
    db.session.commit()
    
    flash('Bucket list item deleted successfully!', 'success')
    return redirect(url_for('bucketlist'))

#with TemplateNotFound error
@app.route('/blog')
def custom_page():
    try:
        return render_template('blog.html')  
    except TemplateNotFound:
        return "This file does not exist. Trying going back to home page.", 200  

#  RUN APP
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
