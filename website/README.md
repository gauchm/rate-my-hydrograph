# Rate My Hydrograph Website

This directory contains the necessary files to run the "Rate My Hydrograph" website that was used to collect responses in the study.
The website is implemented as a [Dash](https://plotly.com/dash) application.

## Content

- `app.py`: The actual dash app. You can start the server with `python app.py`.
- `index.py`: The start page.
- `apps/`: The pages for ratings, questionnaire, leaderboard, and instructions.
- `database.py`: Configuration of the database that stores participants and ratings.
- `uwsgi.ini`: Configuration file of the application server.
- `environment.yaml`: Environment file used to run the website.

## Setup

- Create a `.env` file with contents:
    ```bash
    DB_USER=<database user name>
    DB_PASSWORD=<db password>
    DB_NAME=<db name>  # optional, default: ratemyhydrograph
    DB_CONNECTOR=<db connection string>  # default: postgresql. Others: see https://martin-thoma.com/sql-connection-strings/
    SALT=<some random string>  # used to hash the model name that is stored in the browser session
    LOG_FILE=<path/to/logfile.log>  # default: ratemyhydrograph.log
    ```
- Connect to postgres with `psql` (note: if you used a database other than postgres, this command will vary) and create the database: `CREATE DATABASE ratemyhydrograph;`
- Depending on your directory structure, you may need to modify the paths to the netCDF files with model simulations and observations in `apps/rate.py`.
- To run:
  - locally: `python index.py`
  - with uwsgi: `uwsgi uwsgi.ini` (note: you may need to adapt some paths in uwsgi.ini)

## Requirements
`conda env create --file environment.yml`