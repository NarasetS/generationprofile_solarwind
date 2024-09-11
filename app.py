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
    html.Header('Draw the area of interest'),
    html.Br(),
    html.Button("Remove -> Clear all", id="clear_all"),
    html.Button("Extract data", id= "extract_data"),
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
    dl.Map(center=[14, 100], zoom=8, children=[
        dl.TileLayer(), 
        dl.FeatureGroup([
            dl.EditControl(id="edit_control")]),
        dl.GeoJSON(id='geojson'),
        dl.GeoJSON(id='geojson-2'),
    ], style={'width': '50%', 'height': '90vh', "display": "inline-block"}, id="map"),
    dag.AgGrid(
            id="export-data-grid",
            columnSize="sizeToFit",
            columnDefs=columnDefs,
            rowData=df.to_dict("records"),
            csvExportParams={
                "fileName": "ag_grid_test.csv",
            },
    )

])

# Copy data from the edit control to the geojson component.
@app.callback(Output("geojson", "data"), Input("edit_control", "geojson"))
def mirror(x):
    return x

# Upload input file
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

@app.callback(
            Output("geojson-2", "data"),
            Input('upload-data', 'contents'),
            State('upload-data', 'filename')
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

# Acquire state of input and extract data
@app.callback(Input("extract_data", "n_clicks"),State("geojson", "data"),State("geojson-2", "data"))
def trigger_extract_data(n_clicks,geojsondata,geojsondata2):
    ####### get the data ########

    ####### prepare output file #####
    return print(geojsondata,geojsondata2) 

# Trigger mode (edit) + action (remove all)
@app.callback(Output("edit_control", "editToolbar"), Input("clear_all", "n_clicks"))
def trigger_action(n_clicks):
    return dict(mode="remove", action="clear all", n_clicks=n_clicks)  # include n_click to ensure prop changes

if __name__ == '__main__':
    app.run_server()