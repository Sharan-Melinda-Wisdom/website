import re
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Get the absolute path of the current directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Log file path: app.log inside the BASE_DIR directory
log_file = os.path.join(BASE_DIR, 'app.log')

# Configure logging
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
console_handler.setFormatter(console_format)
logging.getLogger().addHandler(console_handler)

# Function to initialize the database
def init_db():
    db_path = os.path.join(BASE_DIR, 'users.db')  # Database path in the app folder

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )''')
        conn.commit()

# Call init_db when the app starts to make sure the database and table are created
init_db()

# Email validation function
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$'
    return re.match(email_regex, email) is not None

# Password validation function
def is_valid_password(password):
    # Password should be at least 8 characters long, and include at least one uppercase letter,
    # one number, and one special character.
    password_regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(password_regex, password) is not None

# Route for Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the email is valid
        if not is_valid_email(email):
            flash("Invalid email format.", "danger")
            return redirect(url_for('signup'))

        # Check if the password is valid
        if not is_valid_password(password):
            flash("Password must be at least 8 characters long, contain at least one uppercase letter, one number, and one special character.", "danger")
            return redirect(url_for('signup'))

        db_path = os.path.join(BASE_DIR, 'users.db')

        # Insert new user into the database
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                          (username, email, password))
                conn.commit()
                flash("Account created successfully!", "success")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Username or Email already exists.", "danger")
                return redirect(url_for('signup'))

    return render_template('signup.html')

# Route for Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the email is valid
        if not is_valid_email(email):
            flash("Invalid email format.", "danger")
            return redirect(url_for('login'))

        db_path = os.path.join(BASE_DIR, 'users.db')

        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
            user = c.fetchone()

            if user:
                session['user_id'] = user[0]  # Store user ID in session
                session['username'] = user[1]  # Store username in session
                session['email'] = user[2]     # Store email in session
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials.", "danger")

    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if the email is valid
        if not is_valid_email(email):
            flash("Invalid email format.", "danger")
            return redirect(url_for('forgot_password'))

        # Check if the passwords match
        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('forgot_password'))

        # Validate password format
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+={}|\[\]:;"\'<>,.?/\\-]).{8,}$'
        if not re.match(password_regex, new_password):
            flash('Password must be at least 8 characters long, contain one uppercase letter, one lowercase letter, one number, and one special character.', 'danger')
            return redirect(url_for('forgot_password'))

        db_path = os.path.join(BASE_DIR, 'users.db')

        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = c.fetchone()

            if user:
                # Update the user's password in the database
                c.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
                conn.commit()
                flash('Your password has been successfully updated!', 'success')
                return redirect(url_for('login'))
            else:
                flash('Email not found!', 'danger')
                return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

# Route for Contact Us
@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Get data from the form
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # Debugging log
        app.logger.debug(f"Received data - Name: {name}, Email: {email}, Message: {message}")

        # Validate the email
        if not is_valid_email(email):
            flash("Invalid email format.", "danger")
            return redirect(url_for('contact'))

        # Get the absolute path for the contact messages file
        contact_file = os.path.join(BASE_DIR, 'contact_messages.txt')

        # Save the data to a text file
        try:
            with open(contact_file, "a") as f:
                f.write(f"Name: {name}\nEmail: {email}\nMessage: {message}\n\n")
            app.logger.info("Message saved successfully!")
            flash("Thank you for your message!", "success")
        except Exception as e:
            app.logger.error(f"Error while saving message: {e}")
            flash("There was an issue saving your message. Please try again.", "danger")

    return render_template('contact.html')


# Route for Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('email', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Helper function to handle volunteer registration (DRY refactor)
def register_volunteer(file_name, campaign_name, campaign_key):
    if 'user_id' not in session:
        flash("You need to be logged in to register as a volunteer.", "info")
        return redirect(url_for('login'))

    email = session['email']

    db_path = os.path.join(BASE_DIR, 'users.db')
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE email = ?", (email,))
        user = c.fetchone()

        if user:
            username = user[0]
            volunteer_file = os.path.join(BASE_DIR, file_name)
            try:
                with open(volunteer_file, "a") as f:
                    f.write(f"Username: {username}, Email: {email}\n")
                flash(f"You have successfully registered as a volunteer for the {campaign_name}!", "success")
                return redirect(url_for('dashboard', success=True, campaign=campaign_key))
            except Exception as e:
                app.logger.error(f"Error while writing to {file_name}: {e}")
                flash("There was an issue registering you as a volunteer. Please try again.", "danger")
                return redirect(url_for('dashboard'))
        else:
            flash("User not found in the database.", "danger")
            return redirect(url_for('dashboard'))

@app.route('/register_volunteer1', methods=['POST'])
def register_volunteer1():
    return register_volunteer("BeachCleaningVolunteers.txt", "Beach Cleanup", "beach_cleanup")

@app.route('/register_volunteer2', methods=['POST'])
def register_volunteer2():
    return register_volunteer("TreePlantVolunteers.txt", "Tree Plantation", "tree_plantation")

@app.route('/register_volunteer3', methods=['POST'])
def register_volunteer3():
    return register_volunteer("FoodVolunteers.txt", "Food Distribution", "food_distribution")

@app.route('/register_volunteer4', methods=['POST'])
def register_volunteer4():
    return register_volunteer("EduVolunteers.txt", "Educate the Underprivileged", "education")

# Route to display the dashboard page
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "info")
        return redirect(url_for('login'))
    success = request.args.get('success', False)
    username = session.get('username', '')
    return render_template('dashboard.html', success=success, username=username)

@app.route('/')
def home():
    app.logger.debug('Home page accessed')
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('AboutUs.html')

@app.route('/campaigns')
def campaigns():
    return render_template('campaigns.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/donate')
def donate():
    return render_template('Donate.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

if __name__ == '__main__':
    app.run(debug=True)
