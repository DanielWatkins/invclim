"""Apply the inversion detection algorithm to the files in dataloc.
Need to run invtools.py in the same environment first."""

# significant level inversions
dataloc = '../Data/SignificantLevels/'
params = default_params()
params['iso_above'] = True
params['max_embed_depth'] = 0

arctic_stations = pd.read_csv('../arctic_station_list.csv')
dataloc = '../Data/SignificantLevels/'
saveloc = '../Data/SignificantLevelInversions/'

for station in arctic_stations.station_id:
    print(station)
    df = pd.read_csv(dataloc + station + '_slevels_1-K.csv', index=False)
    inv = df.groupby('date').apply(find_temperature_inversions, params)
    inv.to_csv(saveloc + station + '_inversions.csv')
    
    del df
    del inv