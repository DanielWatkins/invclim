"""Sets up the station list the rest of the code depends on. 
From the IGRA2 station list, stations with data extending from before 2000 to past 2019 
are selected. Name style is cleaned up and fixed. Time zones are added.

Next, soundings matching the names in the station list are read in from
the files in the folder Data/IGRA2_Derived. It is expected that the soundings
have already been downloaded using siphon.simplewebservice.igra2.

The soundings are used to then count the number of existing

"""
import pandas as pd
import numpy as np

station_list = pd.read_fwf('../igra2-station-list.txt',
                          header=None)
station_list.columns = ['station_id', 'lat', 'lon', 'elevation', 'name', 'start_year', 'end_year', 'count']
station_list = station_list.loc[(station_list.lat >= 65) & (station_list.end_year >= 2020)]
station_list = station_list.loc[station_list.start_year <= 2000]

station_list.set_index('station_id', inplace=True)

# Drop columns that we're not using
station_list = station_list.loc[:, ['name', 'lat', 'lon', 'elevation']]

# Remove 'UA' from Canada/US names
for name in station_list.name:
    if name.split(' ')[-1] == 'UA':
        station_list.loc[station_list.name == name, 'name'] = ' '.join(name.split(' ')[:-1])

station_list['name'] = [name.title() for name in station_list.name]

# Adjust spelling of names and add special characters
name_adjust = {
    'USM00070026': 'Utqiaġvik',
    'RSM00023205': 'Naryan-Mar',
    'SVM00001004': 'Ny-Ålesund',
    'FIM00002836': 'Sodankylä',
    'RSM00023078': 'Norilsk',
    'RSM00021946': 'Chokurdakh',
    'GLM00004360': 'Tasiilaq',
    'RSM00023330': 'Salekhard',
    'RSM00023472': 'Turukhansk',
    'GLM00004220': 'Aasiaat'
}
for name in name_adjust:
    station_list.loc[name, 'name'] = name_adjust[name]


# actual time zones
actual_time_zones = {
     'CAM00071043': -7, 
     'CAM00071081': -5, 
     'CAM00071082': -5, 
     'CAM00071917': -6,
     'CAM00071924': -6, 
     'CAM00071925': -7, 
     'CAM00071957': -7, 
     'FIM00002836': 2,
     'GLM00004220': -3,
     'GLM00004320': 0,
     'GLM00004339': -1,
     'GLM00004360': -3, 
     'ICM00004089': 0,
     'JNM00001001': 1,
     'RSM00021824': 9, 
     'RSM00021946': 11,
     'RSM00022217': 3, 
     'RSM00023078': 7,
     'RSM00023205': 3, 
     'RSM00023330': 5,
     'RSM00023472': 7,
     'RSM00024266': 10,
     'RSM00024343': 9,
     'SVM00001004': 1,
     'SVM00001028': 1, 
     'USM00070026': -9,
     'USM00070133': -9}

station_list['time_zone'] = 0
for site in actual_time_zones:
    station_list.loc[site, 'time_zone'] = actual_time_zones[site]

station_list['local_time_00Z'] = (station_list.time_zone) % 24
station_list['local_time_12Z'] = (station_list.time_zone + 12) % 24
station_list['local_time_00Z'] = [str(t) + ':00' for t in station_list.local_time_00Z]
station_list['local_time_12Z'] = [str(t) + ':00' for t in station_list.local_time_12Z]

station_list['lat'] = np.round(station_list.lat, 1)
station_list['lon'] = np.round(station_list.lon, 1)
station_list['elevation'] = np.round(station_list.elevation).astype(int)
station_list.sort_values('lon', inplace=True)

station_list.loc[:, 'region'] = np.nan
for site in station_list.index:
    if site[0] in ['U', 'C']:
        station_list.loc[site, 'region'] = 'North America'
    elif site[0] == 'G':
        station_list.loc[site, 'region'] = 'Greenland'
    elif site[0] in ['J', 'S']:
        station_list.loc[site, 'region'] = 'North Atlantic'
    elif site[0] in ['F', 'R']:
        station_list.loc[site, 'region'] = 'Eurasia'



soundings = {}
for site in station_list.index:
    try:
        soundings[site] = pd.read_csv('../Data/IGRA2_Derived/' + site + '-igra2-derived.csv')
        soundings[site]['date'] = pd.to_datetime(soundings[site].date.values)
        soundings[site] = soundings[site].loc[soundings[site].pressure >= 500]
        soundings[site] = soundings[site].loc[(soundings[site].date.dt.year >= 2000) 
                                              & (soundings[site].date.dt.year < 2020)]
    except:
        print('Missing sounding data for ' + site)
        
pressure_resolution = {}
for site in soundings:
    daily = soundings[site].groupby('date').count().pressure
    pressure_resolution[site] = daily.resample('1MS').mean()

nlevels = pd.DataFrame(pressure_resolution).mean(axis=0).round(0).astype(int)
station_list.loc[:,'n_levels'] = np.nan

for site in station_list.index:
    station_list.loc[site, 'n_levels'] = nlevels[site]
station_list['n_levels'] = station_list['n_levels'].astype(int)

# select only levels below 500
# select only times with hour 23, 0, 1 or 11, 12, 13
station_list.loc[:,'n00Z'] = np.nan
station_list.loc[:,'n12Z'] = np.nan
for site in station_list.index:
    hours = np.array([name.hour for name, group in soundings[site].groupby('date')])
    sel_idx_00 = (hours == 23) | (hours < 2) 
    sel_idx_12 = (hours > 10) & (hours < 14)
    station_list.loc[site,'n12Z'] = np.sum(sel_idx_12)
    station_list.loc[site,'n00Z'] = np.sum(sel_idx_00)
    
station_list['n00Z'] = station_list['n00Z'].astype(int)
station_list['n12Z'] = station_list['n12Z'].astype(int)

# The number 7305 is the number of days from Jan 1, 2000 to Dec 31, 2019
station_list.loc[(station_list.n00Z/7305 > 0.75) | (station_list.n12Z/7305 > 0.75)].to_csv('../Data/arctic_stations.csv')

