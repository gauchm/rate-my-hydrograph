import hashlib
import logging
import time
from pathlib import Path

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import xarray
import dash
from dash import Input, Output, State, dcc, html
from sqlalchemy import exc

from app import SALT, app, db
from database import Rating, User

N_YEARS = 1

OBS_COLOR = 'black'
MODEL_ONE_COLOR = 'orange'
MODEL_TWO_COLOR = '#a500ff'

Q_VAR_NAME = "Q"
BASIN_VAR_NAME = "station_id"
DATE_VAR_NAME = "time"

LOGGER = logging.getLogger(__name__)


def load_data(base_dir: Path) -> xarray.Dataset:
    obs_file = base_dir / 'all_gauges.nc'
    if not obs_file.exists():
        raise ValueError(f'Observations netCDF file not found at {obs_file}')
    # netcdfs only have a numeric dimension "nstations" that maps to the station_id variable.
    # for easier processing, we directly make the station_id the dimension.
    obs = xarray.load_dataset(obs_file).swap_dims({'nstations': BASIN_VAR_NAME})

    # load hydrographs from individual models
    hydrographs = {Q_VAR_NAME: obs[Q_VAR_NAME]}
    model_dirs = [d for d in base_dir.glob('model/*') if d.is_dir()]
    for model_dir in model_dirs:
        model_name = model_dir.name
        model_nc = list(model_dir.glob('*.nc'))
        if len(model_nc) != 1:
            LOGGER.info(f'Found {len(model_nc)} files for model {model_name}')
            if len(model_nc) == 0:
                continue
        hydrographs[model_name] = xarray.open_dataset(model_nc[0]).swap_dims({'nstations': BASIN_VAR_NAME})[Q_VAR_NAME]

    hydrograph_xr = xarray.concat(hydrographs.values(), dim='model')
    hydrograph_xr['model'] = list(hydrographs.keys())
    return hydrograph_xr


OBJECTIVES = ['objective_2/great-lakes/validation-temporal', 'objective_1/great-lakes/validation-temporal']
XR = {}
YEARS = {}
BASINS = {}
AVAILABLE_MODELS = {}
for obj in OBJECTIVES:
    XR[obj] = load_data(Path(f'../../data/{obj.split("/")[0]}'))
    YEARS[obj] = sorted(set(x.year for x in pd.date_range("2011", "2017", freq="Y")))
    BASINS[obj] = list(XR[obj][BASIN_VAR_NAME].values)
    AVAILABLE_MODELS[obj] = list(name for name in XR[obj]['model'].values if name != Q_VAR_NAME)
    LOGGER.info(f'Using years {YEARS[obj][0]}-{YEARS[obj][-1]} from {len(BASINS[obj])} basins and '
                f'{len(AVAILABLE_MODELS[obj])} models for objective {obj}')


def hash_model_name(model_name: str) -> str:
    return hashlib.sha512(f"{SALT}{model_name}".encode("utf-8")).hexdigest()


MODEL_HASHES = {hash_model_name(m): m for obj in OBJECTIVES for m in AVAILABLE_MODELS[obj]}

rating_div_winner = html.Div(id="rating-div-winner",
                             children=[
                                 dbc.Button("Model 1",
                                            id="btn_model_a",
                                            n_clicks=0,
                                            style={'backgroundColor': MODEL_ONE_COLOR},
                                            className="me-1 mt-1"),
                                 dbc.Button("Equally good",
                                            id="btn_equal_good",
                                            n_clicks=0,
                                            outline=True,
                                            color='dark',
                                            className="me-1 mt-1"),
                                 dbc.Button("Equally bad",
                                            id="btn_equal_bad",
                                            n_clicks=0,
                                            outline=True,
                                            color='dark',
                                            className="me-1 mt-1"),
                                 dbc.Button("Model 2",
                                            id="btn_model_b",
                                            n_clicks=0,
                                            style={'backgroundColor': MODEL_TWO_COLOR},
                                            className="me-1 mt-1"),
                                 dbc.Tooltip("Hydrographs are of equal quality, but both are good.",
                                             target="btn_equal_good",
                                             placement="bottom"),
                                 dbc.Tooltip("Hydrographs are of equal quality, but both are bad.",
                                             target="btn_equal_bad",
                                             placement="bottom"),
                             ])

rating_page = dbc.Card([
    dcc.Graph(id="line-chart", style={}),
    html.Center([
        html.Div([
            # describes whether to rate high flows, low flows, or overall
            html.Div(id='task-description', className='mb-2'),
            rating_div_winner,
            dcc.Loading(
                id="rating-loading",
                type="default",
                children=html.Div(id="rating-loading-output", className="mt-3 mb-3"),
            ),
        ]),
        html.Div(
            children=[
                dbc.Progress(id="rating-progress", value=0, color="info", className="mt-4", style={'height': '22px'}),
                html.Div(
                    html.Small(id="rating-progress-label", className="text-center w-100 mb-0"),
                    className="position-absolute h-100 w-100 d-flex align-items-center",
                    style={"top": "0"},
                ),
            ],
            className="position-relative",
        ),
    ]),
    dbc.Modal(
        id="modal-task",
        children=[
            dbc.ModalHeader(html.H4(id='modal-task-body', style={'text-align': 'center'}, className='mb-0 me-3')),
        ],
        is_open=False,
        centered=True,
    ),
    html.Div(id='location-dummy-rate'),
    dcc.Store(id='state-basin'),
    dcc.Store(id='state-objective'),
    dcc.Store(id='state-start_date'),
    dcc.Store(id='state-end_date'),
    dcc.Store(id='state-model_a'),
    dcc.Store(id='state-model_b'),
    # we'll use the counter's modified_time to track how long users take to rate each example.
    # we can't use the modified_time of the other states, because they don't always get modified every time
    # (two subsequent samples might have the same basin/models/etc.)
    dcc.Store(id='state-counter', data=-1),
])


@app.callback(
    Output("line-chart", "figure"),
    Output("state-basin", "data"),
    Output("state-objective", "data"),
    Output("state-start_date", "data"),
    Output("state-end_date", "data"),
    Output("state-model_a", "data"),
    Output("state-model_b", "data"),
    Output("state-counter", "data"),
    Output("task-description", "children"),
    Output("rating-progress", "value"),
    Output("rating-progress-label", "children"),
    Output("rating-loading-output", "value"),
    Output('modal-task-body', 'children'),
    Output('modal-task', 'is_open'),
    Output('location-dummy-rate', 'children'),
    Input("btn_model_a", "n_clicks"),
    Input("btn_model_b", "n_clicks"),
    Input("btn_equal_good", "n_clicks"),
    Input("btn_equal_bad", "n_clicks"),
    # https://dash.plotly.com/dash-core-components/store: Need to provide timestamp as input to have the user_id
    # variable populated already during the initial page load
    Input("state-user", "modified_timestamp"),
    State("state-user", "data"),
    State("state-basin", "data"),
    State("state-objective", "data"),
    State("state-start_date", "data"),
    State("state-end_date", "data"),
    State("state-model_a", "data"),
    State("state-model_b", "data"),
    State("line-chart", "figure"),
    # state gets updated with every rating, so the time since model_b was last modified tells us how long the user
    # took to rate the current example.
    State("state-counter", "data"),
    State("state-counter", "modified_timestamp"))
def update_line_chart(model_one_click: int, model_two_click: int, equal_good_click: int, equal_bad_click: int,
                      user_timestamp: int, user_id: str, basin: str, objective: str, start_date: str, end_date: str,
                      model_a_hash: str, model_b_hash: str, figure, counter_state: int, rating_start_time: int):

    # set a random seed, so that multiple workers (that are all forked from each other) don't have the same randomness
    # and therefore show the same tasks. It'd suffice to do this once per worker, but it's cheap and we'd need a global
    # variable to determine the first call, so we do it on every call.
    np.random.seed(int(time.time() * 1000) % (2**32))

    if user_id is None or user_id == '':
        return None, None, None, None, None, None, None, counter_state, '', 0, '', '', '', False, '/questionnaire'
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return None, None, None, None, None, None, None, counter_state, '', 0, '', '', '', False, '/questionnaire'

    y_scale = 'linear'
    task = None

    # Catch initial page loading, where no plot has been shown yet
    if basin is not None:

        rating_duration = int(time.time() * 1000) - rating_start_time

        # figure out if the user submitted their rating while looking at a log-scale or linear-scale axis
        if figure is not None:
            x_range = figure.get("layout", {}).get("xaxis", {}).get("range", [start_date, end_date])
            y_range = figure.get("layout", {}).get("yaxis", {}).get("range", [-999, -999])
            try:
                x_zoomed = any(
                    pd.to_datetime(x1) != pd.to_datetime(x2) for x1, x2 in zip(x_range, [start_date, end_date]))
            except Exception as exception:
                # just to be sure we don't crash if someone injects a non-date value
                LOGGER.warning(f'Invalid x range or start/end date: {x_range}, {[start_date, end_date]}')
                x_zoomed = False
            y_zoomed = not figure.get("layout", {}).get("yaxis", {}).get("autorange", True)
            y_scale = figure.get("layout", {}).get("yaxis", {}).get("type", 'linear')

        model_a, model_b = MODEL_HASHES[model_a_hash], MODEL_HASHES[model_b_hash]
        task = _get_task(counter_state)  # get task type for current counter (before incrementing)
        ratings = Rating(user_id=user_id,
                         objective=objective,
                         basin=basin,
                         start_date=start_date,
                         end_date=end_date,
                         model_a=model_a,
                         model_b=model_b,
                         rating_style='winner',
                         task=task,
                         rating_duration=rating_duration,
                         x_range=x_range,
                         y_range=y_range,
                         x_zoomed=x_zoomed,
                         y_zoomed=y_zoomed,
                         y_scale=y_scale)

        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        user.n_rated_hydrographs += 1
        if 'btn_model_a' in changed_id:
            ratings.num_a_wins = 1
            LOGGER.info(f"User {user_id} said that {model_a} > {model_b} for {task}")
        elif 'btn_model_b' in changed_id:
            ratings.num_b_wins = 1
            LOGGER.info(f"User {user_id} said that {model_a} < {model_b} for {task}")
        elif 'btn_equal_good' in changed_id:
            ratings.num_equal_good = 1
            LOGGER.info(f"User {user_id} said that {model_a} is equally good as {model_b} for {task}")
        elif 'btn_equal_bad' in changed_id:
            ratings.num_equal_bad = 1
            LOGGER.info(f"User {user_id} said that {model_a} is equally bad as {model_b} for {task}")
        else:
            pass

        try:
            db.session.add(user)
            db.session.add(ratings)
            db.session.commit()
        except exc.SQLAlchemyError as exception:
            LOGGER.error(f'Rating could not be committed: {exception}')

    # sample basin, time slice and models
    obj = np.random.choice(OBJECTIVES)
    basin = np.random.choice(BASINS[obj])
    year = np.random.choice(YEARS[obj][:-N_YEARS])
    start_date = pd.to_datetime(f"01-01-{year}", format="%d-%m-%Y")
    end_date = pd.to_datetime(f"31-12-{year+N_YEARS}", format="%d-%m-%Y")
    plot_models = [Q_VAR_NAME] + list(np.random.choice(AVAILABLE_MODELS[obj], 2, replace=False))
    df = XR[obj].sel({
        'model': plot_models,
        BASIN_VAR_NAME: basin,
        DATE_VAR_NAME: slice(start_date, end_date)
    }).to_dataframe().drop(BASIN_VAR_NAME, axis=1)

    # create line objects
    index = df.loc[Q_VAR_NAME].index
    data = [
        go.Scatter(y=df.loc[Q_VAR_NAME, Q_VAR_NAME],
                   x=index,
                   name="Q obs.",
                   line=dict(color=OBS_COLOR, dash='dot'),
                   yaxis='y'),
        go.Scatter(y=df.loc[plot_models[1], Q_VAR_NAME],
                   x=index,
                   name="Model 1",
                   line=dict(color=MODEL_ONE_COLOR),
                   yaxis='y'),
        go.Scatter(y=df.loc[plot_models[2], Q_VAR_NAME],
                   x=index,
                   name="Model 2",
                   line=dict(color=MODEL_TWO_COLOR),
                   yaxis='y')
    ]

    # define layout
    layout = go.Layout(xaxis={
        'type': 'date',
        'title': "Date",
        'range': [index[0], index[-1]],
        'titlefont': {
            'size': 16
        }
    },
                       yaxis={
                           'type': y_scale,
                           'title': "Discharge (m³/s)",
                           'range': [0, df.max() * 1.3],
                           'titlefont': {
                               'size': 16
                           }
                       },
                       updatemenus=[
                           dict(type="buttons",
                                direction="right",
                                xanchor="left",
                                yanchor="bottom",
                                y=1,
                                x=0,
                                active=0 if y_scale == 'linear' else 1,
                                buttons=list([
                                    dict(args=[{
                                        'yaxis.type': 'linear'
                                    }], label="Linear scale", method="relayout"),
                                    dict(args=[{
                                        'yaxis.type': 'log'
                                    }], label="Log scale", method="relayout")
                                ])),
                       ])

    new_task = _get_task(counter_state + 1)
    task_description = [html.H6('Which hydrograph is better in terms of ', style={'display': 'inline'})] \
                           + [html.H4(new_task, style={'display': 'inline'})] \
                           + [html.H6(' performance?', style={'display': 'inline'})]
    task_message = []
    if new_task != task:
        task_message = ['For the next 5 hydrographs, please concentrate on the ']
        if new_task == 'overall':
            task_message += [html.B(html.U('overall')), ' flow.']
        elif new_task == 'high-flow':
            task_message += [html.B(html.U('high')), ' flows.']
        else:
            task_message += [html.B(html.U('low')), ' flows.']

    n_recommended = 15
    rating_progress = min(100, user.n_rated_hydrographs / n_recommended * 100)
    progress_message = f'{n_recommended - user.n_rated_hydrographs} more hydrographs' if rating_progress < 100 \
        else 'Keep rating as many hydrographs as you like!'

    # use hashing so the user can't use browser dev tools to figure out the model names
    return dict(data=data, layout=layout), basin, obj, start_date, end_date, \
        hash_model_name(plot_models[1]), hash_model_name(plot_models[2]), \
            counter_state + 1, task_description, rating_progress, progress_message, '', task_message, task_message != [], None


def _get_task(counter: int) -> str:
    mod = counter % 15
    if mod < 5:
        task = 'overall'
    elif mod < 10:
        task = 'high-flow'
    else:
        task = 'low-flow'
    return task
