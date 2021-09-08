"""Sets up the station list the rest of the code depends on. 
From the IGRA2 station list, stations with data extending from before 2000 to past 2019 
are selected. Name style is cleaned up and fixed. Time zones are added.

Next, soundings matching the names in the station list are read in from
the files in the folder Data/IGRA2_Derived. It is expected that the soundings
have already been downloaded using siphon.simplewebservice.igra2 and placed 
into Data/Soundings/

Soundings are next read in, data below 500 hPa is selected, and the average number of levels
is computed and added to the stations dataframe.
"""
import pandas as pd
import numpy as np

station_list = pd.read_fwf('../Data/igra2-station-list.txt',
                          header=None)
station_list.columns = ['station_id', 'lat', 'lon', 'elevation', 'name', 'start_year', 'end_year', 'count']
# Include all stations north of 65 + Fairbanks
station_list = station_list.loc[(station_list.lat >= 64) | (station_list.station_id == 'USM00070261')]
# Include only stations that extend from pre-2000 to post-2019, except add Geosummit
station_list = station_list.loc[((station_list.start_year <= 2000) & (station_list.end_year >= 2019)) | (station_list.station_id == 'GLM00004417')]

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
    'GLM00004220': 'Aasiaat',
    'USM00070261': 'Fairbanks'
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
     'GLM00004417': -3,
     'GLM00004360': -3, 
     'ICM00004089': 0,
     'JNM00001001': 1,
     'RSM00021824': 9, 
     'RSM00021946': 11,
     'RSM00022217': 3, 
     'RSM00023078': 7, # Norislk
     'RSM00023205': 3, # Naryan-Mar
     'RSM00023415': 3, # Pechora
     'RSM00020744': 3, # Malye Karmakuly
     'RSM00022271': 3, # Shojna
     'RSM00023330': 5,
     'RSM00023472': 7,
     'RSM00024266': 10,
     'RSM00024343': 9,
     'RSM00025123': 11,
     'SVM00001004': 1,
     'SVM00001028': 1, 
     'USM00070026': -9,
     'USM00070261': -9,
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
    elif site[0] in ['J']:
        station_list.loc[site, 'region'] = 'Maritime'
    elif site[0:2] == 'SV':
        station_list.loc[site, 'region'] = 'Maritime'

station_list.loc[station_list.lon < -62, 'region'] = 'Eastern North America'
station_list.loc[station_list.lon < -126, 'region'] = 'Western North America'

station_list.loc[(station_list.lon > 22) & (station_list.lon < 80), 'region'] = 'Western Eurasia'
station_list.loc[station_list.lon > 80, 'region'] = 'Eastern Eurasia'

station_list.loc[station_list.index == 'RSM00020744', 'region'] = 'Maritime'

# Save preliminary
station_list.to_csv('../Data/arctic_stations_long.csv')

soundings = {}
for site in station_list.index:
    try:
        soundings[site] = pd.read_csv('../Data/Soundings/' + site + '-cleaned-soundings.csv')
        soundings[site]['date'] = pd.to_datetime(soundings[site].date.values)
        soundings[site] = soundings[site].loc[(soundings[site].date >= pd.to_datetime('2000-01-01 00:00')) &
                                             (soundings[site].date <= pd.to_datetime('2019-12-31 23:00'))]
    except:
        print('Missing sounding data for ' + site)
        
pressure_resolution = {}
for site in soundings:
    daily = soundings[site].groupby('date').count().pressure
    pressure_resolution[site] = daily.resample('1MS').mean()

nlevels = pd.DataFrame(pressure_resolution).mean(axis=0).round(0).astype(int)
station_list.loc[:,'n_levels'] = np.nan

for site in station_list.index:
    if site in nlevels:
        station_list.loc[site, 'n_levels'] = nlevels[site]
station_list['n_levels'].fillna(0, inplace=True)
station_list['n_levels'] = station_list['n_levels'].astype(int)

# select only levels below 500
# select only times with hour 23, 0, 1 or 11, 12, 13
station_list.loc[:,'n00Z'] = np.nan
station_list.loc[:,'n12Z'] = np.nan
sounding_counts = {}
for site in station_list.index:
    if site in soundings:
        sounding_counts[site] = soundings[site].groupby('date').count().pressure.resample('1MS').count()
        hours = np.array([name.hour for name, group in soundings[site].groupby('date')])
        sel_idx_00 = (hours == 23) | (hours < 2) 
        sel_idx_12 = (hours > 10) & (hours < 14)
        station_list.loc[site,'n12Z'] = np.sum(sel_idx_12)
        station_list.loc[site,'n00Z'] = np.sum(sel_idx_00)

sounding_counts = (pd.DataFrame(sounding_counts).fillna(0) == 0)
station_list.fillna(0, inplace=True)
station_list['n00Z'] = station_list['n00Z'].astype(int)
station_list['n12Z'] = station_list['n12Z'].astype(int)
station_list['n_missing_months'] = sounding_counts.sum(axis=0)
station_list['n_missing_months_post_2005'] = sounding_counts.loc[sounding_counts.index >= pd.to_datetime('2005-01-01')].sum(axis=0)

station_list['begin_date'] = pd.to_datetime('2000-01-01 00:00')
station_list['end_date'] = pd.to_datetime('2019-12-31 23:00')
for site in station_list.index:
    if site[0] == 'R':
        station_list.loc[site, 'begin_date'] = pd.to_datetime('2005-01-01 00:00')
    if site == 'GLM00004417':
        station_list.loc[site, 'begin_date'] = pd.to_datetime('2012-01-01 00:00')
begin_dates = {        
'RSM00022217': '2000-06-01',
'RSM00022522': '2009-04-01',
'RSM00022543': '2000-11-01',
'RSM00022271': '2005-07-01',
'RSM00020744': '2006-02-01',
'RSM00023205': '2005-01-01',
'RSM00023415': '2005-02-01',
'RSM00020046': '2009-01-01',
'RSM00023330': '2000-08-01',
'RSM00020674': '2005-11-01',
'RSM00023472': '2000-11-01',
'RSM00023078': '2000-04-01',
'RSM00024507': '2003-02-01',
'RSM00020292': '2011-01-01',
'RSM00024343': '2005-04-01',
'RSM00021824': '2005-04-01',
'RSM00024266': '2000-02-01',
'RSM00021432': '2011-01-01',
'RSM00021946': '2005-04-01',
'RSM00025428': '2007-06-01',
'RSM00025123': '2005-04-01'}
for site in begin_dates:
    station_list.loc[site, 'begin_date'] = pd.to_datetime(begin_dates[site])
        

# The number 7305 is the number of days from Jan 1, 2000 to Dec 31, 2019
# station_list = station_list.loc[(station_list.n00Z/7305 > 0.5) | (station_list.n12Z/7305 > 0.5)]
station_list.to_csv('../Data/arctic_stations_long.csv')
station_list = station_list.loc[(station_list.n_missing_months_post_2005 <= 1) | (station_list.index == 'GLM00004417')]
station_list.drop('n_missing_months_post_2005', axis=1, inplace=True)

# Careful: this will drop new stations if they aren't manually added here.
order = ['USM00070133', 'USM00070026', 'USM00070261', 
         'CAM00071957', 'CAM00071043', 'CAM00071925', 'CAM00071924',
         'CAM00071917', 'CAM00071081', 'CAM00071082', 'GLM00004220',
         'GLM00004360', 'GLM00004417', 'GLM00004339', 'GLM00004320',
         'JNM00001001', 'SVM00001004', 'SVM00001028', 'RSM00020744',
         'FIM00002836', 'RSM00022217', 'RSM00022271', 'RSM00023205',
         'RSM00023415', 'RSM00023330', 'RSM00023472', 'RSM00023078',
         'RSM00021824', 'RSM00024266', 'RSM00021946', 'RSM00025123']
station_list = station_list.loc[order,:]



station_list.to_csv('../Data/arctic_stations.csv')

# Add in here: number of undersampled months