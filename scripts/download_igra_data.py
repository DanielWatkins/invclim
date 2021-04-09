"""Download IGRA2 data for all stations north of 65 with data extending from 2000 to 2019.
Add calculated variables, and select only the significant levels, surface level, and 500 hPa level."""

import numpy as np
import pandas as pd
from metpy.units import units
import metpy.calc as mpcalc
from siphon.simplewebservice.igra2 import IGRAUpperAir
from datetime import datetime
import os


def import_soundings(station_id):
    """Reads in file with soundings, selects data below 500 hPa, and renames the columns as needed.
    Adds dewpoint temperature and equivalent potential temperature using MetPy. Also computes the
    adjusted relative humidity (wrt ice if T < 0 C)"""
    
    df = pd.read_csv('../Data/IGRA2_Derived/' + station_id + '-igra2-derived.csv')
    df = df.loc[df.pressure >= 500]
    press = df.pressure.values
    press_sel = ((press != 1000) & (press != 925)) & ((press != 850) & (press != 700))
    df = df.loc[press_sel]
    df['date'] = pd.to_datetime(df.date.values)
    hours = df.date.dt.hour
    hour_sel = ((hours > 22) | (hours < 2)) | ((hours > 10) & (hours < 14))
    df = df.loc[hour_sel, :]
    df = df.loc[(df.date >= '2000-01-01') & (df.date < '2020-01-01')].reset_index(drop=True)
    

    
    df.drop(['Unnamed: 0', 'reported_height', 'reported_relative_humidity'], axis=1, inplace=True)
    df.rename({'calculated_height': 'height',
               'calculated_relative_humidity': 'relative_humidity'}, axis=1, inplace=True)
    df['dewpoint_temperature'] = mpcalc.dewpoint(vapor_pressure=df.vapor_pressure.values * units.hPa).to_base_units().magnitude
    df['dewpoint_temperature'] = np.round(df['dewpoint_temperature'].values, 1)
    df.dropna(axis=0, how='any', subset=['relative_humidity'], inplace=True)

    df['equivalent_potential_temperature'] = mpcalc.equivalent_potential_temperature(
                        pressure=df.pressure.values * units.hPa,
                        temperature=df.temperature.values * units.kelvin,
                        dewpoint=df.dewpoint_temperature.values * units.kelvin).to_base_units().magnitude
    
    def satvap_ice(T):
        """Returns the saturation vapor pressure in mb for temperatures
        between -40 and 0 C based on Rogers and Yau, which itself is based
        on Wexler 1977. Units in mb. Expects T to be in K."""
    
        import numpy as np
        from scipy.interpolate import interp1d

        tref = np.array([203.15, 213.15, 223.15, 233.15, 238.15,
           243.15, 248.15, 253.15, 258.15, 263.15, 268.15, 273.15])
        eiref = np.array([0.26, 1.08, 3.9, 12.85, 22.36, 38.02, 63.3, 103.28, 165.32, 259.92, 401.78, 611.15])/100
        svap_i = interp1d(x=tref, y=eiref, kind='quadratic', fill_value=np.nan)

        return svap_i(T)

    def satvap_liq(T):
        """Formula from Bolton (1980) via Rogers and Yin. Units mb. Expects T units in K."""
        tc = T - 273.15
        return 6.112 * np.exp(17.67*tc / (tc + 243.5))
    
    def convert_rh(data):
        """Returns the relative humidity with respect to water
        if T > 273.15, ice if T < 273.15."""
        vap = data['vapor_pressure'].values
        satvap = data['saturation_vapor_pressure'].values
        temp = data['temperature'].values

        rh = np.zeros(len(temp))
        rh = vap/satvap_liq(temp)

        adj_idx = (temp < 273.15) & (temp > 203.15)
        rh[adj_idx] = vap[adj_idx] / satvap_ice(temp[adj_idx])
        rh[temp < 203.15] = np.nan            
        return rh*100

    df['adjusted_relative_humidity'] = convert_rh(df)

    return df.loc[:, ['date', 'pressure', 'height', 'temperature', 'dewpoint_temperature',
       'potential_temperature', 'equivalent_potential_temperature', 'relative_humidity',
       'adjusted_relative_humidity']].round(2)



station_list = pd.read_fwf('../igra2-station-list.txt',
                          header=None)
station_list.columns = ['station_id', 'lat', 'lon', 'elevation', 'name', 'start_year', 'end_year', 'count']
station_list = station_list.loc[(station_list.lat >= 65) & (station_list.end_year >= 2019)]
station_list = station_list.loc[station_list.start_year <= 2000]

station_list.set_index('station_id', inplace=True)
print('Number of available stations:', len(station_list))

begin = datetime(1990,1,10)
end = datetime(2019,12,31,23)
for site in station_list.index:
    try:
        df, header = IGRAUpperAir.request_data([begin, end], site, derived=True)
        df.to_csv('../Data/IGRA2_Derived/' + site + '-igra2-derived.csv')
        header.to_csv('../Data/IGRA2_Headers/' + site + '-igra2-derived.csv')
        print(station)
    except:
        print('Download failed for site', site)
        
        
        
soundings = {}
for site in station_list.index:
    try:
        df = import_soundings(site)
        df.to_csv('../Data/Soundings/' + site + '-cleaned-soundings.csv')
        soundings[site] = df
        print(site)
        del df
    except:
        print('Failed ' + site)