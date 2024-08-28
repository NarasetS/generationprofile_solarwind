import cdsapi
import atlite   

# c = cdsapi.Client()

# c.retrieve(
#     'reanalysis-era5-land',
#     {
#         'variable': [
#             '2m_temperature', 'surface_net_solar_radiation',
#         ],
#         'year': '2022',
#         'month': '01',
#         'day': '01',
#         'time': [
#             '00:00', '01:00', '02:00',
#             '03:00', '04:00', '05:00',
#             '06:00', '07:00', '08:00',
#             '09:00', '10:00', '11:00',
#             '12:00', '13:00', '14:00',
#             '15:00', '16:00', '17:00',
#             '18:00', '19:00', '20:00',
#             '21:00', '22:00', '23:00',
#         ],
#         'area': [
#             90, -180, -90,
#             180,
#         ],
#         'format': 'netcdf',
#     },
#     'download.nc')

cutout = atlite.Cutout(
    path="test.nc",
    module="era5",
    x=slice(-13.6913, 1.7712),
    y=slice(49.9096, 60.8479),
    time="2022-01-01",
)