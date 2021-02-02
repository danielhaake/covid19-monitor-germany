# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import dash
import dash_bootstrap_components as dbc

from app_functions import *


# ----------------------------- DASH APP ------------------------------#

# GLOBAL STYLE SETTINGS
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'author',
                            'content': 'Daniel Haake (Data Collection, Data Preparation, Data Analysis & Visualisation)'
                                       ' & Christian Kirifidis (Visualisation)'}])


# ----------------------------- DASH APP LAYOUT ------------------------------#

app.layout = get_layout(app)


# UPDATE DATA

@app.callback(
    dash.dependencies.Output('tabs-global-overview', 'children'),
    [dash.dependencies.Input('graph-update', 'n_intervals')])
def update_graph_cases_mean_3(n):
    return get_tabs_with_graphs()

if __name__ == '__main__':
    app.run_server(debug=False)
