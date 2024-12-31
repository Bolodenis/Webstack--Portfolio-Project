from flask import Flask, render_template, request, redirect, url_for, flash
from email_service import send_email  # Import the send_email function

import random
import food  # Ensure this contains 'meals_data'
from model import FoodEntry, Session  # Ensure this contains the necessary database functions
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

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
@app.route("/")
def index():
    weekly_meals = assign_meals()
    return render_template("base.html", weekly_meals=weekly_meals)

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
    query = request.args.get('query')  # Correct usage of Flask's request object
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
                    'ingredients': ingredients,  # Now we are passing the ingredients
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


if __name__ == "__main__":
    app.run(debug=True)
