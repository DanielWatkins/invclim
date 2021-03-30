"""Process Soundings
   
   This script prepares soundings for inversion analysis by applying linear interpolation, and 
   rejecting data that does not exceed an error threshold (?).
"""

import pandas as pd
import numpy as np

##### HELPER FUNCTIONS ############
# Need to fix this one to allow for 6 and 18 if used in the GRUAN data
def adjust_time(date):
    """If launch time > 22, assign to 00 the next day. If launch time is between 10 and 2, assign to 12."""
    
    if date.hour <= 2:
        return (date - pd.Timedelta(hours=date.hour)).round('1h')
    if date.hour >= 22:
        adj = np.abs(date.hour - 24)
        return (date + pd.Timedelta(hours=adj)).round('1h')
    if np.abs(date.hour - 12) <= 2:
        adj = date.hour - 12
        return (date - pd.Timedelta(hours=adj)).round('1h')
    else:
        return date
    
def significant_levels(df, t_thresh):
    """Retains only enough points in the profile to recreate the profile
    with an error of t_thresh. Intended use is to downsample high resolution
    radiosondes for more even comparison of profiles.
    Beginning with just the top and bottom values, the code repeatedly checks
    the value of the departure from the linear interpolation. The point with
    greatest error is added to the significant levels set. 
    """
    import warnings
    warnings.filterwarnings('ignore', category=FutureWarning)

    idx = df.pressure.values >= 500
    traw = df.temperature.values[idx]
    zraw = df.height.values[idx]
    praw = df.pressure.values[idx]
    ptraw = df.potential_temperature.values[idx]
    
    
    keep_idx = []
    keep_idx.append(0)
    keep_idx.append(len(traw)-1)
    keep_idx.append(np.random.choice(np.arange(len(traw))))
    t0 = np.array(traw[keep_idx])
    z0 = np.array(zraw[keep_idx])
    p0 = np.array(praw[keep_idx])
    count = 0
    max_iter = 100
    t_error = np.abs(np.interp(zraw, z0, t0) - traw)
    while (np.max(t_error) > t_thresh) & (count < max_iter):
        t_error = np.abs(np.interp(zraw, z0, t0) - traw)
        max_idx = np.argmax(t_error)

        keep_idx.append(max_idx)
        keep_idx.sort()
        keep_idx = list(np.unique(keep_idx))
        t0 = np.array(traw[keep_idx])
        z0 = np.array(zraw[keep_idx])
        count += 1
        if count > max_iter:
            break
    df = df.iloc[keep_idx,:].copy()
    return df


##### MAIN LOOP #######
arctic_stations = pd.read_csv('../arctic_station_list.csv')
dataloc = '../Data/IGRA2_Derived/'
saveloc = '../Data/SignificantLevels/'
eps=[1]
for station in arctic_stations.station_id.values:
    print(station)
    df = pd.read_csv(dataloc + station + '-igra2-derived.csv', index_col=False)
    df.drop('Unnamed: 0', axis=1, inplace=True)
    df.date = pd.to_datetime(df.date)
    df.date = [adjust_time(d) for d in df.date]
    df.rename({'calculated_height': 'height'}, axis=1, inplace=True)
    for epsilon in eps:
        df_sl = df.groupby('date').apply(significant_levels, epsilon)
        if 'level_1' in df_sl.columns:
            df_sl.drop('level_1', axis=1, inplace=True)
        if 'date' in df_sl.columns:
            df_sl.drop('date', axis=1, inplace=True)
        df_sl.reset_index(inplace=True)
        if 'level_1' in df_sl.index:
            df_sl.drop('level_1', axis=1, inplace=True)
        df_sl.to_csv(saveloc + station + '_slevels_' + str(epsilon) + '-K.csv', index=False)
        del df_sl
    del df
    