from dash import html, dcc

with open("about.md", "r") as f:
    ABOUT_TEXT = "".join(f.readlines())

instructions = html.Div([
    html.Div([
        html.P([
            'Your task is simple:',
            html.Br(),
            html.B(
                'Compare the simulated hydrographs in orange and purple against the dotted ground truth observations '
                'in black and decide which one is better!'),
        ]),
        html.P([
            'We\'ll start the ratings with 3 sections of 5 hydrographs. The first section is about overall hydrograph '
            'quality, the second section focuses on high flows, and the last section focuses on low flows. '
            'After these, you can keep rating as many hydrographs as you like '
            '(the more ratings we collect, the better we can analyze them for patterns).',
        ]),
        html.P([
            'If you want to look at a certain event more closely, you can '
            'click and drag the area to zoom in, or use the controls in the top right corner of the plot. '
            'Double-click to reset the zoom level.',
        ]),
    ],
             className='mb-4'),
    html.H5('About'),
    html.P('This is a project by Martin Gauch, Frederik Kratzert, Juliane Mai, Bryan Tolson, Grey Nearing, '
           'Hoshin Gupta, Sepp Hochreiter, and Daniel Klotz. '
           'If you have any questions, don\'t hesitate to contact us via gauch(at)ml.jku.at'),
    html.Details([
        html.Summary([html.B('Background information'), ' (click to expand)']),
        dcc.Markdown(ABOUT_TEXT, className="mb-5")
    ]),
])
