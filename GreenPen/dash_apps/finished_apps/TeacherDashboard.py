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



# Helper functions:

def get_groups_from_graph(callback, user=User.objects.none()):
    """
    Returns a queryset of groups from the callback.

    :param callback: The Plotly Dash callback

    :returns: A queryset of all groups from any click events on the graph
    """

    # If we're a student, only output themselves.
    if user.groups.filter(name='Students').count():
        groups = TeachingGroup.objects.filter(students=Student.objects.get(user=user),
                                              archived=False)

    if user.groups.filter(name='Teachers').count():

        current_selected = get_syllabus_point_from_graph(callback)
        # Groups to return
        groups = TeachingGroup.objects.filter(year_taught=CURRENT_ACADEMIC_YEAR,
                                              archived=False,
                                              syllabus__in=current_selected.get_ancestors(include_self=True).distinct())
    ## Easy filter; If we've clicked a teaching group.

    if callback.inputs['group-chart.clickData']:
        name = callback.inputs['group-chart.clickData']['points'][0]['customdata']
        if name.startswith('group_'):
            group_pk = name.split('_')[1]
            groups = TeachingGroup.objects.filter(pk=group_pk)
        else:
            # We're dealing with a student:
            student_pk = name.split('_')[1]
            student = Student.objects.get(pk=student_pk)
            groups = TeachingGroup.objects.filter(students=student)

    ## Now we filter for groups within our syllabus
    if callback.inputs['time-chart.clickData']:
        sitting_pk = callback.inputs['time-chart.clickData']['points'][0]['customdata']
        sitting = Sitting.objects.get(pk=sitting_pk)
        groups = TeachingGroup.objects.filter(sitting=sitting)

    ## Now we filter out for groups removed via teachinggroup dropdown
    if 'teachinggroup-dropdown.value' in callback.inputs:
        if callback.inputs['teachinggroup-dropdown.value']:
            groups = groups.filter(pk=callback.inputs['teachinggroup-dropdown.value'])

    return groups


def get_students_from_graph(callback, user=User.objects.none(), groups=TeachingGroup.objects.filter(archived=False)):
    """
    Returns a queryset of students filtered by other chart callback.
    :param callback: the plotyl dash callback
    :return: A queryset of students
    """
    students = Student.objects.filter(teachinggroup__in=groups)
    inputs = callback.inputs

    if user.groups.filter(name='Students').count():
        return Student.objects.filter(user=user)
    elif user.groups.filter(name='Teachers').count():
        if 'group-chart.clickData'  in callback.inputs:
            if callback.inputs['group-chart.clickData']:
                name = callback.inputs['group-chart.clickData']['points'][0]['customdata']
                if name.startswith('group_'):
                    group_pk = name.split('_')[1]
                    students = students.filter(teachinggroup__pk=group_pk)
                else:
                    student_pk = name.split('_')[1]
                    students = students.filter(pk=student_pk)

        if inputs['subject-dropdown.value']:
            students = students.filter(
                teachinggroup__syllabus=Syllabus.objects.get(pk=inputs['subject-dropdown.value']))
        if 'teachinggroup-dropdown.value' in inputs:
            if inputs['teachinggroup-dropdown.value']:
                students = students.filter(teachinggroup__pk=inputs['teachinggroup-dropdown.value'])
        if 'student-dropdown.value' in inputs:
            if inputs['student-dropdown.value']:
                students = students.filter(pk=inputs['student-dropdown.value'])
        return students.distinct()
    else:
        raise NotImplementedError('User must be in teacher or studnet group')


def set_sittings(callback, user=User.objects.none()):
    if user.groups.filter(name='Teachers').count():
        sittings = Sitting.objects.all()
    elif user.groups.filter(name='Students').count():
        sittings = Sitting.objects.filter(group__students__user=user)
    else:
        raise NotImplementedError('User must be in teacher or studnet group')

    if 'time-chart.clickData' in callback.inputs:
        if  callback.inputs['time-chart.clickData']:
            sitting_pk = callback.inputs['time-chart.clickData']['points'][0]['customdata']
            sittings = sittings.filter(pk=sitting_pk)

    return sittings


def get_mistakes_from_graph(callback):
    mistakes = Mistake.objects.all()
    if 'mistakes-chart.clickData' in callback.inputs:
        if callback.inputs['mistakes-chart.clickData']:
            mistakes_pk = callback.inputs['mistake-chart.clickData']['points'][0]['customdata']
            mistakes = Mistake.objects.get(pk=mistakes_pk).get_descendants(include_self=True)

    return mistakes

def get_syllabus_point_from_graph(callback):
    root_pk = get_root_pk(callback)
    if not root_pk:
        return Syllabus.objects.filter(level=2)
    else:
        return Syllabus.objects.get(pk=root_pk)


def drop_mistake_columns(df, user):
    """
    Take a data frame of individual marks, and drop the apropriate columns depending
    on whether the use is a teacher or student.

    Teachers should retain the student names so they can be connected to individuals.
    Studnets will be logged into their own view, so don't need student names.
    :param df: dataframe from Mark queryset
    :param user: User instance from dash
    :return: dataframe with appropriate columsn removed.
    """

    if user.groups.filter(name='Students').count():
        df = df.drop(columns='student')

    return df

external_stylesheets=[dbc.themes.BOOTSTRAP]

# Get column headers for mistake table:
# This is necessay to make tests and an initial setup work,
# since we must have at least one mark to populate this field:
def initial_setup():
    setup_student = Student.objects.create()
    setup_exam = Exam.objects.create(name='setup')
    setup_question = Question.objects.create(exam=setup_exam,
                                             order=1,
                                             number='1',
                                             max_score=1
                                             )
    setup_mark=Mark.objects.create(student=setup_student,
                                   question=setup_question,
                                   score=1)
    init_df = read_frame(Mark.objects.filter(pk=Mark.objects.first().pk))

    # Now clean up created mark
    setup_student.delete()
    setup_exam.delete()
    setup_question.delete()
    setup_mark.delete()

app = DjangoDash('TeacherDashboard', external_stylesheets=external_stylesheets)
subject_options = [dict(label=subject.text, value=subject.pk) for subject in Syllabus.objects.filter(level=2)]

app.layout = html.Div([
    html.Div([
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
        ]), ]),
    html.Div([
        html.Div([
            html.H3('Syllabus Performance'),
            dcc.Loading(
                id="sullabus-graph-loading",
                type="default",
                children=dcc.Graph(id='syllabus-graph')
            ),
        ] ,className="six columns"),
        html.Div([
            html.H3('Mistakes'),
            dcc.Loading(
                id="mistake-chart-loading",
                type="default",
                children=dcc.Graph(id='mistake-chart')
            ),
            html.Button('Reset filter on this graph', id='time-chart-reset')
        ], className="six columns"),
    ], className='Row'),
    html.Div([
        html.Div([
            html.H3('Over Time'),
            dcc.Loading(
                id="time-chart-loading",
                type="default",
                children=dcc.Graph(id='time-chart')
            ),
            html.Button('Reset filter on this graph', id='time-chart-reset')
    ], className="six columns"),


    html.Div([
        html.H3('Group Performance'),
        dcc.Loading(
            id="group-performance-loading",
            type="default",
            children=dcc.Graph(id='group-chart')
        ),
        html.Button('Reset filter on this graph', id='group-performance-reset')
        ], className="six columns")
    ], className="row"),

    html.Div([
        html.H3('Mistakes list'),
        dcc.Loading(
            id="mistakes-table-loading",
            type="default",
            children=dash_table.DataTable(
                style_cell={
                        'whiteSpace': 'normal',
                        'height': 'auto',
                        'textAlign': 'left',
                        'font-family': 'sans-serif',
                    },
                id='mistakes-table'
            )
        )
    ])
])


app.css.append_css({
    'external_url': '/staticfiles/css/dash.css'
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
    if not subject_pk:
        return False
    # Check if the user has at some point filtered on the sunburst:
    if 'syllabus-graph.clickData' in callback.inputs:
        if callback.inputs['syllabus-graph.clickData']:
            subject_pk = callback.inputs['syllabus-graph.clickData']['points'][0]['customdata']

    return subject_pk


@app.expanded_callback(
    Output('syllabus-graph', 'figure'),
    [Input('subject-dropdown', 'value'),
     Input('teachinggroup-dropdown', 'value'),
     Input('student-dropdown', 'value'),
     Input('group-chart', 'clickData'),
     Input('time-chart', 'clickData'),
     ])
def update_syllabus_sunburst(*args, **kwargs):
    callback = kwargs['callback_context']
    user = kwargs['user']
    students = get_students_from_graph(callback, user)

    sittings = set_sittings(callback, user)

    parent_point_pk = get_root_pk(callback)
    if not parent_point_pk:
        return False
    parent_point = Syllabus.objects.get(pk=parent_point_pk)
    points = parent_point.get_descendants(include_self=True)
    labels = [point.text for point in points]
    ids = [point.pk for point in points]
    parents = [point.parent.text for point in points]
    parents[0] = ""
    values = [1 for point in points]
    colors = [point.cohort_stats(students, sittings)['rating'] for point in points]

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
    Output('mistake-chart', 'figure'),
    [Input('subject-dropdown', 'value'),
     Input('teachinggroup-dropdown', 'value'),
     Input('student-dropdown', 'value'),
     Input('syllabus-graph', 'clickData'),
     Input('group-chart', 'clickData'),
     Input('time-chart', 'clickData')])
def update_mistake_starburst(*args, **kwargs):
    callback = kwargs['callback_context']
    user = kwargs['user']
    subject_pk = callback.inputs['subject-dropdown.value']
    students = get_students_from_graph(callback, user)

    # Keep blank if we haven't loaded all charts yet.
    if not students:
        return False
    root_pk = get_root_pk(callback)
    if not root_pk:
        return False
    parent_point = Syllabus.objects.get(pk=root_pk)

    mistakes = Mistake.objects.all()
    sittings = set_sittings(callback, user)
    labels = [mistake.mistake_type for mistake in mistakes]
    ids = [mistake.pk for mistake in mistakes]
    parents = []
    for mistake in mistakes:
        if mistake.parent:
            parents.append(mistake.parent.mistake_type)
        else:
            parents.append("")

    parents[0] = ""
    values = [1 for mistake in mistakes]
    colors = [mistake.cohort_totals(students, parent_point.get_descendants(), sittings) for mistake in mistakes]
    graph = go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        customdata=ids,
        marker=dict(colors=colors,
                    colorscale='gnbu',
                    cmin=0),
        hovertemplate='<b>%{label}</b><br>Total Mistakes: %{color}',
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
     Input('teachinggroup-dropdown', 'value'),
     Input('student-dropdown', 'value'),
     Input('syllabus-graph', 'clickData'),
     Input('group-chart', 'clickData'),
     Input('time-chart', 'clickData')])
def update_rating_time_graph(*args, **kwargs):
    callback = kwargs['callback_context']
    user = kwargs['user']
    parent_pk = get_root_pk(callback)

    # Before subject is chosen this will be blank.
    if not parent_pk:
        return False
    parent_point = Syllabus.objects.get(pk=parent_pk)
    groups = get_groups_from_graph(callback, user)
    students = get_students_from_graph(callback, user)
    records = Sitting.objects.filter(exam__question__syllabus_points__in=parent_point.get_descendants(),
                                     group__in=groups,
                                     ).order_by('date').distinct()
    # text = [sitting.exam.name for sitting in records]
    # x = [sitting.date for sitting in records]
    # y = [sitting.avg_syllabus_rating(parent_point) for sitting in records]

    text = []
    x = []
    y = []
    ids = []

    for sitting in records:
        avg_score = sitting.avg_syllabus_rating(parent_point, students)
        if avg_score:
            if avg_score != 'none':
                string = str(sitting.group.name) + "<br>" + str(sitting.exam.name)
                text.append(string)
                x.append(sitting.date)
                y.append(avg_score)
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
            'title': 'Average student rating',
            'range': [0, 5]
        }
    )

    return {'data': [graph], 'layout': layout}


@app.expanded_callback(
    Output('group-chart', 'figure'),
    [Input('subject-dropdown', 'value'),
     Input('teachinggroup-dropdown', 'value'),
     Input('student-dropdown', 'value'),
     Input('syllabus-graph', 'clickData'),
     Input('time-chart', 'clickData'),
     Input('group-chart', 'clickData')])
def update_group_graph(*args, **kwargs):
    """ Update the group performance graph for interractions """


    # Filter out syllabus points
    callback = kwargs['callback_context']
    user = kwargs['user']
    if not get_root_pk(callback):
        return False
    parent_point = Syllabus.objects.get(pk=get_root_pk(callback))
    points = parent_point.get_descendants()

    ## Filter students
    # Check if we've filtered anything:
    groups = get_groups_from_graph(callback, user)
    students = get_students_from_graph(callback, user, groups)

    # Filter out sittings
    sittings = Sitting.objects.filter(exam__question__syllabus_points__in=parent_point.get_descendants()). \
        order_by('date').distinct()

    # Create the graphs
    if Input('group-students-by-classes', 'value'):
        # Spit out by-class graph
        pass

    else:
        # Spit out by-student graph
        pass

    y_0_1 = []
    y_1_2 = []
    y_2_3 = []
    y_3_4 = []
    y_4_5 = []
    names = []
    data = []
    customdata = []

    # If we only have one group, it's better to output individual students.
    if groups.count() == 1:
        group = groups[0]
        for student in students:
            student_qs = Student.objects.filter(pk=student.pk)
            names.append(student.full_name())
            y_0_1.append(group.ratings_pc_between_range(0, 1, sittings, student_qs, points))
            y_1_2.append(group.ratings_pc_between_range(1, 2, sittings, student_qs, points))
            y_2_3.append(group.ratings_pc_between_range(2, 3, sittings, student_qs, points))
            y_3_4.append(group.ratings_pc_between_range(3, 4, sittings, student_qs, points))
            y_4_5.append(group.ratings_pc_between_range(4, 5.1, sittings, student_qs,
                                                 points))  # Must do this to include 5.0 ratings
            customdata.append('student_' + str(student.pk))

    else:
        for group in groups:
            names.append(group.name)
            y_0_1.append(group.ratings_pc_between_range(0, 1, sittings, students, points))
            y_1_2.append(group.ratings_pc_between_range(1, 2, sittings, students, points))
            y_2_3.append(group.ratings_pc_between_range(2, 3, sittings, students, points))
            y_3_4.append(group.ratings_pc_between_range(3, 4, sittings, students, points))
            y_4_5.append(
                group.ratings_pc_between_range(4, 5.1, sittings, students, points))  # Must do this to include 5.0 ratings
            customdata.append('group_' + str(group.pk))

    # Create a bar for each level:
    data.append(go.Bar(name='0-1', x=names, y=y_0_1, customdata=customdata))
    data.append(go.Bar(name='1-2', x=names, y=y_1_2, customdata=customdata))
    data.append(go.Bar(name='2-3', x=names, y=y_2_3, customdata=customdata))
    data.append(go.Bar(name='3-4', x=names, y=y_3_4, customdata=customdata))
    data.append(go.Bar(name='4-5', x=names, y=y_4_5, customdata=customdata))

    figure = go.Figure(data=data)
    figure.update_layout(barmode='stack')
    return figure


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
    Output('mistakes-table', 'data'),
    [Input('subject-dropdown', 'value'),
     Input('teachinggroup-dropdown', 'value'),
     Input('student-dropdown', 'value'),
     Input('syllabus-graph', 'clickData'),
     Input('group-chart', 'clickData'),
     Input('time-chart', 'clickData'),
     Input('mistake-chart', 'clickData')]
    )
def update_mistakes_table(*args, **kwargs):
    callback = kwargs['callback_context']
    user = kwargs['user']
    parent_pk = get_root_pk(callback)

    # Before subject is chosen this will be blank.

    sittings = set_sittings(callback, user)
    students = get_students_from_graph(callback, user)
    mistakes = get_mistakes_from_graph(callback)
    syllabus = get_syllabus_point_from_graph(callback)

    notes_qs = Mark.objects.filter(student__in=students,

                                   sitting__in=sittings,
                                   question__syllabus_points__in=syllabus.get_descendants(include_self=True),
                                   student_notes__isnull=False).exclude(student_notes='').distinct()

    df = read_frame(notes_qs, fieldnames=['student', 'sitting__exam__name', 'student_notes'])
    df = drop_mistake_columns(df, user)
    data = df.to_dict('records')

    return data


@app.expanded_callback(
    Output('mistakes-table', 'columns'),
    [Input('url', 'pathname')]
    )
def update_mistakes_table_headings(*args, **kwargs):
    """
    This runs on first load, to dynamically set column headings depending
    on whether we have teacher or student.
    Teachers need to see student names; students only need to see the
    mistakes themselves.
    :param args:
    :param kwargs:
    :return: column dict as required by pandas
    """
    user = kwargs['user']

    init_df = read_frame(Mark.objects.filter(pk=Mark.objects.first().pk),
                         fieldnames=['student', 'sitting__exam__name', 'student_notes'])
    init_df = drop_mistake_columns(init_df, user)
    columns = [{"name": i, "id": i} for i in init_df.columns]
    return columns
