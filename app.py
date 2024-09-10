import dash_leaflet as dl
from dash import Dash, html, Output, Input, State
from dash.exceptions import PreventUpdate
from dash_extensions.javascript import assign

# Create example app.
app = Dash(prevent_initial_callbacks=True)
app.layout = html.Div([
    # Setup a map with the edit control.
    html.Header('Draw the area of interest'),
    html.Br(),
    html.Button("Remove -> Clear all", id="clear_all"),
    html.Button("Extract data", id= "extract_data"),
    html.Br(),
    dl.Map(center=[14, 100], zoom=8, children=[
        dl.TileLayer(), 
        dl.FeatureGroup([
            dl.EditControl(id="edit_control")]),
        dl.GeoJSON(id='geojson'),
    ], style={'width': '50%', 'height': '90vh', "display": "inline-block"}, id="map"),
])

# Copy data from the edit control to the geojson component.
@app.callback(Output("geojson", "data"), Input("edit_control", "geojson"))
def mirror(x):
    return x

# Trigger mode (edit) + action (remove all)
@app.callback(Output("edit_control", "editToolbar"), Input("clear_all", "n_clicks"))
def trigger_action(n_clicks):
    return dict(mode="remove", action="clear all", n_clicks=n_clicks)  # include n_click to ensure prop changes

@app.callback(Input("extract_data", "n_clicks"),State("geojson", "data"))
def trigger_extract_data(n_clicks,value):
    return print(value)


if __name__ == '__main__':
    app.run_server()