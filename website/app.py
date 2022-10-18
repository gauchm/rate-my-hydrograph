import logging
import os
from pathlib import Path
import sys

import dash
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

LOGGER = logging.getLogger(__name__)

load_dotenv()  # load environment variables from .env
SALT = os.environ.get("SALT")
db_connector = os.environ.get("DB_CONNECTOR", "postgresql")
db_name = os.environ.get("DB_NAME", "ratemyhydrograph")
db_user = os.environ.get("DB_USER")
db_pwd = os.environ.get("DB_PASSWORD")
log_file = os.environ.get("LOG_FILE", "ratemyhydrograph.log")
if db_user is None or db_pwd is None or SALT is None:
    raise ValueError('Database user/password or salt missing. Check .env file.')

DESCRIPTION = 'Your task is simple: Compare the simulated hydrographs against the observations and ' + \
              'decide which one is better!'
server = Flask(__name__)
app = dash.Dash(__name__,
                server=server,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                serve_locally=False,
                meta_tags=[{
                    'name': 'viewport',
                    'content': 'width=device-width, initial-scale=1.0'
                }, {
                    'http-equiv': 'X-UA-Compatible',
                    'content': 'IE=edge'
                }, {
                    'property': 'og:title',
                    'content': 'Rate My Hydrograph'
                }, {
                    'property': 'title',
                    'content': 'Rate My Hydrograph'
                }, {
                    'name': 'og:description',
                    'content': DESCRIPTION
                }, {
                    'name': 'description',
                    'content': DESCRIPTION
                }, {
                    'property': 'og:image',
                    'content': 'https://images.plot.ly/logo/new-branding/plotly-logomark.png'
                }, {
                    'property': 'og:image:alt',
                    'content': 'Rate-My-Hydrograph logo'
                }, {
                    'property': 'twitter:card',
                    'content': 'summary'
                }])

# we have components that are created by callbacks, so we have to turn of the option that checks if all IDs are
# present at app start time. (https://stackoverflow.com/a/69199781)
app.config.suppress_callback_exceptions = True

app.title = 'Rate My Hydrograph'
server.config["SQLALCHEMY_DATABASE_URI"] = f"{db_connector}://{db_user}:{db_pwd}@localhost/{db_name}"
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
server.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 300, 'pool_pre_ping': True}
db = SQLAlchemy(server)


def setup_logging(log_file: str):
    """Initialize logging to `log_file` and stdout.

    Parameters
    ----------
    log_file : str
        Name of the log file.
    """
    file_handler = logging.FileHandler(filename=log_file)
    stdout_handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(handlers=[file_handler, stdout_handler], level=logging.INFO, format='%(asctime)s: %(message)s')

    # Log uncaught exceptions
    def exception_logging(typ, value, traceback):
        LOGGER.exception('Uncaught exception', exc_info=(typ, value, traceback))

    sys.excepthook = exception_logging

    LOGGER.info(f'Logging to {log_file} initialized.')


Path(log_file).parent.mkdir(exist_ok=True)
setup_logging(log_file)
