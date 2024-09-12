import dash_leaflet as dl
from dash import Dash, html, Output, Input, State
from dash.exceptions import PreventUpdate
from dash_extensions.javascript import assign
import dash_core_components as dcc
import dash_ag_grid as dag
import geopandas as gpd
import geojson
import pandas as pd
import base64
import io
from shapely import wkt

# Create example app.
app = Dash(prevent_initial_callbacks=True)
app.layout = html.Div([
    # Setup a map with the edit control.
    html.Header('Draw the area of interest or just dump a file in the box below'),
    html.Br(),
    html.Button("Remove -> Clear all", id="clear_all"),
    dcc.Upload(
                id="upload-data",
                children=html.Div(["Drag and drop a file"]),
                style={
                    "width": "10%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                },
                multiple=True,
            ),
    dcc.Dropdown(['Solar', 'Wind'], 'Solar', id='planttype-dropdown'),
    dcc.Dropdown([i for i in range(2002,2021,1)], 2002, id='yearstart-dropdown'),
    dcc.Dropdown([i for i in range(2020,2001,-1)], 2020, id='yearend-dropdown'),
    html.Br(),
    html.Button("Extract data", id= "extract_data"),
    dcc.Download(id="download-dataframe-csv"),
    html.Br(),
    html.Br(),
    dl.Map(center=[14, 100], zoom=8, children=[
        dl.TileLayer(), 
        dl.FeatureGroup([
            dl.EditControl(id="edit_control")]),
        dl.GeoJSON(id='geojson'),
        dl.GeoJSON(id='geojson-2'),
    ], style={'width': '80%', 'height': '90vh', "display": "inline-block"}, id="map"),


])
#####################################################

# Copy data from the edit control to the geojson component.
@app.callback(Output("geojson", "data"), Input("edit_control", "geojson"))
def mirror(x):
    return x
#####################################################

########## Upload input file
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return df
#####################################################

#####################################################
@app.callback(
            Output("geojson-2", "data"),
            Input('upload-data', 'contents'),
            State('upload-data', 'filename'),
            State('planttype-dropdown', 'value'),
            State('yearstart-dropdown', 'value'),
            State('yearend-dropdown', 'value'),
)
def update_output(list_of_contents, list_of_names):
        if list_of_contents is not None:
            children = [
                parse_contents(c, n) for c, n in
                zip(list_of_contents, list_of_names)]
        try : 
            children[0]['geometry'] = children[0]['geometry'].apply(wkt.loads)
            data_geopandas = gpd.GeoDataFrame(children[0],crs="EPSG:4326")
            data_geopandas = data_geopandas.set_geometry('geometry')
            data_geojson = geojson.loads(data_geopandas.to_json())
        except:
            data_geojson = None
        return data_geojson       
#####################################################

######## Acquire state of input and extract data ###### 
@app.callback(
        Output("download-dataframe-csv", "data"),
        Input("extract_data", "n_clicks"),
        State("geojson", "data"),
        State("geojson-2", "data"),

        prevent_initial_call=True
        )
def trigger_extract_data(n_clicks,geojsondata,geojsondata2,planttype,yearstart,yearend):
    ####### Merge geojson from several sources to create geodataframe ########
    # df = pd.DataFrame({"a": [1, 2, 3, 4], "b": [2, 1, 5, 6], "c": ["x", "x", "y", "y"]})
    

    ####### Loop through year start to year end, Create cutout and extract generation profile for each year #####

    ####### Build up output dataframe with location name in the column and timestampe along the rows ######

    ####### prepare output file #####
    return dcc.send_data_frame(output.to_csv, "output.csv")
#####################################################

# Trigger mode (edit) + action (remove all)
@app.callback(Output("edit_control", "editToolbar"), Input("clear_all", "n_clicks"))
def trigger_action(n_clicks):
    return dict(mode="remove", action="clear all", n_clicks=n_clicks)  # include n_click to ensure prop changes
#####################################################


if __name__ == '__main__':
    app.run_server()