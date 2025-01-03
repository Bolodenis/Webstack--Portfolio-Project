"""
Flask Web Application for Meal Planning, User Authentication, and Recipe Search.

This Flask application allows users to plan meals for the week, manage their meal entries in a database, 
search for recipes using the Spoonacular API, and track expenses. The application includes a user authentication 
system with registration, login, password reset, and logout functionality. It also supports sending contact messages via email.

Features:
- User authentication (register, login, logout)
- Meal planning with a database to store user meal entries
- Recipe search via Spoonacular API
- Contact form with email sending
- Basic error handling and user feedback via flash messages

Dependencies:
- Flask
- Flask-SQLAlchemy
- Flask-Login
- requests
- werkzeug (for password hashing)
- smtplib (for sending email)
"""


from flask import Flask, render_template, request, redirect, url_for, flash
from email_service import send_email  
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import food  
from model import FoodEntry, Session  
import requests

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///model.db'
app.config['SECRET_KEY'] = "Bolo@3207334"

# Initialize database
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Days of the week
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Function to randomly assign meals for each day of the week
def assign_meals():
    meals = {
        "breakfast": [meal['name'] for meal in food.meals_data[0]['breakfast']],
        "lunch": [meal['name'] for meal in food.meals_data[0]['lunch']],
        "dinner": [meal['name'] for meal in food.meals_data[0]['dinner']]
    }

    weekly_meals = {}
    for day in days_of_week:
        daily_meals = {
            "breakfast": random.choice(meals['breakfast']),
            "lunch": random.choice(meals['lunch']),
            "dinner": random.choice(meals['dinner'])
        }
        weekly_meals[day] = daily_meals

    return weekly_meals

# Routes
# Home page route (base page)
@app.route("/")
def index():
    if current_user.is_authenticated:
        weekly_meals = assign_meals()
        return render_template("base.html", weekly_meals=weekly_meals)
    else:
        return redirect(url_for('login'))  # Redirect to login page if not logged in


@app.route("/breakfast")
def breakfast():
    weekly_meals = assign_meals()
    breakfast_meals = {day: meals["breakfast"] for day, meals in weekly_meals.items()}
    return render_template("breakfast.html", breakfast_meals=breakfast_meals)

@app.route("/lunch")
def lunch():
    weekly_meals = assign_meals()
    lunch_meals = {day: meals["lunch"] for day, meals in weekly_meals.items()}
    return render_template("lunch.html", lunch_meals=lunch_meals)

@app.route("/dinner")
def dinner():
    weekly_meals = assign_meals()
    dinner_meals = {day: meals["dinner"] for day, meals in weekly_meals.items()}
    return render_template("dinner.html", dinner_meals=dinner_meals)

@app.route("/food_plan")
def food_plan():
    return render_template("tracker.html")

# Database session
session = Session()

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MEAL_CATEGORIES = ['breakfast', 'lunch', 'dinner']

@app.route('/view')
def display():
    schedule = {category: {day: [] for day in DAYS_OF_WEEK} for category in MEAL_CATEGORIES}
    entries = session.query(FoodEntry).all()

    for entry in entries:
        if entry.day in DAYS_OF_WEEK and entry.category in MEAL_CATEGORIES:
            schedule[entry.category][entry.day].append(entry)

    return render_template('index2.html', schedule=schedule, days=DAYS_OF_WEEK, categories=MEAL_CATEGORIES)

@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if request.method == 'POST':
        day = request.form.get('day')
        category = request.form.get('category')
        food_input = request.form.get('food')

        if day in DAYS_OF_WEEK and category in MEAL_CATEGORIES and food_input:
            food_pairs = [food.strip() for food in food_input.split(',')]
            selected_food = random.choice(food_pairs)

            existing_entry = session.query(FoodEntry).filter_by(day=day, category=category).first()
            if existing_entry:
                session.delete(existing_entry)
                session.commit()

            new_entry = FoodEntry(day=day, category=category, food=selected_food)
            session.add(new_entry)
            session.commit()

            flash(f"New food entry '{selected_food}' added for {day}.", "success")
            return redirect(url_for('add_entry'))
        else:
            flash("Invalid input. Please try again.", "danger")

    return render_template('add.html', days=DAYS_OF_WEEK, categories=MEAL_CATEGORIES)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_entry(id):
    food_entry = session.query(FoodEntry).get(id)
    if not food_entry:
        return "Food entry not found", 404

    if request.method == 'POST':
        food_entry.food = request.form.get('food', food_entry.food)
        session.commit()
        return redirect(url_for('display'))

    return render_template('edit.html', food_entry=food_entry)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_entry(id):
    food_entry = session.query(FoodEntry).get(id)
    if food_entry:
        session.delete(food_entry)
        session.commit()
    return redirect(url_for('display'))

# Spoonacular API integration
def search_recipe(query, page=1, limit=10):
    api_key = '8f43cb1856b74d10865f47eb884c7b7e'
    api_url = f'https://api.spoonacular.com/recipes/complexSearch?query={query}&apiKey={api_key}&number={limit}&offset={(page-1) * limit}'
    response = requests.get(api_url)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_recipe_details(recipe_id):
    api_key = '8f43cb1856b74d10865f47eb884c7b7e'
    api_url = f'https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={api_key}'
    response = requests.get(api_url)

    if response.status_code == 200:
        return response.json()
    else:
        return None

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')  
    page = int(request.args.get('page', 1))
    per_page = 3

    if not query:
        return render_template('form.html', message="Please provide a search query.", total_pages=1, page=page)

    data = search_recipe(query, page, per_page)
    if data and 'results' in data:
        total_results = data.get('totalResults', 0)
        total_pages = (total_results // per_page) + (1 if total_results % per_page else 0)
        recipes = data['results']

        recipe_data = []
        for recipe in recipes:
            recipe_details = get_recipe_details(recipe['id'])
            if recipe_details:
                # Extract ingredients correctly
                ingredients = recipe_details.get('extendedIngredients', [])
                nutrition = recipe_details.get('nutrition', {})
                recipe_data.append({
                    'title': recipe['title'],
                    'image': recipe['image'],
                    'ingredients': ingredients,  
                    'nutrition': nutrition,
                    'instructions': recipe_details.get('instructions', 'No instructions available'),
                    'id': recipe['id']
                })

        return render_template('form.html', recipes=recipe_data, total_pages=total_pages, page=page, query=query)
    else:
        return render_template('form.html', message="No recipes found.", total_pages=1, page=page)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Send email
        send_email(name, email, message)

        return render_template('contact.html', message="Thank you for reaching out, we'll get back to you soon!")

    return render_template('contact.html', message=None)

# expense tracker 
# Store expenses as a dictionary
expenses = {}

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # Get form data
        category = request.form.get('category')
        amount = request.form.get('amount')

        # Validate input
        if category and amount:
            try:
                amount = float(amount)  # Convert amount to a number
                
                # Update or add the category in the dictionary
                if category in expenses:
                    expenses[category] += amount
                else:
                    expenses[category] = amount

            except ValueError:
                pass  # Handle invalid input gracefully

        return redirect(url_for('dashboard'))

    # Pass expenses to the template as a list of tuples
    return render_template('dashboard.html', expenses=expenses.items())

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))  # Redirect to homepage if already logged in

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))  # Redirect to homepage after successful login
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template("login.html")

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if all required fields are provided
        if not email:
            flash("Email is required", "error")  # Flash an error message
            return redirect(url_for('register'))

        if not username:
            flash("Username is required", "error")
            return redirect(url_for('register'))

        if not password:
            flash("Password is required", "error")
            return redirect(url_for('register'))

        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email is already registered. Please choose another.", "error")
            return redirect(url_for('register'))

        # Now, safely hash the password
        hashed_password = generate_password_hash(password)

        # Create new user instance
        new_user = User(username=username, email=email, password=hashed_password)

        try:
            # Attempt to add the user to the database
            db.session.add(new_user)
            db.session.commit()  # Commit the transaction
            flash("Registration successful", "success")
            return redirect(url_for('login'))  # Redirect to the login page after successful registration
        except Exception as e:
            # Handle any potential database errors
            db.session.rollback()  # Rollback if there is an error
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('register'))

    return render_template('register.html')

# Forgot password page
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        # Check if email exists, send reset link, etc.
        flash("If your email exists in our system, you will receive a password reset link.")
        return redirect(url_for('login'))
    return render_template('forgot_password.html')



# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("logging out")

    return redirect(url_for('login'))  # Redirect to login page after logout


if __name__ == "__main__":
    app.run(debug=True)
