"""Apply the inversion detection algorithm to the files in dataloc.
"""
import pandas as pd
import sys
sys.path.append('/Users/watkdani/Documents/Research/Thesis/02 Climatology of multilayered temperature inversions/')
import invclim.core as icc
import invclim.invfinder as iif

# significant level inversions
dataloc = '../Data/Soundings/'

params={'max_embed_depth': 100, 
        'min_dz': 0, # units('m'),
        'min_dp': 0, # units('hPa'),
        'min_dt': 0, # units('K'),
        'min_drh': 0, # units('percent'),
        'rh_or_dt': False}

def find_inversions(group):
    df = icc.setup_dataset(group.loc[:, ['date','pressure','height','temperature','relative_humidity']
                                    ].reset_index(drop=True)) # put the reset into setup_dataset
    inv = iif.invfinder(df, params)
    inv.index.names = ['inv_number']
    inv.reset_index(inplace=True)
    inv['date'] = group.name
    return inv

arctic_stations = pd.read_csv('../Data/arctic_stations.csv')
saveloc = '../Data/Inversions/'

for site in arctic_stations.station_id:
    try: 
        df = pd.read_csv(dataloc + site + '-cleaned-soundings.csv')
        
        df['date'] = pd.to_datetime(df.date.values)
        try:
            inv = df.groupby('date').apply(find_inversions)
            inv.to_csv(saveloc + site + '_inversions.csv')
            del inv
        except:
            print(site + ' find inversions failed')
    
    except:
        print(site + ' load soundings failed')
  

