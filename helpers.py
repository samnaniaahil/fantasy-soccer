from functools import wraps
from flask import redirect, session


def create_player_dict(df_row):
    player_info = df_row[["name", "web_name", "position", "team", "now_cost", 
                          "form", "news", "news_added", "total_points"]]

    player_index = player_info.index[0]
    player_dict = player_info.to_dict(orient="index")[player_index]

    return player_dict


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function