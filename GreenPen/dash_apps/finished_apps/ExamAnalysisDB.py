import dash_core_components as dcc
import dash_daq as daq
import dash_table
import dash_html_components as html

from django_pandas.io import read_frame

from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from django_plotly_dash import DjangoDash
from GreenPen.models import Syllabus, Student, Sitting, TeachingGroup, Mistake, Mark, Question, Exam
from django.contrib.auth.models import User
from GreenPen.settings import CURRENT_ACADEMIC_YEAR
from GreenPen.models import generate_analsysios_df

import colorlover

external_stylesheets=[dbc.themes.BOOTSTRAP]

app = DjangoDash('ExamAnalysisDB', external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Location(id='url', refresh=True),
                    html.Label(["Subject",
                                dcc.Dropdown(id='subject-dropdown')]
                               ),
                    html.Label(["Exam",
                                dcc.Dropdown(id='exam-dropdown', )
                                ]),
                    html.Label(["Sitting",
                                dcc.Dropdown(id='sitting-dropdown', )
                                ])

                ]),
            ]),
        ]), ]),
    html.Div([
        html.Div([
            html.H3('Results'),
            dcc.Loading(
                id="results-table-loading",
                type="default",
                children=dash_table.DataTable(
                    id='results-table',
                    export_format="xlsx",
                    )
            ),
        ] ,className="twelve columns"),

    ], className='Row'),

])


app.css.append_css({
    'external_url': '/staticfiles/css/dash.css'
})




@app.expanded_callback(
    [Output('results-table', 'data'),
     Output('results-table', 'columns'),
     Output('results-table', 'style_data_conditional')],
    [Input('subject-dropdown', 'value'),
     Input('exam-dropdown', 'value'),
     Input('sitting-dropdown', 'value'),
     ])
def update_results_table(*args, **kwargs):
    callback = kwargs['callback_context']

    # Only want to filter for one exam at a time, and optionally one sitting
    e_pk = callback.inputs['exam-dropdown.value']
    if not e_pk:
        return [], [], []
    qs = Mark.objects.filter(sitting__exam__pk=e_pk)

    s_pk = callback.inputs['sitting-dropdown.value']
    if s_pk:
        qs = qs.filter(sitting__pk=s_pk)

    df = generate_analsysios_df(qs)
    # Need to reset index to include questoin number
    df = df.reset_index()
    styles = discrete_background_color_bins(df)
    columns = [{"name": i, "id": i} for i in df.columns]
    data = df.to_dict('records')

    return data, columns, styles


@app.expanded_callback(
    Output('subject-dropdown', 'options'),
    [Input('url', 'pathname')]
)
def update_subject_options(*args, **kwargs):
    """
    Update the list of options for subjects based on the students TeachingGroup enrolements.
    :param args:
    :param kwargs:
    :return:
    """
    subjects = Syllabus.objects.filter(level=2)
    # Build a list of subjects taken by the student.
    subject_options = [dict(label=subject.text, value=subject.pk) for subject in subjects.distinct()]

    return subject_options

@app.expanded_callback(
    Output('exam-dropdown', 'options'),
    [Input('subject-dropdown', 'value')]
)
def update_exam_dropdown(*args, **kwargs):
    syllabus_pk = kwargs['callback_context'].inputs['subject-dropdown.value']
    if not syllabus_pk:
        return False
    syllabus = Syllabus.objects.get(pk=syllabus_pk)
    exams = Exam.objects.filter(syllabus__in=syllabus.get_descendants(include_self=True))

    return [dict(label=exam.name, value=exam.pk) for exam in exams]


@app.expanded_callback(
    Output('sitting-dropdown', 'options'),
    [Input('exam-dropdown', 'value')]
)
def update_sitting_dropdown(*args, **kwargs):
    exam_pk = kwargs['callback_context'].inputs['exam-dropdown.value']
    if not exam_pk:
        return False

    sittings = Sitting.objects.filter(exam__pk=exam_pk)

    return [dict(label=str(sitting), value=sitting.pk) for sitting in sittings]


def discrete_background_color_bins(df, n_bins=5, columns='all'):

    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()
    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]
    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]['div']['RdYlBu'][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                            '{{{column}}} >= {min_bound}' +
                            (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })
        legend.append(
            html.Div(style={'display': 'inline-block', 'width': '60px'}, children=[
                html.Div(
                    style={
                        'backgroundColor': backgroundColor,
                        'borderLeft': '1px rgb(50, 50, 50) solid',
                        'height': '10px'
                    }
                ),
                html.Small(round(min_bound, 2), style={'paddingLeft': '2px'})
            ])
        )

    return styles