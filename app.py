from flask import Flask, render_template, request, redirect, url_for, flash
import random
import food  # Ensure this contains 'meals_data'
from model import FoodEntry, Session  # Ensure this contains the necessary database functions


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


# Days of the week
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Function to randomly assign meals for each day of the week (using prepopulated data from food.py)
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


# Route for prepopulated meals
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






###



# Create a session
session = Session()

# Constants
DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MEAL_CATEGORIES = ['breakfast', 'lunch', 'dinner']

@app.route('/view')
def display():
    """
    Home page that displays food entries for each category and day.
    """
    # Fetch all entries grouped by meal category
    schedule = {category: {day: [] for day in DAYS_OF_WEEK} for category in MEAL_CATEGORIES}
    entries = session.query(FoodEntry).all()  # Query the database for all food entries

    # Group entries by category and day
    for entry in entries:
        if entry.day in DAYS_OF_WEEK and entry.category in MEAL_CATEGORIES:
            schedule[entry.category][entry.day].append(entry)  # Store the full entry object

    return render_template('index2.html', schedule=schedule, days=DAYS_OF_WEEK, categories=MEAL_CATEGORIES)
@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    """
    Page to add a food entry for a specific day and meal category.
    """
    if request.method == 'POST':
        day = request.form.get('day')
        category = request.form.get('category')
        food_input = request.form.get('food')

        if day in DAYS_OF_WEEK and category in MEAL_CATEGORIES and food_input:
            # Split the input into food pairs (trim spaces and separate by commas)
            food_pairs = [food.strip() for food in food_input.split(',')]
            
            # Randomly select one food from the pairs for the category and day
            selected_food = random.choice(food_pairs)

            # Check if there is already an entry for this day and category
            existing_entry = session.query(FoodEntry).filter_by(day=day, category=category).first()

            if existing_entry:
                # If an entry exists, delete it
                session.delete(existing_entry)
                session.commit()
                flash(f"Existing food entry for {day} in {category} has been removed.", "info")

            # Create a new entry with the selected food for the chosen category and day
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
    food_entry = session.query(FoodEntry).get(id)  # Retrieve the entry by ID
    if not food_entry:
        return "Food entry not found", 404  # If the entry is not found, return a 404 error

    if request.method == 'POST':
        # Retrieve the food input from the form and update the entry
        food_entry.food = request.form.get('food', food_entry.food)  # If no food is provided, keep the old one
        session.commit()  # Commit the changes to the database

        # Redirect to the home page where the updated data will be displayed
        return redirect(url_for('display'))

    return render_template('edit.html', food_entry=food_entry)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_entry(id):
    food_entry = session.query(FoodEntry).get(id)
    if food_entry:
        session.delete(food_entry)
        session.commit()
    return redirect(url_for('display'))




# Test route
@app.route('/hello')
def hello():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
