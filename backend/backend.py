
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
import requests
import json
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secure_random_key_12345'  # Change to a secure random key

# Load environment variables
load_dotenv()
gmail_address = os.getenv('GMAIL_ADDRESS')
gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')
recipient_email = os.getenv('RECIPIENT_EMAIL')

# Validate environment variables
if not all([gmail_address, gmail_app_password, recipient_email]):
    print("Error: Missing .env variables. Please set GMAIL_ADDRESS, GMAIL_APP_PASSWORD, and RECIPIENT_EMAIL.")
    exit(1)

# SQLite database setup
def init_db():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )''')
        conn.commit()

init_db()

# ThingSpeak configuration
channel_id = "2978629"
read_api_key = "CI1ZEWQ00DXHT87Q"
base_url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_api_key}"

# Decision tree model
X_train = np.array([
    [70, 36.5, 50], [80, 37.0, 55], [60, 36.8, 45], [75, 36.2, 60],
    [120, 38.5, 70], [110, 39.0, 65], [130, 38.0, 75], [100, 39.5, 80]
])
y_train = np.array([0, 0, 0, 0, 1, 1, 1, 1])

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
model = DecisionTreeClassifier(max_depth=3, random_state=42)
model.fit(X_train_scaled, y_train)

# Email cooldown
last_email_time = None
EMAIL_COOLDOWN = timedelta(minutes=5)
DISABLE_COOLDOWN = True  # Set to False after email testing

def send_email_alert(subject, message):
    global last_email_time
    current_time = datetime.now()
    
    try:
        if DISABLE_COOLDOWN or last_email_time is None or (current_time - last_email_time) >= EMAIL_COOLDOWN:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = gmail_address
            msg['To'] = recipient_email

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(gmail_address, gmail_app_password)
                server.sendmail(gmail_address, recipient_email, msg.as_string())
            
            last_email_time = current_time
            print(f"Email sent successfully to {recipient_email} at {current_time}")
            return True
        else:
            print(f"Email blocked: Cooldown active until {last_email_time + EMAIL_COOLDOWN}")
            return False
    except smtplib.SMTPAuthenticationError as e:
        print(f"Email authentication error: {e.smtp_code}, {e.smtp_error.decode()}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        print(f"General email error: {str(e)}")
        return False

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([name, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')

        try:
            with sqlite3.connect('users.db') as conn:
                c = conn.cursor()
                c.execute('SELECT id FROM users WHERE email = ?', (email,))
                if c.fetchone():
                    flash('Email already registered.', 'error')
                    return render_template('signup.html')
                
                password_hash = generate_password_hash(password)
                c.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                         (name, email, password_hash))
                conn.commit()
                flash('Signup successful! Please log in.', 'success')
                return redirect(url_for('login'))
        except Exception as e:
            print(f"Signup error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([email, password]):
            flash('Email and password are required.', 'error')
            return render_template('login.html')

        try:
            with sqlite3.connect('users.db') as conn:
                c = conn.cursor()
                c.execute('SELECT id, name, password_hash FROM users WHERE email = ?', (email,))
                user = c.fetchone()
                if user and check_password_hash(user[2], password):
                    session['user_id'] = user[0]
                    session['user_name'] = user[1]
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid email or password.', 'error')
                    return render_template('login.html')
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))
    return render_template('index.html', user_name=session.get('user_name'))

@app.route('/test_email')
def test_email():
    result = send_email_alert("Test Email", "This is a test email from the Patient Monitoring System.")
    return jsonify({"status": "Email sent" if result else "Email failed"})

@app.route('/api/vitals', methods=['GET'])
def get_vitals():
    try:
        response = requests.get(f"{base_url}&results=1")
        response.raise_for_status()
        data = json.loads(response.text)
        feeds = data.get('feeds', [])
        
        if not feeds:
            print("Error: No data available from ThingSpeak")
            return jsonify({"error": "No data available"}), 404
        
        latest = feeds[0]
        if all(key in latest and latest[key] != '' and latest[key] is not None for key in ['field1', 'field2', 'field3']):
            pulse = float(latest['field1'])
            temp = float(latest['field2'])
            humidity = float(latest['field3'])
            
            X_test = scaler.transform([[pulse, temp, humidity]])
            prediction = model.predict(X_test)[0]
            status = "Abnormal" if prediction == 1 else "Normal"
            
            if status == "Abnormal":
                subject = "Patient Health Alert"
                message = (f"ALERT: Patient anomaly detected!\n"
                           f"Pulse: {pulse:.0f} BPM\n"
                           f"Temperature: {temp:.1f}°C\n"
                           f"Humidity: {humidity:.1f}%\n"
                           f"Time: {latest['created_at']}")
            else:
                subject = "Patient Health Update"
                message = (f"Patient vitals are normal.\n"
                           f"Pulse: {pulse:.0f} BPM\n"
                           f"Temperature: {temp:.1f}°C\n"
                           f"Humidity: {humidity:.1f}%\n"
                           f"Time: {latest['created_at']}")
            
            if send_email_alert(subject, message):
                print(f"Email alert triggered for {status} status")
            else:
                print(f"Email alert failed or on cooldown for {status} status")
            
            return jsonify({
                "pulse": pulse,
                "temperature": temp,
                "humidity": humidity,
                "status": status,
                "timestamp": latest['created_at']
            })
        else:
            print("Error: Incomplete or empty data from ThingSpeak")
            return jsonify({"error": "Incomplete data"}), 400
    
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/vitals/history', methods=['GET'])
def get_vitals_history():
    try:
        response = requests.get(f"{base_url}&results=50")
        response.raise_for_status()
        data = json.loads(response.text)
        feeds = data.get('feeds', [])
        
        if not feeds:
            print("Error: No historical data available from ThingSpeak")
            return jsonify({"error": "No historical data available"}), 404
        
        history = []
        for feed in feeds:
            if all(key in feed and feed[key] != '' and feed[key] is not None for key in ['field1', 'field2', 'field3']):
                pulse = float(feed['field1'])
                temp = float(feed['field2'])
                humidity = float(feed['field3'])
                X_test = scaler.transform([[pulse, temp, humidity]])
                status = "Abnormal" if model.predict(X_test)[0] == 1 else "Normal"
                history.append({
                    "pulse": pulse,
                    "temperature": temp,
                    "humidity": humidity,
                    "status": status,
                    "timestamp": feed['created_at']
                })
        
        if not history:
            print("Error: No valid historical data from ThingSpeak")
            return jsonify({"error": "No valid historical data"}), 400
        
        return jsonify(history)
    
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)