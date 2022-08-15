# Climatology of Arctic surface-based and elevated inversions, 2000-2019
The scripts necessary to carry out the analysis of the paper "Climatology of Arctic surface-based and elevated inversions, 2000-2019" are provided here. 

Requirements: 
numpy  
pandas  
metpy  
siphon  

## Scripts
### 01_download_igra_data.py
Downloads IGRA data for all stations north of 64 which have data between 2000-2019. Data are saved in ../Data/IGRA_Derived and the headers are saved in ../Data/IGRA_Headers. The station list for the station files downloaded are saved as ../Data/arctic_stations_init.csv

### 02_process_igra_data.py
Reads through the downloaded IGRA data. Selects just the data within +/- 1 hr of 00Z and 12Z. Checks if the surface level is present and if there are at least 5 levels present below 500 hPa. Next, checks the number of soundings at each time. Drops data from months that have less than 25% of the expected soundings at each time. Processed profiles are placed in ../Data/Soundings
TBD: output data on the number of soundings available at each time for use in the data figure

### 0X_plot_sonde_types.py
 
