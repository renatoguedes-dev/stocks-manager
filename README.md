# Stock Manager Simulator

## Overview
This is a stock manager simulator web application built using Flask. It allows users to manage their stock portfolio by buying and selling stocks, and viewing their transaction history.

## Features
- User authentication and registration
- Buy and sell stocks
- View current portfolio and transaction history
- Change password

## Technologies Used
- Python
- Flask
- SQLite
- Jinja2
- Bootstrap

## Setup and Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/stock-manager-simulator.git
    cd stock-manager-simulator
    ```

2. **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the database:**
    - Ensure you have `sqlite3` installed on your system.
    - Run the following command to create the database and set up the schema:
    ```bash
    sqlite3 finance.db < schema.sql
    ```

5. **Run the application:**
    ```bash
    flask run
    ```

## Usage
- Visit `http://127.0.0.1:5000` in your browser.
- Register for a new account or log in with an existing account.
- Start managing your stock portfolio!

## File Structure
- `app.py`: The main Flask application file.
- `templates/`: Directory containing HTML templates.
- `static/`: Directory containing static files (CSS, JavaScript).
- `schema.sql`: SQL file to set up the database schema.
