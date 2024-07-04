import datetime
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from flask_session import Session
from helpers import apology, is_positive_integer, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # HTML table summarizing which stocks the user owns, the numbers of shares
    # owned, the current price of each stock, and the total value of each holding

    # select logged user
    users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

    # select users current cash
    cash = users[0]["cash"]

    user_balance = cash
    total_shares_balance = 0

    # Get users portfolio
    portfolio = db.execute(
        "SELECT symbol, SUM(share_quantity) as total_shares FROM portfolio WHERE user_id = ? GROUP BY symbol", session["user_id"])

    for stock in portfolio:
        quote = lookup(stock["symbol"])
        stock["price"] = quote["price"]
        current_total_price = quote["price"] * stock["total_shares"]

        # add the current stock position to the user's balance
        user_balance += current_total_price

        # add current stock position to the total shares balance
        total_shares_balance += current_total_price

    return render_template("index.html", portfolio=portfolio, cash=cash, total_shares_balance=total_shares_balance, user_balance=user_balance)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        transaction_type = "buy"
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        quote = lookup(symbol)

        if not quote:
            return apology("Symbol not found")

        elif not shares:
            return apology("Amount of shares not provided")

        elif not is_positive_integer(shares):
            return apology("Amount of shares must be a positive integer")

        # check the current price and multiply for the number of shares
        shares = int(shares)
        total = quote["price"] * shares
        rounded_total = round(total, 2)

        # check if user has enough cash
        users = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"]
        )
        current_balance = users[0]["cash"]

        remaining_balance = current_balance - rounded_total
        if remaining_balance < 0:
            return apology("Not enough balance to buy the shares")

        # Get the current date and time
        current_datetime = datetime.datetime.now()
        # Format the current date and time as a string
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        db.execute("BEGIN TRANSACTION")

        # insert purchase information on the transactions table
        db.execute(
            """
            INSERT INTO transactions (
                username,
                symbol,
                share_price,
                share_quantity,
                total_paid,
                type,
                user_id,
                timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            session["username"],
            quote["symbol"],
            quote["price"],
            shares,
            total,
            transaction_type,
            session["user_id"],
            formatted_datetime,
        )

        # update user's cash
        db.execute(
            """
            UPDATE users
            SET cash = ?
            WHERE id = ?
            """,
            remaining_balance,
            session["user_id"],
        )

        users = db.execute("SELECT symbol, SUM(share_quantity) as total_shares FROM transactions WHERE user_id = ? and symbol = ?",
                           session["user_id"], quote["symbol"])
        portfolio = db.execute(
            "SELECT * FROM portfolio WHERE user_id = ? AND symbol = ?", session["user_id"], quote["symbol"])

        # if user already has a portfolio with the stock being transacted this will happen:
        if portfolio:
            portfolio_shares = users[0]["total_shares"]
            db.execute("UPDATE portfolio SET share_quantity = ? WHERE user_id = ? AND symbol = ?",
                       portfolio_shares, session["user_id"], quote["symbol"])

        else:
            # insert buy information on portfolio table
            db.execute(
                """
                INSERT INTO portfolio (
                    user_id,
                    symbol,
                    share_quantity
                    ) VALUES (?, ?, ?)
                """,
                session["user_id"],
                quote["symbol"],
                shares,
            )

        flash(
            f"Successfully bought {shares} shares of {quote["symbol"]} for {usd(rounded_total)}."
        )

        db.execute("COMMIT")

        return redirect("/")

    else:

        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", session["user_id"])

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)

        if not quote:
            return apology("Symbol not found")

        return render_template("quoted.html", quote=quote)

    else:

        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        usuarios = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if not username:
            return apology("Providing a username is required")

        elif not password:
            return apology("Password is required")

        elif not confirmation:
            return apology("Confirming password is required")

        elif len(usuarios) != 0:
            return apology("Username already exists")

        elif password != confirmation:
            return apology(
                "Please ensure that the passwords entered in both fields are identical. Passwords are case-sensitive.",
                400,
            )

        # creates a hash for the password
        hash = generate_password_hash(password)

        # includes the username and password hash in the db
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

        usuarios = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Remember which user has registered and keep them logged in
        session["user_id"] = usuarios[0]["id"]
        session["username"] = username

        flash("Registered!")

        return redirect("/")

    else:

        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        transaction_type = "sell"
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("You must select a symbol")

        shares = request.form.get("shares")
        quote = lookup(symbol)

        if not quote:
            return apology("Symbol not found")

        elif not shares:
            return apology("Amount of shares not informed")

        elif not is_positive_integer(shares):
            return apology("Amount of shares must be a positive integer")

        # check the current price and multiply for the number of shares
        shares = int(shares)
        total = quote["price"] * shares
        rounded_total = round(total, 2)

        stock_portfolio = db.execute(
            "SELECT symbol, share_quantity FROM portfolio WHERE user_id = ? AND symbol = ?", session["user_id"], quote["symbol"])
        shares_from_portfolio = stock_portfolio[0]["share_quantity"]

        if shares > shares_from_portfolio:
            return apology("You don't have that amount of shares to sell")

        db.execute("BEGIN TRANSACTION")

        # get current user's cash
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        cash = user[0]["cash"]

        # updated value to be set to the user's cash
        updated_balance = cash + rounded_total

        # deposit rounded total to the user's cash
        db.execute(
            """
            UPDATE users
            SET cash = ?
            WHERE id = ?
            """,
            updated_balance,
            session["user_id"],
        )

        # Get the current date and time
        current_datetime = datetime.datetime.now()
        # Format the current date and time as a string
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        negative_shares = shares * -1
        # add entry to the transactions
        db.execute(
            """
            INSERT INTO transactions (
                username,
                symbol,
                share_price,
                share_quantity,
                total_paid,
                type,
                user_id,
                timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            session["username"],
            quote["symbol"],
            quote["price"],
            negative_shares,
            total,
            transaction_type,
            session["user_id"],
            formatted_datetime,
        )

        # update/remove the stocks from user Portfolio
        portfolio_shares = shares_from_portfolio - shares

        if portfolio_shares > 0:
            db.execute("UPDATE portfolio SET share_quantity = ? WHERE user_id = ? AND symbol = ?",
                       portfolio_shares, session["user_id"], quote["symbol"])

        elif portfolio_shares == 0:
            db.execute("DELETE FROM portfolio WHERE user_id = ? AND symbol = ?",
                       session["user_id"], quote["symbol"])

        flash(
            f"Successfully sold {shares} shares of {quote["symbol"]} for {usd(rounded_total)}."
        )

        db.execute("COMMIT")

        return redirect("/")

    else:

        portfolio = db.execute(
            "SELECT symbol, share_quantity FROM portfolio WHERE user_id = ?", session["user_id"])
        return render_template("sell.html", portfolio=portfolio)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":
        return redirect("/password_change")

    else:
        users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        user = users[0]["username"]
        return render_template("profile.html", user=user)


@app.route("/password_change", methods=["GET", "POST"])
@login_required
def password_change():

    if request.method == "POST":
        users = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        # get the current hash of the user's password
        user_hash = users[0]["hash"]

        # store user inputs in variables
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # check for empty fields, wrong password or mismatch between new password and confirmation
        if not current_password or not new_password or not confirmation:
            return apology("You must fill all fields")

        elif not check_password_hash(user_hash, current_password):
            return apology("Invalid password", 403)

        elif new_password != confirmation:
            return apology("Please ensure that the new password and confirmation fields match.")

        # creates a new hash for the new password
        new_hash = generate_password_hash(new_password)

        # updates the hash on db, inserting the new one
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, session["user_id"])

        flash("Password changed with success!")

        return redirect("/")

    else:

        return render_template("password_change.html")
