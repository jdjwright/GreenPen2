import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html

from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from django_plotly_dash import DjangoDash
from GreenPen.models import Syllabus, Student, Sitting, TeachingGroup, Mistake
from GreenPen.settings import CURRENT_ACADEMIC_YEAR


# Helper functions:

def get_groups_from_graph(callback):
    """
    Returns a queryset of groups from the callback.

    :param callback: The Plotly Dash callback

    :returns: A queryset of all groups from any click events on the graph
    """

    # If we're a student, only output themselves.


    # Start by finding our syllabus so we only get groups taught that syllabus:
    current_selected = Syllabus.objects.get(pk=get_root_pk(callback))
    # Groups to return
    groups = TeachingGroup.objects.filter(year_taught=CURRENT_ACADEMIC_YEAR,
                                          archived=False,
                                          syllabus__in=current_selected.get_ancestors(include_self=True))
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

    return groups


def get_students_from_graph(callback, groups=TeachingGroup.objects.filter(archived=False)):
    """
    Returns a queryset of students filtered by other chart callback.
    :param callback: the plotyl dash callback
    :return: A queryset of students
    """
    students = Student.objects.filter(teachinggroup__in=groups)
    if 'group-chart.clickData' not in callback.inputs:
        return students
    elif not callback.inputs['group-chart.clickData']:
        return students
    else:
        name = callback.inputs['group-chart.clickData']['points'][0]['customdata']
        if name.startswith('group_'):
            group_pk = name.split('_')[1]
            return students.filter(teachinggroup__pk=group_pk)
        else:
            student_pk = name.split('_')[1]
            return Student.objects.filter(pk=student_pk)


def set_sittings(callback):
    sittings = Sitting.objects.all()
    if 'time-chart.clickData' not in callback.inputs:
        return sittings
    elif not callback.inputs['time-chart.clickData']:
        return sittings

    else:
        sitting_pk = callback.inputs['time-chart.clickData']['points'][0]['customdata']
        sittings = Sitting.objects.filter(pk=sitting_pk)
    return sittings


external_stylesheets=[dbc.themes.BOOTSTRAP]

app = DjangoDash('TeacherDashboard', external_stylesheets=external_stylesheets)
subject_options = [dict(label=subject.text, value=subject.pk) for subject in Syllabus.objects.filter(level=2)]

app.layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='subject-dropdown',
            options=subject_options,
            value=2
        ), ]),
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

    # Check if the user has at some point filtered on the sunburst:
    if 'syllabus-graph.clickData' in callback.inputs:
        if callback.inputs['syllabus-graph.clickData']:
            subject_pk = callback.inputs['syllabus-graph.clickData']['points'][0]['customdata']

    return subject_pk


@app.expanded_callback(
    Output('syllabus-graph', 'figure'),
    [Input('subject-dropdown', 'value'),
     Input('group-chart', 'clickData'),
     Input('time-chart', 'clickData')
     ])
def update_syllabus_sunburst(*args, **kwargs):
    callback = kwargs['callback_context']

    subject_pk = callback.inputs['subject-dropdown.value']
    students = get_students_from_graph(callback)

    sittings = set_sittings(callback)

    parent_point = Syllabus.objects.get(pk=subject_pk)
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
     Input('syllabus-graph', 'clickData'),
     Input('group-chart', 'clickData'),
     Input('time-chart', 'clickData')])
def update_mistake_starburst(*args, **kwargs):
    callback = kwargs['callback_context']

    subject_pk = callback.inputs['subject-dropdown.value']
    students = get_students_from_graph(callback)
    parent_point = Syllabus.objects.get(pk=get_root_pk(callback))
    mistakes = Mistake.objects.all()
    sittings = set_sittings(callback)
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
                    cmid=2.5,
                    cmax=5,
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
     Input('syllabus-graph', 'clickData'),
     Input('group-chart', 'clickData'),
     Input('time-chart', 'clickData')])
def update_rating_time_graph(*args, **kwargs):
    callback = kwargs['callback_context']
    parent_pk = get_root_pk(callback)
    parent_point = Syllabus.objects.get(pk=parent_pk)
    groups = get_groups_from_graph(callback)
    students = get_students_from_graph(callback)
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
        if sitting.avg_syllabus_rating(parent_point) != 'none':
            string = str(sitting.group.name) + "<br>" + str(sitting.exam.name)
            text.append(string)
            x.append(sitting.date)
            y.append(sitting.avg_syllabus_rating(parent_point))
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
     Input('syllabus-graph', 'clickData'),
     Input('time-chart', 'clickData'),
     Input('group-chart', 'clickData')])
def update_group_graph(*args, **kwargs):
    """ Update the group performance graph for interractions """


    # Filter out syllabus points
    callback = kwargs['callback_context']

    # If we've clicked the reset, remove the clickData input for this:
    if callback:
        pass
    parent_point = Syllabus.objects.get(pk=get_root_pk(callback))
    points = parent_point.get_descendants()

    ## Filter students
    # Check if we've filtered anything:
    groups = get_groups_from_graph(callback)
    students = Student.objects.filter(teachinggroup__in=groups)

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
        students = groups[0].students.all()
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
