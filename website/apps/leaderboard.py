from dash import Input, Output, State

from app import app
from database import User


@app.callback(Output("leaderboard_modal", "is_open"), Input("leaderboard_open", "n_clicks"),
              Input("leaderboard_close", "n_clicks"), State("leaderboard_modal", "is_open"))
def toggle_leaderboard(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(Output("leaderboard_div", "hidden"), Input("state-user", "data"))
def hide_leaderboard_button(user_id):
    # only show leaderboard button if we know the user
    return user_id is None or user_id == ''


@app.callback(Output("leaderboard_text", "children"), Output("leaderboard_bar", "value"),
              Output("leaderboard_bar", "color"), Input("leaderboard_modal", "is_open"), State("state-user", "data"))
def toggle_leaderboard(is_open, user_id):
    leaderboard_text = 'No data available'
    leaderboard_bar = 0
    leaderboard_color = 'primary'
    if is_open and user_id is not None:
        user = User.query.filter_by(id=user_id).first()
        if user is not None:
            n_ratings_user = user.n_rated_hydrographs
            n_users = User.query.count()
            n_more_ratings_users = User.query.filter(User.n_rated_hydrographs > n_ratings_user) \
                .order_by(User.n_rated_hydrographs).count()
            leaderboard_bar = (n_users - n_more_ratings_users) / n_users * 100
            leaderboard_text = f'You rated {n_ratings_user} hydrographs, this puts you in ' \
                               f'leaderboard position {n_more_ratings_users + 1}.'
            if n_more_ratings_users == 0:
                leaderboard_color = 'success'  # easter egg for the leader ;)

    return leaderboard_text, leaderboard_bar, leaderboard_color
