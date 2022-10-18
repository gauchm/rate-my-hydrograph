import logging

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
from flask import send_from_directory

# need to import server so we can expose it to uwsgi
from app import app, db, server
# "unused" imports are necessary to load the callbacks from these modules
from apps import rate, questionnaire, instructions, leaderboard
from database import User  # pylint: disable=unused-import

LOGGER = logging.getLogger(__name__)

LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

base_layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Navbar(
        dbc.Container([
            dbc.Row(
                [
                    dbc.Col(dbc.NavbarBrand("Rate My Hydrograph")),
                ],
                align="center",
                className="g-0 me-auto",
            ),
            html.Div(  # need a div around this button to make it hideable
                id="leaderboard_div",
                hidden=True,
                children=dbc.Button("Leaderboard", id="leaderboard_open", outline=True, color="light",
                                    className="me-1"),
            ),
            dbc.Button("Help", id="help_open", outline=True, color="light"),
        ]),
        color="dark",
        dark=True,
        className="mb-2",
    ),
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Help")),
            dbc.ModalBody(children=[instructions.instructions]),
            dbc.ModalFooter(dbc.Button("Close", id="help_close", className="ms-auto", n_clicks=0)),
        ],
        id="help_modal",
        is_open=False,
        size="xl",
    ),
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Leaderboard")),
            dbc.ModalBody(children=[
                html.P(id="leaderboard_text", children="No data available"),
                dbc.Progress(id="leaderboard_bar", value=0, color="primary", className="mb-3"),
            ]),
            dbc.ModalFooter(dbc.Button("Close", id="leaderboard_close", className="ms-auto", n_clicks=0)),
        ],
        id="leaderboard_modal",
        is_open=False,
        size="xl",
    ),
    dbc.Container([
        dbc.Alert(
            "",
            id="alert-error",
            color="danger",
            is_open=False,
            dismissable=True,
        ),
        html.Div(id='page-content')
    ]),
    dcc.Store(id='state-user', storage_type='local'),  # remember user id in localStorage
])

start_page = dbc.Card(
    dbc.CardBody([
        html.H1('Welcome to Rate My Hydrograph'), instructions.instructions,
        html.Div("Before we start, we'd like to ask you a few demographic questions.", className='mt-4'),
        dbc.Nav(dbc.NavItem(dbc.NavLink('Start questionnaire', href='/questionnaire', active=True, external_link=True)),
                pills=True,
                className='mt-2')
    ]))

welcome_back_page = dbc.Card(
    dbc.CardBody([
        html.H2("Welcome back to Rate My Hydrograph!"),
        instructions.instructions,
        html.P("Let's continue rating hydrographs!", className='mt-4'),
        dbc.Nav(dbc.NavItem(dbc.NavLink('Continue rating', href='/rate', active=True, external_link=True)),
                pills=True,
                className='mt-2'),
    ]))

app.layout = base_layout


@app.callback(Output("help_modal", "is_open"), Input("help_open", "n_clicks"), Input("help_close", "n_clicks"),
              State("help_modal", "is_open"))
def toggle_help(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(Output('page-content', 'children'), Input('url', 'pathname'), State('state-user', 'data'))
def display_page(pathname: str, user_id: str):
    if user_id is not None and user_id != '':
        user = User.query.filter_by(id=user_id).first()
        if user is not None:
            if pathname == '/rate':
                return rate.rating_page
            return welcome_back_page
        LOGGER.warning(f'Encountered unknown user {user_id}')
    if pathname == '/questionnaire':
        return questionnaire.questionnaire_page
    return start_page


@app.server.route('/robots.txt')
def robots():
    return send_from_directory(app.config['assets_folder'], 'robots.txt')


if __name__ == '__main__':
    db.create_all()
    app.run_server(debug=True)
