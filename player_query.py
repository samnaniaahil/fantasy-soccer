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
from sqlalchemy import text, create_engine

engine = create_engine("sqlite:///soccer.db")
con = engine.connect()
results = con.execute(text("SELECT * FROM transfers"))[0]


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






