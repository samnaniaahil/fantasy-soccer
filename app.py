import bcrypt
from collections import Counter
from flask.helpers import get_flashed_messages
from unidecode import unidecode
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_login import login_required
from markupsafe import Markup
import os
import pandas as pd
import re
import requests
import sqlite3
from tempfile import mkdtemp
from unidecode import unidecode

from helpers import login_required

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

db = os.environ.get("DATABASE_URL")

# Data pre-processing
# -------------------
# Data retreived from: https://fantasy.premierleague.com/api/bootstrap-static/
# Special thanks to David Allen: 
# (https://towardsdatascience.com/fantasy-premier-league-value-analysis-python-tutorial-using-the-fpl-api-8031edfe9910#8ef2)
# -------------------
url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
r = requests.get(url)
json = r.json()
json.keys()

elements_df = pd.DataFrame(json['elements'])
elements_types_df = pd.DataFrame(json['element_types'])
teams_df = pd.DataFrame(json['teams'])

elements_df['position'] = elements_df.element_type.map(elements_types_df.set_index('id').singular_name)
elements_df['team'] = elements_df.team.map(teams_df.set_index('id').name)

# Merge players' first and last names into one column
elements_df["name"] = elements_df["first_name"] + " " + elements_df["second_name"]
elements_df = elements_df.drop(columns=["first_name", "second_name"])

df = elements_df[["name", "web_name", "position", "team", "now_cost", "form", 
                  "news", "news_added", "total_points", "points_per_game", 
                  "goals_scored", "assists", "clean_sheets", "goals_conceded", 
                  "saves", "ict_index","selected_by_percent", "yellow_cards", "red_cards"]]

df = df.sort_values("name")

#team logos from: https://www.transfermarkt.us/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=2020

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
def add_player():
    con = sqlite3.connect(db, uri=True)
    cur = con.cursor()
    # Get number of players in user's team
    cur.execute("SELECT COUNT(id) FROM team WHERE user_id = ?", (session["user_id"],))
    player_count = cur.fetchone()[0]

    #Check if user can afford player
    player_cost = cur.execute("SELECT now_cost FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],)).fetchall()[0][0]
    user_money = int(cur.execute("SELECT money FROM users WHERE id = ?", (session["user_id"],)).fetchall()[0][0])
    if player_cost > user_money:
        con.commit()
        con.close()
        flash("Not enough money. Short £" + str(player_cost - user_money) + ".")
        return redirect("/team")

    if player_count < MAX_PLAYERS_IN_TEAM:
        cur.execute("INSERT INTO team SELECT NULL, user_id, name, web_name, position, team, now_cost, form, points FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],))
        transfer_type = "In"
        cur.execute("INSERT INTO transfers SELECT NULL, user_id, name, position, team, now_cost, DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME'), ?"
                    "FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (transfer_type, session["user_id"]))

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

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete_player():
    con = sqlite3.connect(db, uri=True)
    cur = con.cursor()
    player = str(cur.execute("SELECT name FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],)).fetchall()[0][0])
    player_rows = cur.execute("SELECT name FROM team WHERE name = ? AND user_id = ?", (player, session["user_id"])).fetchall()
    if len(player_rows) == 0:
        con.commit()
        con.close()
        flash("Player not in team.")
        return redirect("/team")
    
    cur.execute("DELETE FROM team WHERE name = ? AND user_id = ?", (player, session["user_id"]))
    transfer_type = "Out"
    cur.execute("INSERT INTO transfers SELECT NULL, user_id, name, position, team, now_cost, DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME'), ? FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (transfer_type, session["user_id"]))
    
    player_cost = cur.execute("SELECT now_cost FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session["user_id"],)).fetchall()[0][0]
    cur.execute("UPDATE users SET money = money + ? WHERE id = ?", (player_cost, session["user_id"]))

    con.commit()
    con.close()
    flash("Player deleted.")
    return redirect("/team")


@app.route("/league")
@login_required
def league():
    con = sqlite3.connect(db, uri=True)
    cur = con.cursor()

    users = cur.execute("SELECT users.username, SUM(team.points), users.money FROM users JOIN team WHERE users.id = team.user_id GROUP BY users.id ORDER BY SUM(team.points) DESC").fetchall()

    con.commit()
    con.close()
    return render_template("league.html", users=users)    


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    con = sqlite3.connect(db, uri=True)
    cur = con.cursor()
    if request.method == "POST":
        cur.execute("DELETE FROM transfers WHERE user_id = ?", (session["user_id"],))
        con.commit()
        con.close()
        return render_template("history.html")
    else:   
        # Show history of transfers (i.e additions and deletions from team)
        transfers = cur.execute("SELECT * FROM transfers WHERE user_id = ?", (session["user_id"],)).fetchall()
        con.commit()
        con.close()
        return render_template("history.html", transfers=transfers)


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password").encode("utf-8")

        if not username:
            return render_template("login.html", error_msg="Please enter a username.")
        if not password:
            return render_template("login.html", error_msg="Please enter a password.")

        con = sqlite3.connect(db, uri=True)
        cur = con.cursor()
        user_rows = cur.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()

        #user_rows[0][2] is the username's corresponding hashed password
        if len(user_rows) == 0 or not bcrypt.checkpw(password, user_rows[0][2]):
            con.commit()
            con.close()
            return render_template("login.html", error_msg="Invalid username and/or password.")
        
        # user_rows[0][0] is the user's id in a sqlite table
        session["user_id"] = user_rows[0][0]

        return redirect("/")

    else:
        return render_template("login.html", error_msg="")



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/players", methods=["GET", "POST"])
@login_required
def players():
    if request.method == "POST":
        # Normalize string, unidecode removes accents
        player_input = unidecode(request.form.get("player").strip().lower())
        if not player_input:
            return redirect("/players")

        # Remove all accents from player name when comparing to user's input
        player_rows = df.loc[df["name"].apply(unidecode).str.lower().str.contains(player_input)]

        if len(player_rows) == 1:
            player = player_rows["name"].iloc[0]
            # Get info and stats of player
            player_info = player_rows[["name", "web_name", "position", "team", "now_cost", 
                                       "form", "news", "news_added", "total_points"]]
            player_index = player_info.index[0]
            player_info = player_info.to_dict(orient="index")[player_index]
            player_code = list(elements_df["code"].loc[elements_df["name"] == player])[0]
            player_stats = player_rows.iloc[:, 8:]

            # Get player news and date news was added from timestamp
            player_news, player_news_date = "", ""
            if player_info["news"]:
                player_news = str(player_info["news"])
                player_news_date = player_info["news_added"][0:10]

            # Convert data frame to HTML table
            player_stats.columns = player_stats.columns.str.title().str.replace("_", " ")
            player_stats_table = Markup(player_stats.to_html(index=False))

            con = sqlite3.connect(db, uri=True)
            cur = con.cursor()

            # Check if player is in team
            player_rows = cur.execute("SELECT * FROM team WHERE name = ? AND user_id = ?", (player_info["name"], session["user_id"])).fetchall()
            if len(player_rows) == 1:
                player_in_team = True
            else:
                 player_in_team = False

            cur.execute("INSERT INTO searches (user_id, name, web_name, position, team, now_cost, form, points) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", 
                        (session["user_id"], player_info["name"], player_info["web_name"], player_info["position"], player_info["team"],
                         player_info["now_cost"], player_info["form"], player_info["total_points"]))

            con.commit()
            con.close()
            
            return render_template("player.html", player_info=player_info, player_code=player_code,
                                   player_stats_table=player_stats_table, player_index=player_index,
                                   player_news=player_news, player_news_date=player_news_date, 
                                   player_in_team=player_in_team)

        return redirect("/players")

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
        elif len(username) < 6:
            flash("Username must be at least 6 characters.")
        elif not password:
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

        messages = get_flashed_messages()
        if messages:
            return render_template("register.html")

        password = password.encode("utf-8")
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        con = sqlite3.connect(db, uri=True)
        cur = con.cursor()

        usernames = cur.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchall()
        if len(usernames) > 0:
                return render_template("register.html", error_msg="Username already taken.")

        cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?)", (username, hashed_password, BUDGET))

        con.commit()
        con.close()
        return redirect("/login")

    else:
        return render_template("register.html")



@app.route("/team")
@login_required
def team():
    con = sqlite3.connect(db, uri=True)
    cur = con.cursor()
    players = cur.execute("SELECT name, position, points FROM team WHERE user_id = ? ORDER BY position = ? DESC, position = ? DESC, position = ? DESC, position = ? DESC",
                          (session["user_id"], "Goalkeeper", "Defender", "Midfielder", "Forward")).fetchall()
    player_codes = []
    positions = []
    for player in players:
        player_codes.append(list(elements_df["code"].loc[elements_df["name"] == player[0]]))
        positions.append(player[1])

    if players: 
        total_points = cur.execute("SELECT SUM(points) FROM team WHERE user_id = ?", (session["user_id"],)).fetchone()[0]
        if not total_points:
            total_points = 0
        else:
            total_points = int(total_points)
    else:
        total_points = 0
    position_dict = Counter(positions)
    position_types = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
    
    money = cur.execute("SELECT money FROM users WHERE id = ?", (session["user_id"],)).fetchone()[0]
    con.commit()
    con.close()
    return render_template("team.html", players=players, position_dict=position_dict, position_types=position_types, 
                           player_codes=player_codes, total_points=total_points, money=money)


