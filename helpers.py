from functools import wraps
from flask import redirect, session
import matplotlib.pyplot as plt
import pandas as pd
import requests


def create_player_dict(df_row):
    player_info = df_row[["name", "web_name", "position", "team", "now_cost", 
                          "form", "news", "news_added", "total_points"]]

    player_index = player_info.index[0]
    player_dict = player_info.to_dict(orient="index")[player_index]

    return player_dict


def create_player_graph(player_id):
    base_url = "https://fantasy.premierleague.com/api/"

    r = requests.get(base_url + "element-summary/" + str(player_id) + "/").json()
    player_df = pd.json_normalize(r["history"])

    if not player_df.empty:
        figure, ax = plt.subplots()

        for i in range(len(player_df.index)):
            # Calculate scores of each match played depending on if it the player played at home or away
            if player_df["was_home"].iloc[i] == True:
                score_diff = player_df["team_h_score"].iloc[i] - player_df["team_a_score"].iloc[i]
            else:
                score_diff = player_df["team_a_score"].iloc[i] - player_df["team_h_score"].iloc[i]
            # Label point on graph according to result of match
            if score_diff > 0:
                result = "won"
                l_color = "green"
            elif score_diff == 0:
                result = "drew"
                l_color = "#F6BE00"
            else:
                result = "lost"
                l_color = "red"
                
            plt.scatter(i+1, player_df["total_points"].iloc[i], label=result, color=l_color)

    # Manually create legend to avoid duplicate labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    
    # Restrict x-axis values to integers
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    ax.set_xlabel("Gameweek")
    ax.set_ylabel("Points")
    
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)  
    
    plt.title("Points History")
    
    plt.savefig("static/graphs/" + player_id + "_graph.png", dpi=300)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function