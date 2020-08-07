import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html

from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from django_plotly_dash import DjangoDash
from GreenPen.models import Syllabus, Student, Sitting, TeachingGroup
from GreenPen.settings import CURRENT_ACADEMIC_YEAR


# Helper functions:

def get_groups_from_graph(callback):
    """
    Returns a queryset of groups from the callback.

    :param callback: The Plotly Dash callback

    :returns: A queryset of all groups from any click events on the graph
    """

    # Start by finding our syllabus so we only get groups taught that syllabus:
    current_selected = Syllabus.objects.get(pk=get_root_pk(callback))
    # Groups to return
    groups = TeachingGroup.objects.filter(year_taught=CURRENT_ACADEMIC_YEAR,
                                          syllabus__in=current_selected.get_ancestors(include_self=True))
    ## Easy filter; If we've clicked a teaching group.

    if callback.inputs['group-chart.clickData']:
        name = callback.inputs['group-chart.clickData']['points'][0]['customdata']
        if name.startswith('group_'):
            group_pk = name.split('_')[1]
            groups = TeachingGroup.objects.filter(pk=group_pk)
        else:
            raise NotImplemented('No code designed for drilling into no-group objects')

    ## Now we filter for groups within our syllabus
    if callback.inputs['time-chart.clickData']:
        sitting_pk = callback.inputs['time-chart.clickData']['points'][0]['customdata']
        sitting = Sitting.objects.get(pk=sitting_pk)
        groups = groups.filter(sitting=sitting)

    ## Now we filter out for groups removed via teachinggroup dropdown
    if callback.inputs['teachinggroup-dropdown.value']:
        groups = groups.filter(pk=callback.inputs['teachinggroup-dropdown.value'])

    return groups

def get_students_from_graph(kwargs):
    """
    Returns a queryset of students filtered by other chart callback.
    :param callback: the plotyl dash callback
    :return: A queryset of students
    """
    inputs = kwargs['callback_context'].inputs
    user = kwargs['user']
    # Student should only see their own data
    if user.groups.filter(name='Students').count():
        return Student.objects.filter(user=user)

    # Not a user and not a teacher? Get lost!
    if not user.groups.filter(name='Teachers').count():
        raise NotImplementedError('Must be a teacher or a student')

    # Must be a teacher, so let's check what dropdown filters have been applied:
    students = Student.objects.all()
    if inputs['subject-dropdown.value']:
        students = students.filter(teachinggroup__syllabus=Syllabus.objects.get(pk=inputs['subject-dropdown.value']))
    if inputs['teachinggroup-dropdown.value']:
        students = students.filter(teachinggroup__pk=inputs['teachinggroup-dropdown.value'])
    if inputs['student-dropdown.value']:
        students = students.filter(pk=inputs['student-dropdown.value'])
    return students.distinct()


external_stylesheets=[dbc.themes.BOOTSTRAP]

app = DjangoDash('StudentDashboard', external_stylesheets=external_stylesheets)


app.layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.Div([
                dcc.Location(id='url', refresh=True),
                html.Label(["Subject",
                            dcc.Dropdown(id='subject-dropdown')]
                           ),
                html.Label(["Teaching Group",
                            dcc.Dropdown(id='teachinggroup-dropdown', )
                            ]),
                html.Label(["Student",
                            dcc.Dropdown(id='student-dropdown', )
                            ])

                ]),
        ]),
    ]),
    dbc.Row([
        dbc.Col(
        html.Div([
            dcc.Loading(
                id="sullabus-graph-loading",
                type="default",
                children=dcc.Graph(id='syllabus-graph')
            ),
        ]), sm=4
        ),
        dbc.Col([
            html.Div([
                html.H3('Over Time'),
                dcc.Loading(
                    id="time-chart-loading",
                    type="default",
                    children=dcc.Graph(id='time-chart')
                ),
            html.Button('Reset filter on this graph', id='time-chart-reset')
            ])

        ], sm=4
        ),
        dbc.Col([
            html.Div([
            html.H3('Group Performance'),
            dcc.Loading(
                id="group-performance-loading",
                type="default",
                children=dcc.Graph(id='group-chart')
            ),
            html.Button('Reset filter on this graph', id='group-performance-reset')
            ])
        ], sm=4)
    ])
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


def filter_syllabus_points(callback):
    """ Takes any callback and creates a filtered queryset of syllabus points for later use """


def get_root_pk(callback):
    """
    Returns the primary key to place at the centre of a sunburst plot.

    :param callback: The plotly dash callback to scan for relevant data

    :return: An integer corresponding to the pk at the cenre of the sunburst

    """
    # This will be over-ridden if we have clicked on a value.
    subject_pk = callback.inputs['subject-dropdown.value']

    # Check if the user has at some point filtered on the sunburst:
    if 'syllabus-graph.clickData' in callback.inputs:
        if callback.inputs['syllabus-graph.clickData']:
            subject_pk = callback.inputs['syllabus-graph.clickData']['points'][0]['customdata']

    return subject_pk


@app.expanded_callback(
    Output('syllabus-graph', 'figure'),
    [Input('subject-dropdown', 'value'),
     Input('group-chart', 'clickData'),
     Input('teachinggroup-dropdown', 'value'),
     Input('student-dropdown', 'value'),
     ])
def update_syllabus_sunburst(*args, **kwargs):
    callback = kwargs['callback_context']
    if not callback.inputs['student-dropdown.value']:
        return False
    subject_pk = callback.inputs['subject-dropdown.value']

    students = get_students_from_graph(kwargs)

    parent_point = Syllabus.objects.get(pk=subject_pk)
    points = parent_point.get_descendants(include_self=True)
    labels = [point.text for point in points]
    ids = [point.pk for point in points]
    parents = [point.parent.text for point in points]
    parents[0] = ""
    values = [1 for point in points]
    colors = [point.cohort_stats(students)['rating'] for point in points]

    graph = go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        customdata=ids,
        marker=dict(colors=colors,
                    colorscale='RdYlGn',
                    cmid=2.5,
                    cmax=5,
                    cmin=0),
        hovertemplate='<b>%{label}</b><br>Average rating: %{color}',
        name='',

    )
    layout = go.Layout(
        margin=dict(t=0, l=0, r=0, b=0),
        uniformtext=dict(minsize=10, mode='hide'),
        title='Syllabus Performance Explorer',
        showlegend=False

    )

    return {'data': [graph], 'layout': layout}


@app.expanded_callback(
    Output('time-chart', 'figure'),
    [Input('subject-dropdown', 'value'),
     Input('syllabus-graph', 'clickData'),
     Input('group-chart', 'clickData'),
     Input('time-chart', 'clickData'),
     Input('teachinggroup-dropdown', 'value'),
     Input('student-dropdown', 'value')])
def update_rating_time_graph(*args, **kwargs):
    callback = kwargs['callback_context']
    parent_pk = get_root_pk(callback)
    if not callback.inputs['student-dropdown.value']:
        return False
    parent_point = Syllabus.objects.get(pk=parent_pk)
    students = get_students_from_graph(kwargs)

    # Only update the graph if we're down to a signle student
    if students.count() != 1:
        return False

    groups = TeachingGroup.objects.filter(students__in=students)
    records = Sitting.objects.filter(exam__question__syllabus_points__in=parent_point.get_descendants(),
                                     group__in=groups
                                     ).order_by('date').distinct()
    # text = [sitting.exam.name for sitting in records]
    # x = [sitting.date for sitting in records]
    # y = [sitting.avg_syllabus_rating(parent_point) for sitting in records]

    text = []
    x = []
    y = []
    ids = []

    for sitting in records:
        if sitting.student_total(students[0]):
            string = str(sitting.group.name) + "<br>" + str(sitting.exam.name)
            text.append(string)
            x.append(sitting.date)
            y.append(round(sitting.student_total(students[0])/sitting.exam.total_score(),2)*100)
            ids.append(sitting.pk)

    graph = go.Scatter(
        x=x,
        y=y,
        text=text,
        mode='lines+markers',
        marker=dict(color=y,
                    colorscale='RdYlGn',
                    cmid=2.5,
                    cmax=5,
                    cmin=0),
        customdata=ids

    )
    layout = go.Layout(
        xaxis={
            'title': 'Date of assessment',
        },
        yaxis={
            'title': 'Percentage scored',
            'range': [0, 100]
        }
    )

    return {'data': [graph], 'layout': layout}


def clicked_sitting(callback):
    pass


@app.expanded_callback(
    Output('group-chart', 'clickData'),
    [Input('group-performance-reset', 'n_clicks')]
)
def reset_group_graph(*args, **kwargs):
    return False


@app.expanded_callback(
    Output('time-chart', 'clickData'),
    [Input('time-chart-reset', 'n_clicks')]
)
def reset_time_graph(*args, **kwargs):
    return False


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
    user = kwargs['user']

    # Teachers can see everyone:
    if user.groups.filter(name='Teachers').count():
        subjects = Syllabus.objects.filter(level=2)

    elif user.groups.filter(name='Students').count():
        student = Student.objects.get(user=user)
        teachinggroups = TeachingGroup.objects.filter(students=student)
        subjects = Syllabus.objects.filter(teachinggroup__in=teachinggroups)
    else:
        raise NotImplementedError('User must belong to either Teachers or Students groups')

    # Build a list of subjects taken by the student.
    subject_options = [dict(label=subject.text, value=subject.pk) for subject in subjects.distinct()]

    return subject_options

@app.expanded_callback(
    Output('teachinggroup-dropdown', 'options'),
    [Input('subject-dropdown', 'value')]
)
def update_classgroup_dropdowns(*args, **kwargs):
    syllabus_pk = kwargs['callback_context'].inputs['subject-dropdown.value']
    if not syllabus_pk:
        return False
    syllabus = Syllabus.objects.get(pk=syllabus_pk)
    user = kwargs['user']
    # Teachers can see everyone:
    if user.groups.filter(name='Teachers').count():
        classgroups = TeachingGroup.objects.filter(syllabus=syllabus)

    elif user.groups.filter(name='Students').count():
        student = Student.objects.get(user=user)
        classgroups = TeachingGroup.objects.filter(students=student,
                                                   syllabus=syllabus)
    else:
        raise NotImplementedError('User must belong to either Teachers or Students groups')


    return [dict(label=group.name, value=group.pk) for group in classgroups]


@app.expanded_callback(
    Output('student-dropdown', 'options'),
    [Input('teachinggroup-dropdown', 'value')]
)
def update_student_dropdown(*args, **kwargs):
    teachingroup_pk = kwargs['callback_context'].inputs['teachinggroup-dropdown.value']
    if not teachingroup_pk:
        return False
    teachinggroup = TeachingGroup.objects.get(pk=teachingroup_pk)
    user = kwargs['user']
    # Teachers can see everyone:
    if user.groups.filter(name='Teachers').count():
        students = Student.objects.filter(teachinggroup=teachinggroup)

    elif user.groups.filter(name='Students').count():
        student = Student.objects.get(user=user)
        students = Student.objects.filter(pk=student.pk)
    else:
        raise NotImplementedError('User must belong to either Teachers or Students groups')


    return [dict(label=student.full_name(), value=student.pk) for student in students]

@app.expanded_callback(
    Output('student-dropdown', 'value'),
    [Input('student-dropdown', 'options')]
)
def set_default_student(*args, **kwargs):
    # Only need to do this if we're a student, otherwise it's confusing!
    if kwargs['user'].groups.filter(name='Teachers').count():
        return False
    else:
        return kwargs['callback_context'].inputs['student-dropdown.options'][0]['value']

@app.expanded_callback(
    Output('subject-dropdown', 'value'),
    [Input('subject-dropdown', 'options')]
)
def set_default_subject(*args, **kwargs):
    # Only need to do this if we're a student, otherwise it's confusing!
    if kwargs['user'].groups.filter(name='Teachers').count():
        return False
    else:
        return kwargs['callback_context'].inputs['subject-dropdown.options'][0]['value']

@app.expanded_callback(
    Output('teachinggroup-dropdown', 'value'),
    [Input('teachinggroup-dropdown', 'options')]
)
def set_default_teachinggroup(*args, **kwargs):
    # Only need to do this if we're a student, otherwise it's confusing!
    if kwargs['user'].groups.filter(name='Teachers').count():
        return False
    else:
        return kwargs['callback_context'].inputs['teachinggroup-dropdown.options'][0]['value']