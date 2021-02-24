# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import dash
import dash_bootstrap_components as dbc
from flask_caching import Cache

from app_layout import *


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
app.layout = layout.layout()

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


# Path for health check
@app.server.route("/ping")
def ping():
  return "{status: ok}"


if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=False)
