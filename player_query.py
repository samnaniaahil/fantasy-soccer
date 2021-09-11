#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 14 12:38:02 2021

@author: aahilsamnani
"""

import bokeh
from unidecode import unidecode
import requests
import matplotlib.pyplot as plt
import mpld3
from mpld3 import plugins
import pandas as pd
import numpy as np
import sqlite3
import psycopg2
import random


url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
r = requests.get(url)
json = r.json()
json.keys()

elements_df = pd.DataFrame(json['elements'])
elements_types_df = pd.DataFrame(json['element_types'])
teams_df = pd.DataFrame(json['teams'])

elements_df['position'] = elements_df.element_type.map(elements_types_df.set_index('id').singular_name)
elements_df['team'] = elements_df.team.map(teams_df.set_index('id').name)

elements_df["name"] = elements_df["first_name"] + " " + elements_df["second_name"]
elements_df = elements_df.drop(columns=["first_name", "second_name"])



df = elements_df[["name", "web_name", "position", "team", "now_cost", "form", 
                  "news", "news_added", "total_points", "points_per_game", 
                  "goals_scored", "assists", "clean_sheets", "goals_conceded", 
                  "saves", "ict_index","selected_by_percent", "yellow_cards", "red_cards"]]



base_url = "https://fantasy.premierleague.com/api/"
player_id = 558
r2 = requests.get(base_url + "element-summary/" + str(player_id) + "/").json()
player_df = pd.json_normalize(r2["history"])

if not player_df.empty:
    figure, ax = plt.subplots()
    
    
    plt.style.use("ggplot")
    for i in range(len(player_df.index)):
        if player_df["was_home"].iloc[i] == True:
            score_diff = player_df["team_h_score"].iloc[i] - player_df["team_a_score"].iloc[i]
        else:
            score_diff = player_df["team_a_score"].iloc[i] - player_df["team_h_score"].iloc[i]
            
        if score_diff > 0:
            result = "won"
            l_color = "green"
        elif score_diff == 0:
            result = "drew"
            l_color = "yellow"
        else:
            result = "lost"
            l_color = "red"
        
        random_number = random.randint(0,16777215)
        hex_number = str(hex(random_number))
        hex_number ='#'+ hex_number[2:]
        plt.scatter(i+1, player_df["total_points"].iloc[i], 
                   label=result, color=hex_number)
    

    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
     
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_xlabel("Gameweek")
    
    ax.set_ylabel("Points")
    
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)   


"""column = "form"
figure, ax = plt.subplots()
team_df = df[["team", column]].groupby("team").mean()"""

"""for i in range(20):
    team = teams_df["name"].tolist()[i]
    ax.bar(team, team_df[column].tolist()[i], label=team)
ax.set_xticks([i for i in range(20)])
ax.set_xticklabels(teams_df["name"].unique().tolist())
ax.set_xlabel("Team")
ax.set_ylabel(column)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
plt.title("Average " + column + " by Team")
plt.setp(ax.get_xticklabels(), rotation=90)
figure.subplots_adjust(bottom=0.2)
plt.setp(ax.get_xticklabels(), rotation=90)
plt.savefig("static/" + column + "_graph.png", dpi=300)"""





"""
ax.bar(df["team"].unique().tolist(), teams_df["total_points"].tolist())
plt.setp(ax.get_xticklabels(), rotation=90)
"""

"""if request.method == "POST":
        # Normalize string, unidecode removes accents
        player_input = unidecode(request.form.get("player").strip().lower())
        if not player_input:
            return redirect("/players")
        # Remove all accents from player name stored in DataFrame
        player_df_row = df.loc[df["name"].apply(unidecode).str.lower().str.contains(player_input)]

        if len(player_df_row) == 1:
            player = player_df_row["name"].iloc[0]
            player_info = player_df_row[["name", "web_name", "position", "team", "now_cost", 
                                       "form", "news", "news_added", "total_points"]]
            player_stats = player_df_row.iloc[:, 8:]

            player_index = player_info.index[0]
            player_dict = player_info.to_dict(orient="index")[player_index]

            # Get player code to retreive image of player from soccer API in player.html
            player_dict["code"] = list(elements_df["code"].loc[elements_df["name"] == player])[0]

            if player_dict["news"]:
                player_dict["news"] = player_dict["news"]
                # Exctract news date from timestamp
                player_dict["news_added"] = player_dict["news_added"][0:10]

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
            cur.execute("INSERT INTO searches (user_id, name, web_name, position, team, now_cost, form, points) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", 
                        (session["user_id"], player_dict["name"], player_dict["web_name"], player_dict["position"], player_dict["team"],
                         player_dict["now_cost"], player_dict["form"], player_dict["total_points"]))
            con.commit()
            con.close()
            
            # Render another page to show player profile
            return render_template("player.html", player_dict=player_dict, player_stats_table=player_stats_table,
                                   player_in_team=player_in_team)

        return redirect("/players")

    else:
        players_df = df[["name", "position", "team"]]
        return render_template("players.html", players_df=players_df)"""





