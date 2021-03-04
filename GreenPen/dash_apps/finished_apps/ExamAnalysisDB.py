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
                    )
            ),
        ] ,className="twelve columns"),

    ], className='Row'),

])


app.css.append_css({
    'external_url': '/staticfiles/css/dash.css'
})




@app.expanded_callback(
    [Output('results-table', 'data'),Output('results-table', 'columns')],
    [Input('subject-dropdown', 'value'),
     Input('exam-dropdown', 'value'),
     Input('sitting-dropdown', 'value'),
     ])
def update_results_table(*args, **kwargs):

    # Placeholder test values
    e = Exam.objects.get(name="2020/21 Mock Y12 Structured paper")
    qs = Mark.objects.filter(sitting__exam=e)
    df = generate_analsysios_df(qs)
    columns = [{"name": i, "id": i} for i in df.columns]
    data = df.to_dict('records')


    return data, columns



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


