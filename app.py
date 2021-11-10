# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import dash
from flask_caching import Cache

from layout.app_layout import *


# ----------------------------- DASH APP ------------------------------#

# GLOBAL STYLE SETTINGS
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'author',
                            'content': 'Daniel Haake (Dashboard Application, Data Collection, Data Preparation, '
                                       'Data Analysis & Visualization) '
                                       '& Christian Kirifidis (Dashboard Application & Visualization)'}])

app.title = 'COVID-19 Monitor Germany'
layout = Layout()
app.layout = layout.layout

server = app.server  # important for using with gunicorn

cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple'
})

timeout = 600  # seconds


# Reloading graphs to get graphs with new data
@app.callback(
    dash.dependencies.Output('tabs-global-overview', 'children'),
    [dash.dependencies.Input('graph-update', 'n_intervals')])
@cache.memoize(timeout=timeout)
def update_tabs_with_graphs(n):
    return layout.tabs_with_graphs()


@app.callback(
    dash.dependencies.Output('graph-fig-median_ages', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-median-and-mean-ages', component_property='value')])
def build_graph(value):
    if value == 'median-ages':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-mean_ages', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-median-and-mean-ages', component_property='value')])
def build_graph(value):
    if value == 'mean-ages':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-hospitalizations-per-age-group-bar-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-hospitalizations-per-age-group', component_property='value')])
def build_graph(value):
    if value == 'hospitalizations-per-age-group-stacked-bar':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-hospitalizations-per-age-group-line-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-hospitalizations-per-age-group', component_property='value')])
def build_graph(value):
    if value == 'hospitalizations-per-age-group-line-plot':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-cases-per-outbreak-bar-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-cases-per-outbreak', component_property='value')])
def build_graph(value):
    if value == 'cases-per-outbreak-stacked-bar':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-cases-per-outbreak-in-percent-bar-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-cases-per-outbreak', component_property='value')])
def build_graph(value):
    if value == 'cases-in-percent-per-outbreak-stacked-bar':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-cases-per-outbreak-line-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-cases-per-outbreak', component_property='value')])
def build_graph(value):
    if value == 'cases-per-outbreak-line-plot':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-cases-per-outbreak-in-percent-line-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-cases-per-outbreak', component_property='value')])
def build_graph(value):
    if value == 'cases-in-percent-per-outbreak-line-plot':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-deaths-by-week-and-age-group-bar-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-deaths-by-week-of-death-and-age-group', component_property='value')])
def build_graph(value):
    if value == 'deaths-by-week-of-death-and-age-group-stacked-bar':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-deaths-by-week-and-age-group-line-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-deaths-by-week-of-death-and-age-group', component_property='value')])
def build_graph(value):
    if value == 'deaths-by-week-of-death-and-age-group-line-plot':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-deaths-in-percent-by-week-and-age-group-bar-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-deaths-by-week-of-death-and-age-group', component_property='value')])
def build_graph(value):
    if value == 'deaths-in-percent-by-week-of-death-and-age-group-stacked-bar':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('graph-fig-deaths-in-percent-by-week-and-age-group-line-plot', 'style'),
    [dash.dependencies.Input(component_id='radio-items-for-deaths-by-week-of-death-and-age-group', component_property='value')])
def build_graph(value):
    if value == 'deaths-in-percent-by-week-of-death-and-age-group-line-plot':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


# Path for health check
@app.server.route("/ping")
def ping():
  return "{status: ok}"


if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=False)
