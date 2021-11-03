import bcrypt
from collections import Counter
from flask.helpers import get_flashed_messages
from unidecode import unidecode
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_login import login_required
from markupsafe import Markup
import pandas as pd
import re
import requests
import sqlite3
from tempfile import mkdtemp
from unidecode import unidecode

import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt

from helpers import create_player_dict, create_player_graph, login_required


MAX_PLAYERS_IN_TEAM = 11
BUDGET = 800

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = "soccer.db"

# Data pre-processing
# Data retreived from: https://fantasy.premierleague.com/api/bootstrap-static/
# -------------------
r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
json = r.json()

elements_df = pd.DataFrame(json["elements"])
elements_types_df = pd.DataFrame(json["element_types"])
teams_df = pd.DataFrame(json["teams"])

elements_df["position"] = elements_df.element_type.map(elements_types_df.set_index("id").singular_name)
elements_df["team"] = elements_df.team.map(teams_df.set_index("id").name)

# Merge players' first and last names into one column
elements_df["name"] = elements_df["first_name"] + " " + elements_df["second_name"]
elements_df = elements_df.drop(columns=["first_name", "second_name"])

df = elements_df[["name", "web_name", "position", "team", "now_cost", "form", 
                  "news", "news_added", "total_points", "points_per_game", 
                  "goals_scored", "assists", "clean_sheets", "goals_conceded", 
                  "saves", "ict_index","selected_by_percent", "yellow_cards", "red_cards"]]

df = df.sort_values("name")



# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_player():
    if request.method == "POST":
        # Connect to database
        con = sqlite3.connect(db)
        cur = con.cursor()

        # Check if user can afford player
        player_cost = cur.execute("SELECT now_cost FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],)).fetchall()[0][0]
        user_money = int(cur.execute("SELECT money FROM users WHERE id = ?", (session["user_id"],)).fetchall()[0][0])
        if player_cost > user_money:
            # Commit changes and close database connection
            con.commit()
            con.close()

            flash("Not enough money. Short £" + str(player_cost - user_money) + ".")
            return redirect("/team")

        # Get number of players in user's team
        cur.execute("SELECT COUNT(id) FROM team WHERE user_id = ?", (session["user_id"],))
        player_count = cur.fetchone()[0]

        if player_count < MAX_PLAYERS_IN_TEAM:
            # Add player
            cur.execute("INSERT INTO team SELECT NULL, user_id, name, web_name, position, team, now_cost, form, points FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],))
            # Record additonal info about player's addition in the "transfers" table
            transfer_type = "In"
            cur.execute("INSERT INTO transfers SELECT NULL, user_id, name, position, team, now_cost, DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME'), ?"
                        "FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (transfer_type, session["user_id"]))
            # Subtract player's cost from the user's budget
            cur.execute("UPDATE users SET money = money - ? WHERE id = ?", (player_cost, session["user_id"]))

            con.commit()
            con.close()
            flash("Player added.")
            return redirect("/team")
        else:
            con.commit()
            con.close()
            flash("Team full (11/11 players).")
            return redirect("/team")
    
    else:
        return redirect("/players")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete_player():
    if request.method == "POST":
        con = sqlite3.connect(db)
        cur = con.cursor()

        # Get player info from user's most recent search 
        player = str(cur.execute("SELECT name FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],)).fetchall()[0][0])
        # Delete player
        cur.execute("DELETE FROM team WHERE name = ? AND user_id = ?", (player, session["user_id"]))
        # Record additional info about player deletion in the "transfers" table
        transfer_type = "Out"
        cur.execute("INSERT INTO transfers SELECT NULL, user_id, name, position, team, now_cost, DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME'), ? FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                    (transfer_type, session["user_id"]))
        
        # Add player's cost back into the user's budget
        player_cost = cur.execute("SELECT now_cost FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],)).fetchall()[0][0]
        cur.execute("UPDATE users SET money = money + ? WHERE id = ?", (player_cost, session["user_id"]))

        con.commit()
        con.close()
        flash("Player deleted.")
        return redirect("/team")
    
    else:
        return redirect("/players")


@app.route("/graph")
@login_required
def display_graph():
    column = request.args.get("column")
    
    team_df = df[["team", column]]
    team_df[column] = pd.to_numeric(team_df[column])
    team_df = team_df.groupby("team").mean()

    figure, ax = plt.subplots()

    num_teams = len(team_df.index)
    for i in range(num_teams):
        team = teams_df["name"].iloc[i]

        ax.bar(team, team_df[column].iloc[i], label=team)

    ax.set_xticks([i for i in range(num_teams)])
    ax.set_xticklabels(teams_df["name"].unique().tolist())
    ax.set_xlabel("Team")
    plt.setp(ax.get_xticklabels(), rotation=90)

    ax.set_ylabel(column)

    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    figure.subplots_adjust(bottom=0.4)

    plt.savefig("static/graphs/" + column + "_graph.png", dpi=300)

    return render_template("graph.html", column=column)


@app.route("/graphs", methods=["GET", "POST"])
@login_required
def graphs():
    
    if request.method == "POST":
        column = request.form.get("column")
        if not column:
            return redirect("/graphs")

        return redirect(url_for("display_graph", column=column))
    
    else:
        # Remove all non-numeric columns
        new_df = df
        for column in new_df:
            try:
                pd.to_numeric(new_df[column])
            except ValueError:
                new_df = new_df.drop(columns=[column])

        df_cols = new_df.columns.values

        return render_template("graphs.html", df_cols=df_cols)


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    con = sqlite3.connect(db)
    cur = con.cursor()
    if request.method == "POST":
        # Clear user's transfers from database if they click "Clear Transfer History"
        cur.execute("DELETE FROM transfers WHERE user_id = ?", (session["user_id"],))
        con.commit()
        con.close()
        return redirect("/history")

    else:   
        # Show history of transfers (i.e additions and deletions from team)
        transfers = cur.execute("SELECT * FROM transfers WHERE user_id = ?", (session["user_id"],)).fetchall()
        con.commit()
        con.close()
        return render_template("history.html", transfers=transfers)


@app.route("/league")
@login_required
def league():
    con = sqlite3.connect(db)
    cur = con.cursor()

    # Get info about each user sorted by number of points to display as a leaderboard
    users = cur.execute("SELECT users.username, SUM(team.points), users.money FROM users JOIN team WHERE users.id = team.user_id GROUP BY users.id ORDER BY SUM(team.points) DESC").fetchall()

    con.commit()
    con.close()
    
    return render_template("league.html", users=users)    


@app.route("/login", methods=["GET", "POST"])
def login():
    # Display any login error messages before session is cleared
    get_flashed_messages()

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        # bcrypt (like other hashing algorithms) only accepts byte arrays
        password = request.form.get("password").encode("utf-8")

        if not username:
            flash("Please enter a username.")
            return redirect("/login")
        if not password:
            flash("Please enter a password.")
            return redirect("/login")

        con = sqlite3.connect(db)
        cur = con.cursor()

        user_row = cur.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()

        # user_rows[0][2] is the username's corresponding hashed password
        if len(user_row) == 0 or not bcrypt.checkpw(password, user_row[0][2]):
            con.commit()
            con.close()
            flash("Invalid username and/or password.")
            return redirect("/login")
        
        # user_rows[0][0] is the user's id in a sqlite table
        session["user_id"] = user_row[0][0]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    
    return redirect("/login")


@app.route("/player")
@login_required
def display_player():
    player = request.args.get("player")
    player_df_row = df.loc[df["name"] == player]

    if len(player_df_row) == 0:
        return redirect("/players")
    else:
        player_dict = create_player_dict(player_df_row)

    # Get player code to retreive image of player from soccer API in player.html
    player_dict["code"] = elements_df["code"].loc[elements_df["name"] == player].values[0]

    # Get player id to identify corresponding player graph image from disk
    player_dict["id"] = elements_df["id"].loc[elements_df["name"] == player].values[0]

    if player_dict["news"]:
        player_dict["news"] = player_dict["news"]
        # Exctract news date from timestamp
        player_dict["news_added"] = player_dict["news_added"][0:10]

    player_stats = player_df_row.iloc[:, 8:]
    player_stats.columns = player_stats.columns.str.title().str.replace("_", " ")
    player_stats_table = Markup(player_stats.to_html(index=False))

    con = sqlite3.connect(db)
    cur = con.cursor()

    # Check if player is in team to decide to display either an "add" or "delete" player button in player.html
    player_row = cur.execute("SELECT * FROM team WHERE name = ? AND user_id = ?", (player_dict["name"], session["user_id"])).fetchall()
    if len(player_row) == 1:
        player_in_team = True
    else:
        player_in_team = False

    con.commit()
    con.close()

    return render_template("player.html", player_dict=player_dict, player_stats_table=player_stats_table, 
                           player_in_team=player_in_team)


@app.route("/players", methods=["GET", "POST"])
@login_required
def players():
    if request.method == "POST":
        # Normalize string, unidecode removes accents
        player_input = unidecode(request.form.get("player").strip().lower())
        if not player_input:
            return redirect("/players")
        # Remove all accents from player name stored in DataFrame
        player_df_row = df.loc[df["name"].apply(unidecode).str.lower().str.contains(player_input)]

        if len(player_df_row) == 0:
            return redirect("/players")
        else:
            player_dict = create_player_dict(player_df_row)
            
        con = sqlite3.connect(db)
        cur = con.cursor()
        
        cur.execute("INSERT INTO searches (user_id, name, web_name, position, team, now_cost, form, points) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", 
                    (session["user_id"], player_dict["name"], player_dict["web_name"], player_dict["position"], player_dict["team"],
                        player_dict["now_cost"], player_dict["form"], player_dict["total_points"]))

        con.commit()
        con.close()
        
        create_player_graph(str(elements_df["id"].loc[elements_df["name"] == player_dict["name"]].values[0]))

        player = str(player_df_row["name"].iloc[0])
        return redirect(url_for("display_player", player=player))

    else:
        players_df = df[["name", "position", "team"]]
        return render_template("players.html", players_df=players_df)


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_confirmation = request.form.get("confirmation")

        if not username:
            flash("Please enter a username.")
            return redirect("/register")
        elif len(username) < 6:
            flash("Username must be at least 6 characters.")
            return redirect("/register")
        else:
            con = sqlite3.connect(db)
            cur = con.cursor()
            usernames = cur.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchall()
            if len(usernames) > 0:
                con.commit()
                con.close()
                flash("Username already taken.")
                return redirect("/register")
            con.commit()
            con.close()

        password_error = True
        if not password:
            flash("Please enter a password.")
        elif not password_confirmation:
            flash("Please confirm password.")
        elif password != password_confirmation:
            flash("Passwords do not match.")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.")
        elif re.search("[0-9]", password) is None:
            flash("Password must contain a number.")
        elif re.search("[a-zA-Z]", password) is None:
            flash("Password must contain a letter.")
        elif re.search("[a-z]", password) is None:
            flash("Password must contain a lowercase letter.")
        elif re.search("[A-Z]", password) is None:
            flash("Password must contain an uppercase letter.")
        elif re.search("^(?=.*?[!@#$%^&_+=()`~:;-])", password) is None:
            flash("Password must contain a special character.")
        else:
            password_error = False

        if password_error:
            return redirect("/register")

        # bcrypt (like other hashing algorithms) only accepts byte arrays
        password = password.encode("utf-8")
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        con = sqlite3.connect(db)
        cur = con.cursor()

        cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?)", (username, hashed_password, BUDGET))

        con.commit()
        con.close()

        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/team")
@login_required
def team():
    con = sqlite3.connect(db)
    cur = con.cursor()
    players = cur.execute("SELECT name, position, points FROM team WHERE user_id = ? ORDER BY position = ? DESC, position = ? DESC, position = ? DESC, position = ? DESC",
                          (session["user_id"], "Goalkeeper", "Defender", "Midfielder", "Forward")).fetchall()

    player_codes = []
    positions = []        
    for player in players:
        player_codes.append(list(elements_df["code"].loc[elements_df["name"] == player[0]]))
        positions.append(player[1])

    # Get user's total points by adding number of points for each player in their team
    if players: 
        total_points = cur.execute("SELECT SUM(points) FROM team WHERE user_id = ?", (session["user_id"],)).fetchone()[0]
        if not total_points:
            total_points = 0
        else:
            total_points = int(total_points)
    else:
        total_points = 0

    # Get number of players in each position
    position_dict = Counter(positions)
    
    money = cur.execute("SELECT money FROM users WHERE id = ?", (session["user_id"],)).fetchone()[0]

    con.commit()
    con.close()

    position_types = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
    return render_template("team.html", players=players, position_dict=position_dict, position_types=position_types, 
                           player_codes=player_codes, total_points=total_points, money=money)
