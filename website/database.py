import logging
from typing import Tuple
import uuid
from datetime import datetime, timezone

from app import db

LOGGER = logging.getLogger(__name__)


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    objective = db.Column(db.String(255))
    basin = db.Column(db.String(255))
    start_date = db.Column(db.DateTime())
    end_date = db.Column(db.DateTime())
    model_a = db.Column(db.String(255))
    model_b = db.Column(db.String(255))
    num_a_wins = db.Column(db.Integer())
    num_b_wins = db.Column(db.Integer())
    num_equal_good = db.Column(db.Integer())
    num_equal_bad = db.Column(db.Integer())
    num_skip = db.Column(db.Integer())
    rating_values = db.Column(db.String(255))
    rating_style = db.Column(db.String(255))
    task = db.Column(db.String(255))
    rating_duration = db.Column(db.Integer())
    x_zoomed = db.Column(db.Boolean())
    y_zoomed = db.Column(db.Boolean())
    x_range_start = db.Column(db.String(255))
    x_range_end = db.Column(db.String(255))
    y_range_start = db.Column(db.Float())
    y_range_end = db.Column(db.Float())
    y_scale = db.Column(db.String(255))
    last_modified = db.Column(db.DateTime(),
                              default=lambda: datetime.now(tz=timezone.utc),
                              onupdate=lambda: datetime.now(tz=timezone.utc))

    user_id = db.Column(db.String(255), db.ForeignKey('user.id'), nullable=False)

    def __init__(self, basin: str, objective: str, start_date: str, end_date: str, model_a: str, model_b: str,
                 rating_style: str, task: str, rating_duration: int, x_zoomed: bool, y_zoomed: bool,
                 x_range: Tuple[str, str], y_range: Tuple[float, float], y_scale: str, **kwargs):
        super().__init__(**kwargs)
        if len(x_range) < 2:
            x_range = ['unknown', 'unknown']
            LOGGER.warning(f'Encountered invalid x range {x_range}')
        if len(y_range) < 2 or not isinstance(y_range[0], (float, int)) or not isinstance(y_range[1], (float, int)):
            y_range = [-999, -999]
            LOGGER.warning(f'Encountered invalid y range {y_range}')

        self.basin = basin
        self.objective = objective
        self.start_date = start_date
        self.end_date = end_date
        self.model_a = model_a
        self.model_b = model_b
        self.rating_style = rating_style
        self.task = task
        self.rating_duration = rating_duration
        self.num_a_wins = 0
        self.num_b_wins = 0
        self.num_equal_good = 0
        self.num_equal_bad = 0
        self.num_skip = 0
        self.rating_values = ""
        self.x_zoomed = x_zoomed
        self.y_zoomed = y_zoomed
        self.x_range_start = x_range[0]
        self.x_range_end = x_range[1]
        self.y_range_start = y_range[0]
        self.y_range_end = y_range[1]
        self.y_scale = y_scale

    def __repr__(self):
        return f"<Rating (User {self.user_id}, basin {self.basin}, objective {self.objective}, \
            {self.start_date}-{self.end_date}, \
            style: {self.rating_style}, task: {self.task}): \
                {self.num_a_wins} wins {self.model_a}, {self.num_b_wins} wins {self.model_b}, \
                {self.num_equal_good} equally good, {self.num_equal_bad} equally bad>"


class User(db.Model):
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    n_rated_hydrographs = db.Column(db.Integer())
    creation_time = db.Column(db.DateTime(), default=lambda: datetime.now(tz=timezone.utc))

    occupation = db.Column(db.String(1000))
    focus_areas = db.Column(db.String(1000))
    gender = db.Column(db.String(255))
    country = db.Column(db.String(255))
    years_experience = db.Column(db.Integer())

    ratings = db.relationship("Rating", backref="rating", lazy=True)

    def __init__(self, occupation: str, focus_areas: str, gender: str, country: str, years_experience: int, **kwargs):
        super().__init__(**kwargs)

        self.id = str(uuid.uuid4())
        self.n_rated_hydrographs = 0
        self.creation_time = datetime.now(tz=timezone.utc)

        self.occupation = occupation
        self.focus_areas = focus_areas
        self.gender = gender
        self.country = country
        self.years_experience = years_experience

    def __repr__(self):
        return f"<User (id={self.id}): created {self.creation_time.strftime('%Y-%m-%d %H:%M:%S %z')}, \
            {self.n_rated_hydrographs} ratings>"
