import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
#return render_template("extra.html", name=rows)

import time
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = sqlite3.connect("finance.db", check_same_thread=False)

c = db.cursor()

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
    c.execute("SELECT * FROM stockss WHERE id = ? ", (session.get('user_id'), ))
    stockss_row = c.fetchall()

    c.execute("SELECT * FROM users WHERE id = ? ", (session.get('user_id'), ))
    user_row = c.fetchall()

    user = user_row[0][1]

    total = user_row[0][3]

    for row in stockss_row:
        total = total + row[3]

    return render_template('homepage.html', rows=stockss_row , cash=user_row[0][3] , total=total , user=user)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":

        symbol = request.form.get('symbol')
        qty = request.form.get('shares')

        if symbol == "":
            return apology("input is blank", 400)

        try:
            qty = int(qty)
        except ValueError:
            return apology("invalid quantity", 400)
        if not qty >=1  :
            return apology('Invalid Number of stocks', 400)

        if qty == "" :
            return apology("MISSING SHARES", 400)


        stock_quote = lookup(symbol)

        if not stock_quote:
            return apology("INVALID SYMBOL", 400)

        total_price = qty * (stock_quote['price'])

        session_saved_userid = session.get('user_id')

        c.execute("SELECT * FROM users WHERE id = ?", (session_saved_userid, ))
        rows = c.fetchall()

        total_money_of_user = rows[0][3]


        if total_price > total_money_of_user:
            return apology("You don't have enough money")

        c.execute("SELECT * FROM stockss WHERE id = ?", (session_saved_userid, ))
        rows = c.fetchall()

        #if already exist
        #return render_template("extra.html", name=rows[0][1], name2=rows[0][3], name3= (stock_quote['price']))



        for row in rows:

            if row[1] == symbol:
                db.execute("""
                    UPDATE stockss
                    SET qty = qty + ?,
                        total_value = total_value + ?,
                        last_price = ?
                    WHERE id = ?
                    AND symbol = ?
                """, (qty, total_price, stock_quote['price'], session_saved_userid, symbol))

                db.commit()
                break

        else:
            db.execute('INSERT INTO stockss (id, symbol, qty, last_price, total_value) values(?, ?, ?, ?, ?)'
                , (session_saved_userid, symbol, qty, stock_quote['price'], qty*stock_quote['price']))
            db.commit()

        update_money(total_price)
        update_history(symbol, qty, stock_quote['price'])

        return redirect('/')

    return render_template('buy.html')


@app.route("/history")
@login_required
def history():

    c.execute("SELECT * FROM history WHERE id = ?", (session.get('user_id'), ))
    rows= c.fetchall()

    #return render_template("extra.html", name=rows)

    return render_template("history.html", rows=reversed(rows))


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
        c.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),))# already has quotes

        rows = c.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        session['username'] = rows[0][1]

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

    if request.method == "POST":

        symbol = request.form.get("symbol")

        if symbol == "":
            return apology("input is blank", 400)

        stock_quote = lookup(symbol)


        if not stock_quote:
            return apology("INVALID SYMBOL", 400)
        else:
            return render_template("show_price.html", symbol=stock_quote['symbol'], price=stock_quote['price'])

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        c.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        rows = c.fetchall()

        if rows != []:
            return apology('Username Taken', 400)

        if not request.form.get('username') :
            return apology('Must provide Username', 400)

        elif not request.form.get('password') or not request.form.get('confirmation'):
            return apology('Must provide Password', 400)

        elif (request.form.get('confirmation') != request.form.get('password')):
            return apology('Password do not match', 400)

        hashed_password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256', salt_length=8)

        db.execute('INSERT INTO users (username, hash) values(?, ?)', (request.form.get('username'), hashed_password))
        db.commit()

        return redirect('/login')
    else:
        return render_template("register.html")

#chatpgt copied fn
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    c.execute("SELECT symbol, qty FROM stockss WHERE id = ?", (session.get('user_id'), ))
    stocks = c.fetchall()

    if request.method == "POST":
        symbol = request.form.get('symbol')
        qty = request.form.get('shares')

        if not symbol:
            return apology("Must provide symbol", 400)

        try:
            qty = int(qty)
        except ValueError:
            return apology("Invalid quantity", 400)

        if qty <= 0:
            return apology("Invalid Number of stocks", 400)

        # Get the user's stock holdings for the selected symbol
        c.execute("SELECT qty FROM stockss WHERE id = ? AND symbol = ?", (session.get('user_id'), symbol))
        stock_row = c.fetchone()

        if not stock_row:
            return apology("You don't own that stock", 400)

        owned_qty = stock_row[0]

        if qty > owned_qty:
            return apology("You don't have that many shares", 400)

        # Calculate the total value of the sale
        stock_quote = lookup(symbol)
        total_price = qty * stock_quote['price']

        if qty < owned_qty:
            # Update the stock quantity
            db.execute("""
                UPDATE stockss
                SET qty = qty - ?,
                    total_value = total_value - ?
                WHERE id = ? AND symbol = ?
            """, (qty, total_price, session.get('user_id'), symbol))

        else:
            # If selling all shares, delete the row
            db.execute("DELETE FROM stockss WHERE id = ? AND symbol = ?", (session.get('user_id'), symbol))

        # Update user's cash balance
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", (total_price, session.get('user_id')))
        db.commit()

        update_history(symbol, -qty, stock_quote['price'])

        return redirect('/')

    return render_template('sell.html', stocks=stocks)


def update_money(total_price):

    session_saved_userid = session.get('user_id')

    db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", (total_price, session_saved_userid))
    db.commit()

    return




def update_history(symbol, qty, price):

    db.execute("""INSERT INTO history
                (id, symbol, qty, price)
                VALUES(?, ?, ?, ?)""",
                (session.get('user_id'), symbol, qty, price))
    db.commit()
    return


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)