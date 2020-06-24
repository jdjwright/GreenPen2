import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from django_plotly_dash import DjangoDash
from GreenPen.models import Syllabus, Student, Sitting

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = DjangoDash('SyllabusExample', external_stylesheets=external_stylesheets)
subject_options = [dict(label=subject.text, value=subject.pk) for subject in Syllabus.objects.filter(level=2)]

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='syllabus-graph', animate=True),
        dcc.Dropdown(
            id='subject-dropdown',
            options=subject_options,
            value=2
        )],
    ),
    html.Div([
        html.H3('Over time'),
        dcc.Graph(id='time-chart')
    ])
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


def get_root_pk(callback):
    if len(callback.triggered):
        if 'syllabus-graph.clickData' in callback.triggered[0]['prop_id']:
            pk_clicked = callback.inputs['syllabus-graph.clickData']['points'][0]['customdata']
            # Test if we've cliekd the centre point (go back)
            if callback.triggered[0]['value']['points'][0]['pointNumber'] == 0:

                # Check if it's the root from the subject dropdown box:
                if pk_clicked == callback.inputs['subject-dropdown.value']:
                    subject_pk = pk_clicked
                else:
                    subject_pk = Syllabus.objects.get(pk=pk_clicked).parent.pk

            # Not clicking the parent, so just use the pk we clicked
            else:
                subject_pk = pk_clicked

        if 'subject-dropdown.value' in callback.triggered[0]['prop_id']:
            subject_pk = callback.inputs['subject-dropdown.value']

    else:
        subject_pk = callback.inputs['subject-dropdown.value']

    return subject_pk


@app.expanded_callback(
    Output('syllabus-graph', 'figure'),
    [Input('subject-dropdown', 'value'),
     Input('syllabus-graph', 'clickData')])
def display_value(*args, **kwargs):
    callback = kwargs['callback_context']

    subject_pk = get_root_pk(callback)
    students = Student.objects.all()
    parent_point = Syllabus.objects.get(pk=subject_pk)
    points = parent_point.get_descendants(include_self=True).filter(level__lte=parent_point.level+2)
    labels = [point.text for point in points]
    ids = [point.pk for point in points]
    parents = [point.parent.text for point in points]
    parents[0] = ""
    values = [point.cohort_stats(students)['rating'] for point in points]

    graph = go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        customdata=ids,
        marker=dict(colors=values,
                    colorscale='RdYlGn',
                    cmid=2.5,
                    cmax=5,
                    cmin=0),
        hovertemplate='<b>%{label}</b><br>Average rating: %{value}',
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
     Input('syllabus-graph', 'clickData')])
def display_value(*args, **kwargs):
    callback = kwargs['callback_context']
    parent_pk = get_root_pk(callback)
    parent_point = Syllabus.objects.get(pk=parent_pk)

    records = Sitting.objects.filter(exam__question__syllabus_points__in=parent_point.get_descendants()).order_by('date')
    labels = [sitting.exam.name for sitting in records]
    x = [sitting.date for sitting in records]
    y = [sitting.avg_syllabus_rating(parent_point) for sitting in records]

    graph = go.Scatter(
        x=x,
        y=y

    )
    layout = go.Layout(


    )

    return {'data': [graph], 'layout': layout}
