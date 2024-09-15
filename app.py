import dash_leaflet as dl
from dash import Dash, html, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import geopandas as gpd
import geojson
import pandas as pd
import base64
import io
from shapely import wkt
from geojson import Feature, Point, FeatureCollection
import cdsapi
import atlite   
import cartopy.io.shapereader as shpreader
import datetime as dt
from datetime import timedelta, date

# Create example app.
app = Dash(prevent_initial_callbacks=True)
app.layout = html.Div([
    # Setup a map with the edit control.
    html.H1('This work revoles around Atlite library and CDS Data store api. API key and url (as "cds_api.txt" and follow cds_api_modify_guide.txt in the directory) are needed to process further.'),
    html.Header('Draw the area of interest or just dump a file in the box below (check file format in the directory "drop_file_format.csv")'),
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
    html.Header('Select Plant Type'),
    dcc.Dropdown(['Solar', 'Wind'], 'Solar', id='planttype-dropdown'),

    html.Header('Select Year'),
    dcc.Dropdown([i for i in range(1951,2024,1)], 2020, id='year-dropdown'),

    html.Header('Grid size (x*y)'),
    dcc.Dropdown([0.25,0.1,0.05,0.01], 0.1, id='gridsize-dropdown'),

    html.Header('Select UTC Adjustment'),
    dcc.Dropdown([i for i in range(-14,12,1)], 7, id='utc-dropdown'),

    html.Br(),
    html.Button("Extract data", id= "extract_data"),
    html.Header('After pressing "Extract Data", It will start checking the data stored in CDS_Data folder.(download if absent, from CDS data store)'),
    html.Header('The processing time would relatively dependent on grid size.'),
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
def createdatelist(year):
    if year%4 == 0:
        numberofdaysinyear = 366
    else: numberofdaysinyear = 365

    start_date = date(year-1, 12, 31)
    date_list = [(start_date+timedelta(hours=24*i)).strftime('%Y-%m-%d') for i in range(numberofdaysinyear+1)]
    ### create  date_list ####
    return date_list

@app.callback(
        Output("download-dataframe-csv", "data"),
        Input("extract_data", "n_clicks"),
        State("geojson", "data"),
        State("geojson-2", "data"),
        State('planttype-dropdown', 'value'),
        State('year-dropdown', 'value'),
        State('utc-dropdown','value'),
        State('gridsize-dropdown','value'),
        prevent_initial_call=True
        )
def trigger_extract_data(n_clicks,geojsondata,geojsondata2,planttype,year,utc,gridsize):
    ####### Create cutout and extract generation profile for each year #####
    shpfilename = shpreader.natural_earth(
        resolution="10m", category="cultural", name="admin_0_countries"
    )
    reader = shpreader.Reader(shpfilename)
    th = gpd.GeoSeries(
        {r.attributes["NAME_EN"]: r.geometry for r in reader.records()},
        crs={"init": "epsg:4326"},
    ).reindex(["Thailand"])

   ####### Merge geojson from several sources to create geodataframe ########
    try :  
        gpd_1 = gpd.GeoDataFrame.from_features(geojsondata)
        gpd_1 = gpd_1.geometry
        gpd_1 = gpd_1.reset_index()
        gpd_1 = gpd_1.rename(columns ={'index' : 'name'})
    except:
        gpd_1 = gpd.GeoDataFrame()
    try :    
        gpd_2 = gpd.GeoDataFrame.from_features(geojsondata2)
        gpd_2 = gpd_2.drop(columns=['cluster','id'])
    except:
        gpd_2 = gpd.GeoDataFrame()
    gpd_data = gpd.GeoDataFrame( pd.concat([gpd_1,gpd_2], ignore_index=True))
    gpd_data = gpd_data.set_geometry('geometry')
    gpd_data = gpd_data.set_crs(epsg=4326)
    gpd_data['center'] = gpd_data['geometry'].centroid
    gpd_data = gpd_data.set_geometry('center')
    gpd_data = gpd_data.drop(columns='geometry')
    gpd_data['x'] = gpd_data.geometry.x
    gpd_data['y'] = gpd_data.geometry.y
    gpd_data = gpd_data.drop(columns='center')
    gpd_data = gpd_data.set_index('name')

    ##### loop through date list #####
    output = pd.DataFrame()
    for i in createdatelist(year) :
        path = 'CDS_Data/' + str(i) +'_'+str(gridsize)+ ".nc"
        print(path)
        cutout = atlite.Cutout(
            path=path,
            module="era5",
            bounds= th.unary_union.bounds,
            time= i,
            dt = 'h',
            dx = gridsize, 
            dy = gridsize,
        )
        # This is where all the work happens (this can take some time, for us it took ~15 minutes).
        cutout.prepare(['height', 'wind', 'influx', 'temperature'])
        cells = cutout.grid
        nearest = cutout.data.sel({"x": gpd_data.x.values, "y": gpd_data.y.values}, "nearest").coords
        gpd_data["x"] = nearest.get("x").values
        gpd_data["y"] = nearest.get("y").values
        cells_generation = gpd_data.merge(cells, how="inner").rename(pd.Series(gpd_data.index))

        if planttype == 'Solar' :
                power_generation = cutout.pv(    
                    panel="CSi",
                    orientation="latitude_optimal",
                    capacity_factor=True,
                    tracking= None,
                    shapes=cells_generation.geometry
                ) 

        if planttype == 'Wind' :
                power_generation = cutout.wind(
                    turbine="Vestas_V112_3MW", 
                    capacity_factor=True,
                    shapes=cells_generation.geometry,
                    )
        else : None
        output_buffer = power_generation.to_pandas()
        output = pd.concat([output,output_buffer])

    # output = power_generation.to_pandas()
    output.reset_index(inplace = True)
    output['time_utcadj'] =  output['time'] + timedelta(hours=utc)
    output = output.drop(columns = 'time')
    output = output.loc[output['time_utcadj'].dt.year == year]
    output = output.set_index('time_utcadj')
    ####### prepare output file #####
    return  dcc.send_data_frame(output.to_csv, "output_"+str(planttype)+"_"+str(year)+"_"+str(gridsize)+".csv") #print(power_generation.to_pandas()) 
#####################################################

# Trigger mode (edit) + action (remove all)
@app.callback(Output("edit_control", "editToolbar"), Input("clear_all", "n_clicks"))
def trigger_action(n_clicks):
    return dict(mode="remove", action="clear all", n_clicks=n_clicks)  # include n_click to ensure prop changes
#####################################################


if __name__ == '__main__':
    app.run_server()