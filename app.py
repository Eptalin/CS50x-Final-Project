from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

#Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///rank.db")

# Tells client's browser not to cache response (always verifies with server) 
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
    # Generate data sets for line charts
    char_ids = db.execute("SELECT DISTINCT char_id FROM tracker WHERE user_id = ? ORDER BY game_id;", session["user_id"])
    data = {}

    for char_id in char_ids:
        char_id = char_id["char_id"]
        char_game = db.execute(
            "SELECT games.abbr AS game FROM games JOIN characters ON games.id = characters.game_id "
            "WHERE characters.id = ?;", char_id)[0]["game"]
        
        if char_game == "SF6":
            rank_data = db.execute(
                "SELECT points FROM tracker "
                "WHERE user_id = ? AND char_id = ?;", 
                session["user_id"], char_id
            )
            # Extract rank IDs and rank titles
            xValues = list(range(1, len(rank_data) + 1))
            yValues = [record["points"] for record in rank_data]
            yLabels = [record["points"] for record in rank_data]

        elif char_game == "GBVSR":
            # Fetch rank ID and rank title from database
            rank_data = db.execute(
                "SELECT rankings.id, rankings.rank FROM rankings "
                "JOIN tracker ON tracker.rank_id = rankings.id "
                "WHERE user_id = ? AND char_id = ?;", 
                session["user_id"], char_id
            )
            # Extract rank IDs and rank titles
            xValues = list(range(1, len(rank_data) + 1))
            yValues = [record["id"] for record in rank_data]
            yLabels = [record["rank"] for record in rank_data]

        char_name = db.execute(
            "SELECT character AS name FROM characters WHERE id = ?", char_id)[0]["name"]
        
        # Store data in dictionary
        data[char_id] = {"name": char_name, "game": char_game, "xValues": xValues, "yValues": yValues, "yLabels": yLabels}

    return render_template("index.html", data=data)    


@app.route("/add_character", methods=["GET", "POST"])
@login_required
def add_character():
    
    # POST: Add a character to the user's profile to begin tracking
    if request.method == "POST":
        # Turn user data into objects
        game = request.form.get("game")
        character = request.form.get("character")
        points = request.form.get("points")
        rank = request.form.get("rank")

        # Verify user input
        if not game or not character:
            return apology("Select Game and Character")
        
        # Query db to set the game_id and char_id
        game_id = db.execute("SELECT id FROM games WHERE name = ?;", game)[0]["id"]
        char_id = db.execute("SELECT id FROM characters WHERE character = ?;", character)[0]["id"]

        # Check whether user is already tracking the character
        char_check = db.execute("SELECT char_id FROM tracker WHERE user_id = ? AND char_id = ?;", session["user_id"], char_id)
        if len(char_check) != 0:
            return apology("Character is already being tracked")

        if game_id == 1 and not points:
            return apology("Enter LP")
        elif game_id == 2 and not rank:
            return apology("Enter rank")
        else:
            game_verification(game_id, char_id, points, rank)        
                
        return redirect("/")
    
    # GET: Populate game list and load form
    else:
        game_list = [
            game["name"]
            for game in db.execute(
                "SELECT name FROM games;"
            )
        ]
        return render_template("add_character.html", games=game_list)
    

# Populate the dropdown list of characters on the add_character route
@app.route("/get_characters")
def get_characters():
    game = request.args.get("game")
    characters = db.execute("SELECT character FROM characters JOIN games ON games.id = characters.game_id WHERE games.name = ?;", game)
    ranks = db.execute("SELECT rank FROM rankings JOIN games ON games.id = rankings.game_id WHERE games.name = ?;", game)
    return jsonify({"characters": characters, "ranks": ranks})


@app.route("/add_entry", methods=["GET", "POST"])
@login_required
def add_entry():
    
    if request.method == "POST":
        # Turn form data into objects
        character = request.form.get("character")
        points = request.form.get("points")
        rank = request.form.get("rank")
        
        # Verify user input
        if not character:
            return apology("Please select character")
        
        # Query db to set the game_id and char_id
        char_id = db.execute("SELECT id FROM characters WHERE character = ?;", character)[0]["id"]
        game_id = db.execute("SELECT game_id FROM tracker WHERE char_id = ?;", char_id)[0]["game_id"]
        
        # Verify game-specific data and input into database
        if game_id == 1 and not points:
            return apology("Enter LP")
        elif game_id == 2 and not rank:
            return apology("Enter rank")
        else:
            game_verification(game_id, char_id, points, rank)
        
        return redirect("/")
    
    else:
        # Send user's character.character and character.game to html using jinja
        characters = db.execute(
            "SELECT DISTINCT characters.character AS name, games.abbr AS game FROM characters "
            "JOIN games ON characters.game_id = games.id "
            "JOIN tracker ON characters.id = tracker.char_id "
            "WHERE tracker.user_id = ?;", session["user_id"])
        ranks_gbvsr = [
            i["rank"]
            for i in db.execute(
                "SELECT rank FROM rankings WHERE game_id = 2;"
            )
        ]
        return render_template("add_entry.html", characters=characters, ranksGBVSR=ranks_gbvsr)


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():

    if request.method == "POST":
        
        # Remove selected entry from database table
        entry_no = request.form.get("entry")
        db.execute("DELETE FROM tracker WHERE entry_no = ?;", entry_no)

        return redirect("/history")
    
    else:
        # Show all user entries by date
        rows = db.execute(
            "SELECT tracker.entry_no, games.name AS game, characters.character, rankings.rank, tracker.points "
            "FROM tracker "
            "JOIN games ON tracker.game_id = games.id "
            "JOIN characters ON characters.id = tracker.char_id "
            "LEFT JOIN rankings ON tracker.rank_id = rankings.id "
            "WHERE tracker.user_id = ? "
            "ORDER BY datetime DESC;", session["user_id"])

        return render_template("history.html", rows=rows)


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
            return apology("invalid username or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Turn user input into objects
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Verify user input
        if not username:
            return apology("Username required")
        if not password or password != confirmation:
            return apology("Passwords don't match")

        # Add new user to database and redirect to login page
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?);",
                       username, generate_password_hash(password))
            return redirect("/login")
        # If the username is taken, apologise
        except Exception as e:
            print(e)
            return apology("Username already taken")

    else:
        return render_template("register.html")
    

def game_verification(game_id, char_id, points, rank):
    # Verify game-specific input and insert into database
    
    # Street Fighter 6 #
    # Verify points
    if game_id == 1:
        if not points.isdigit():
            return apology("LP must be a number")
        points = int(points)
        if points < 0 or points > 25000:
            return apology("Invalid LP")

        db.execute("INSERT INTO tracker (user_id, game_id, char_id, points) VALUES (?, ?, ?, ?);", session["user_id"], game_id, char_id, points)
        return

    # Granblue Fantasy Versus: Rising #
    # Verify rank
    if game_id == 2:
        if not rank:
            return apology("Please enter rank")
        rank_id = db.execute("SELECT id FROM rankings WHERE rank = ?;", rank)[0]["id"]
        ranks = [i["id"] for i in db.execute("SELECT id FROM rankings WHERE game_id = ?", game_id)]
        if rank_id not in ranks:
            return apology("Invalid rank")
        
        db.execute("INSERT INTO tracker (user_id, game_id, char_id, rank_id) VALUES (?, ?, ?, ?);", session["user_id"], game_id, char_id, rank_id)
        return
