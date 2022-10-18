import logging
from typing import List, Tuple, Union

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html
from sqlalchemy import exc

from app import app, db
from database import User

LOGGER = logging.getLogger(__name__)

OCCUPATIONS = [{
    'label': 'Academia',
    'value': 'academia'
}, {
    'label': 'Industry',
    'value': 'industry'
}, {
    'label': 'Public sector',
    'value': 'public-sector'
}]
FOCUS_AREAS = [{
    'label': 'Flood modeling',
    'value': 'flood-modeling'
}, {
    'label': 'Drought modeling',
    'value': 'drought-modeling'
}, {
    'label': 'Water resources management',
    'value': 'water-resources'
}, {
    'label': 'Water quality',
    'value': 'waterquality'
}, {
    'label': 'Hydropower',
    'value': 'hydropower'
}, {
    'label': 'Consulting',
    'value': 'consulting'
}, {
    'label': 'Insurance',
    'value': 'Insurance'
}, {
    'label': 'Social sciences',
    'value': 'social-sciences'
}, {
    'label': 'Other',
    'value': 'other'
}]

with open('assets/countries.txt', 'r') as f:
    COUNTRIES = [line.strip() for line in f.readlines()]

questionnaire_page = dbc.Card(
    dbc.CardBody([
        html.H4("Before we start, we'd like to ask you a few demographic questions", className="card-title mb-4"),
        dbc.Form(id="questionnaire-form",
                 children=[
                     dbc.Label('Primary occupation', html_for='radio-occupation'),
                     dbc.RadioItems(id='radio-occupation',
                                    options=OCCUPATIONS,
                                    value=OCCUPATIONS[0]['value'],
                                    labelStyle={'display': 'inline-block'}),
                     dbc.Label('Focus area(s)', html_for='checklist-focus', className="mt-3"),
                     dbc.Checklist(id='checklist-focus', options=FOCUS_AREAS, labelStyle={'display': 'inline-block'}),
                     html.Div(id="focus-freetext-div",
                              hidden=True,
                              className='mt-1',
                              children=[
                                  dbc.Input(id='focus-freetext',
                                            type='text',
                                            placeholder='Enter focus area',
                                            maxlength=100,
                                            minlength=2,
                                            className="w-50")
                              ]),
                     dbc.Label('How many years of experience do you have related to hydrology?',
                               html_for='years-experience',
                               className='mt-3'),
                     dbc.Input(id='years-experience', type='number', min=0, max=100, step=1, className="w-50"),
                     dbc.Label('Country of residence', html_for='country', className='mt-3'),
                     dbc.Select(id='country',
                                required=True,
                                options=[{
                                    'label': c,
                                    'value': c
                                } for c in COUNTRIES],
                                className="w-50"),
                     dbc.Label('Gender', html_for='radio-gender', className='mt-3'),
                     dbc.RadioItems(id='radio-gender',
                                    options=[{
                                        'label': 'Male',
                                        'value': 'male'
                                    }, {
                                        'label': 'Female',
                                        'value': 'female'
                                    }, {
                                        'label': 'Other/prefer not to disclose',
                                        'value': 'other'
                                    }],
                                    value='other',
                                    labelStyle={'display': 'inline-block'}),
                     dbc.Label("Terms and conditions", html_for='consent-checkbox', className='mt-3'),
                     dbc.Checkbox(
                         id="consent-checkbox",
                         value=False,
                         label="I consent with the use of the data I enter on this webpage for research purposes. "
                         "I understand that the data may be published as a research publication. "
                         "I understand that this website will store a unique id in my browser's localStorage to "
                         "recognize me if I reopen the site at a later point.",
                     ),
                     dbc.Button('Start rating hydrographs',
                                id='submit-questionnaire',
                                type='submit',
                                n_clicks=0,
                                disabled=True,
                                color="primary",
                                className="mt-2")
                 ]),
        html.Div(id='location-dummy')
    ]))


@app.callback(
    Output("focus-freetext-div", "hidden"),
    Input("checklist-focus", "value"),
)
def hide_focus_freetext(focus_areas: List[str]):
    return focus_areas is None or 'other' not in focus_areas


@app.callback(
    Output("submit-questionnaire", "disabled"),
    Input("radio-occupation", "value"),
    Input("checklist-focus", "value"),
    Input("focus-freetext", "value"),
    Input("radio-gender", "value"),
    Input("country", "value"),
    Input("years-experience", "value"),
    Input("consent-checkbox", "value"),
)
def validate_questionnaire(occupation: str, focus_areas: List[str], focus_text: str, gender: str, country: str,
                           years_experience: int, consent_checked: bool):
    # if invalid, display link as disabled
    return not _form_is_valid(occupation=occupation,
                              focus_areas=focus_areas,
                              focus_text=focus_text,
                              gender=gender,
                              country=country,
                              years_experience=years_experience,
                              consent_checked=consent_checked,
                              verbose_check=False)


@app.callback(
    Output("state-user", "data"),
    Output('location-dummy', 'children'),
    Output('alert-error', 'children'),
    Output('alert-error', 'is_open'),
    Input("submit-questionnaire", "n_clicks"),
    State("radio-occupation", "value"),
    State("checklist-focus", "value"),
    State("focus-freetext", "value"),
    State("radio-gender", "value"),
    State("country", "value"),
    State("years-experience", "value"),
    State("consent-checkbox", "value"),
    State("state-user", "data"),
)
def submit_questionnaire(submit_clicks: int, occupation: str, focus_areas: List[str], focus_text: str, gender: str,
                         country: str, years_experience: int, consent_checked: bool, user_id: str):
    if user_id is not None and user_id != '':
        user = User.query.filter_by(id=user_id).first()
        if user is not None:
            return user_id, dcc.Location(id='welcome-redirect', pathname='/welcomeback'), \
                'Cannot resubmit questionnaire for an existing user', True

    if submit_clicks is not None and submit_clicks > 0:
        is_valid, messages = _form_is_valid(occupation=occupation,
                                            focus_areas=focus_areas,
                                            focus_text=focus_text,
                                            gender=gender,
                                            country=country,
                                            years_experience=years_experience,
                                            consent_checked=consent_checked,
                                            verbose_check=True)
        if is_valid:
            if 'other' in focus_areas:
                focus_areas.append(focus_text.strip())
            focus_areas = ','.join(focus_areas)
            user = User(occupation=occupation,
                        focus_areas=focus_areas,
                        gender=gender,
                        country=country,
                        years_experience=years_experience)
            user_id = user.id

            try:
                db.session.add(user)
                db.session.commit()
            except exc.SQLAlchemyError as exception:
                LOGGER.error(f'User could not be committed: {exception}')
                return user_id, [], [html.H5('A database error occurred')], True

            LOGGER.info(f"New user {user}")
            return user_id, dcc.Location(id='rating-redirect', pathname='/rate'), '', False
        return user_id, [], [html.H5('Form is invalid')] + messages, True
    return user_id, [], '', False


def _form_is_valid(occupation: str, focus_areas: List[str], focus_text: str, gender: str, country: str,
                   years_experience: int, consent_checked: bool,
                   verbose_check: bool) -> Union[bool, Tuple[bool, List[html.P]]]:
    messages = []
    if not consent_checked:
        messages.append('Please accept terms')
    if gender not in ['male', 'female', 'other']:
        messages.append('Invalid gender option selected')
    if country is None or country.strip() == '':
        messages.append('Please provide a country of residence')
    if country is not None and country not in COUNTRIES:
        messages.append('Country of residence too long')
    if years_experience is None or not isinstance(years_experience, int) \
            or years_experience < 0 or years_experience > 100:
        messages.append('Years of experience must be a number between 0 and 100')
    if occupation is None:
        messages.append('Please specify occupation')
    if occupation is not None and occupation not in [occ['value'] for occ in OCCUPATIONS]:
        messages.append('Invalid occupation')
    if focus_areas is None or len(focus_areas) == 0:
        messages.append('Please specify at least one focus area')
    if occupation is not None and focus_areas is not None and any(
            focus not in [option['value'] for option in FOCUS_AREAS] for focus in focus_areas):
        messages.append('Invalid focus area')
    if focus_areas is not None and 'other' in focus_areas and (focus_text is None or focus_text.strip() == ''):
        messages.append('Please specify your focus area')
    if focus_text is not None and len(focus_text) > 100:
        messages.append('Focus area description too long.')

    is_valid = len(messages) == 0
    if verbose_check:
        return is_valid, [html.P(m) for m in messages]
    return is_valid
