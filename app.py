# my_flask_app/app.py

from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, jsonify
import pymysql.cursors
import os
import secrets
import logging
from logging.handlers import RotatingFileHandler # For basic log rotation

app = Flask(__name__)

# --- Application Configuration ---
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
APP_VERSION = os.getenv('APP_VERSION', 'V1')

# Database Configuration
DB_HOST = os.getenv('MYSQL_HOST')
DB_USER = os.getenv('MYSQL_USER')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
DB_NAME = os.getenv('MYSQL_DATABASE')

# --- Configure Logging for the Application and Flask Requests ---
# Set Flask's default logger level
app.logger.setLevel(logging.INFO)

# Remove any default handlers Flask might add in debug mode to prevent duplicates
for handler in app.logger.handlers:
    app.logger.removeHandler(handler)

# Create a file handler for the main app log
# Using RotatingFileHandler for basic log rotation (preventing single huge log file)
# Max 1 MB per file, keep 5 backup files
log_file_path = '/var/log/my_flask_app/app.log'
file_handler = RotatingFileHandler(log_file_path, maxBytes=1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

# Also capture werkzeug (Flask's internal server) logs
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)
werkzeug_logger.addHandler(file_handler) # Send werkzeug logs to the same file

# For errors, you might want a separate error log (optional, but good for separation)
error_log_file_path = '/var/log/my_flask_app/app_error.log'
error_handler = RotatingFileHandler(error_log_file_path, maxBytes=1024 * 1024, backupCount=5)
error_handler.setLevel(logging.ERROR) # Only log ERROR and CRITICAL messages
error_handler.setFormatter(formatter)
app.logger.addHandler(error_handler)


def get_db_connection():
    """Establishes a connection to the MySQL database."""
    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
        app.logger.error("Database environment variables are not fully set.")
        return None

    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        app.logger.error(f"Error connecting to database: {e}")
        return None

# --- Routes ---
@app.route('/')
def index():
    app.logger.info("Accessing home page.")
    return render_template('index.html', app_version=APP_VERSION)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    age = request.form['age']
    email = request.form['email']
    gender = request.form['gender']
    app.logger.info(f"Received submission for user: {email}")

    connection = get_db_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    age INT,
                    email VARCHAR(255) UNIQUE,
                    gender VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                cursor.execute(create_table_sql)
                connection.commit()

                check_sql = "SELECT id FROM users WHERE email = %s"
                cursor.execute(check_sql, (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash(f"User with email '{email}' already exists!", 'error')
                    app.logger.warning(f"Duplicate submission detected for email: {email}")
                else:
                    insert_sql = "INSERT INTO users (name, age, email, gender) VALUES (%s, %s, %s, %s)"
                    cursor.execute(insert_sql, (name, age, email, gender))
                    connection.commit()
                    flash(f"User '{name}' data submitted successfully!", 'success')
                    app.logger.info(f"Successfully submitted data for user: {email}")
        except pymysql.err.IntegrityError as e:
            if "Duplicate entry" in str(e):
                flash(f"Error: User with email '{email}' already exists (Integrity Error)!", 'error')
                app.logger.error(f"Integrity error - duplicate email: {email}")
            else:
                connection.rollback()
                flash(f"Database integrity error: {e}", 'error')
                app.logger.error(f"Database integrity error for {email}: {e}")
        except Exception as e:
            connection.rollback()
            flash(f"Error submitting data: {e}", 'error')
            app.logger.critical(f"Unhandled error during submission for {email}: {e}")
        finally:
            connection.close()
    else:
        flash("Failed to connect to the database. Check server logs.", 'error')
        app.logger.critical("Failed to establish database connection during submission.")

    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    try:
        connection = get_db_connection()
        if connection:
            connection.close()
            app.logger.info("Health check: Database connection OK.")
            return jsonify({"status": "healthy", "database_connection": "ok", "app_version": APP_VERSION}), 200
        else:
            app.logger.error("Health check: Database connection FAILED.")
            return jsonify({"status": "unhealthy", "database_connection": "failed", "app_version": APP_VERSION}), 500
    except Exception as e:
        app.logger.critical(f"Health check failed due to unexpected error: {e}")
        return jsonify({"status": "unhealthy", "error": str(e), "app_version": APP_VERSION}), 500


if __name__ == '__main__':
    # Initial database and table setup
    # Note: When Systemd runs this, it executes this block.
    # It's generally better to use separate migration scripts for production.
    conn = None
    try:
        if all([DB_HOST, DB_USER, DB_PASSWORD]):
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            conn.close()

            db_connection = get_db_connection()
            if db_connection:
                with db_connection.cursor() as cursor:
                    create_table_sql = """
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        age INT,
                        email VARCHAR(255) UNIQUE,
                        gender VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                    cursor.execute(create_table_sql)
                db_connection.commit()
                db_connection.close()
                app.logger.info(f"Database '{DB_NAME}' and table 'users' ensured with UNIQUE email constraint.")
        else:
            app.logger.warning("Skipping initial DB setup: Database environment variables not fully set for __main__ block.")
    except Exception as e:
        app.logger.critical(f"Initial DB setup failed: {e}")
    finally:
        if conn and conn.open:
            conn.close()

    # This runs Flask's development server.
    # In a real production setup, you'd use a WSGI server like Gunicorn/Waitress.
    app.run(host='0.0.0.0', port=5000, debug=True)