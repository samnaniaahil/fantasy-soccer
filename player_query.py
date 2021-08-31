#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 14 12:38:02 2021

@author: aahilsamnani
"""

from unidecode import unidecode
import requests
import pandas as pd
import numpy as np
import sqlite3
import psycopg2


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

df = elements_df[["name", "web_name", "position", "team", "total_points", 
                  "points_per_game", "minutes", "goals_scored", "assists", 
                  "clean_sheets", "goals_conceded", "saves", "ict_index",
                  "form", "now_cost", "selected_by_percent", "news", "news_added", 
                  "yellow_cards", "red_cards"]]

player_info = df[["name", "web_name", "position", "team", "now_cost", 
                                       "form", "news", "news_added", "total_points"]]


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





