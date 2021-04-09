"""Calculate inversion frequency by height and plot the result."""

import numpy as np
import pandas as pd
import proplot as pplt

arctic_stations = pd.read_csv('../Data/arctic_stations.csv')
arctic_stations.set_index('station_id', inplace=True)

inversions = {}
for site in arctic_stations.index:
    inversions[site] = pd.read_csv('../Data/Inversions/' + site + '_inversions.csv')
    inversions[site]['date'] = pd.to_datetime(inversions[site].date.values)
    
def inv_indicator(inv_df, zgrid):
    """Returns a dataframe dimensions (n_obvs x n_heights) with 
    entries 1 if inversion is present at that height and 0 otherwise."""
    ind_list = []
    names = []
    for name, group in inv_df.groupby('date'):

        ind = zgrid*0
        for height_base, height_top in zip(group.height_base, group.height_top):
            ind += np.array((height_base <= zgrid) & (height_top > zgrid))
        ind_list.append(ind)
        names.append(name)
    return pd.DataFrame(np.vstack(ind_list), index=names, columns=zgrid)        

def get_phi(indicator_df):
    """From the indicator df output by inv_indicator, compute lag 1 autocorrelation
    via the Pearson method for each month and each height."""
    corr_coef = np.zeros((12, len(zgrid)))
    for ii, month in enumerate(np.arange(1, 13)):
        for jj, col in enumerate(indicator_df.columns):
            corr_coef[ii, jj] = indicator_df.loc[
                indicator_df.index.month == month, col].shift(1).corr(
                indicator_df.loc[
                    indicator_df.index.month == month, col], method='pearson')   
    return pd.DataFrame(
        data=corr_coef, index=np.arange(1, 13), 
        columns=indicator_df.columns)

def standard_error_adj(f, phi):
    """Computes the error in the proportion adjusted for autocorrelation phi.
    f should be a dataframe or array with nrows = nobservations, ncols=nheights,
    and phi is an array with len nheights."""
    n = len(f)
    v =  (1+phi)/(1-phi)
    v[v < 1] = 1
    se = np.sqrt(f.mean(axis=0)*(1-f.mean(axis=0))/n *v)
    return se


def season(m):
    if m in [12, 1, 2]:
        return 'DJF'
    elif m in [3,4,5]:
        return 'MAM'
    elif m in [6,7,8]:
        return 'JJA'
    else:
        return 'SON'
    
    
freqs = {}
phis = {}
errs = {}
n = {}

for site in arctic_stations.index:
    # setting first point at 5m AGL so changes in elevation aren't as important.
    # could adjust actual time series tho.
    zgrid = arctic_stations.loc[site, 'elevation'] + 5 + np.arange(25, 3000, 50)
    
    # flags 1 if an inversion overlaps that height and 0 if not
    indicator_df = inv_indicator(inversions[site], zgrid)
    
    # monthly average of indicators is the frequency
    freqs[site] = indicator_df.resample('1MS').mean()
    
    # estimate the correlation at each height with pearson correlation coefficient
    phis[site] = get_phi(indicator_df)
    
    # adjusted standard error for proportion if phi is positive, otherwise use standard error
    errs[site] = standard_error_adj(freqs[site], phis[site])
    
    # number of observations in each month
    n[site] = indicator_df.resample('1MS').count().iloc[:,1]
    
    
fig, axs = pplt.subplots(nrows=7, ncols=5, width=12)
for site, ax in zip(arctic_stations.index, np.ravel(axs)):
    seas = np.array([season(m) for m in freqs[site].index.month])
    z = freqs[site].columns
    shade=freqs[site].loc[seas=='DJF'].quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    #ax.plot(freqs[site].columns, median, shadedata=shadedata, fadedata=fadedata, k{orientation:'horizontal'})
    ax.fill_betweenx(z, shade.loc[0.1,:].values, shade.loc[0.9,:].values,alpha=0.2, color='blue')
    ax.fill_betweenx(z, shade.loc[0.25,:].values, shade.loc[0.75,:].values,alpha=0.2, color='blue')
    ax.plot(shade.loc[0.5,:].values, z,  color='blue', linestyle=':')
    f = freqs[site].loc[seas=='DJF'].mean(axis=0)
    err = errs[site].loc[[12,1,2],:].mean(axis=0)
    ax.plot(f.values, z, color='b', linewidth=1)
    ax.plot(f.values - err.values, z, color='b', linewidth=1, linestyle='--')
    ax.plot(f.values + err.values, z, color='b', linewidth=1, linestyle='--')


    shade=freqs[site].loc[seas=='JJA'].quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    #ax.plot(freqs[site].columns, median, shadedata=shadedata, fadedata=fadedata, k{orientation:'horizontal'})
    ax.fill_betweenx(z, shade.loc[0.1,:].values, shade.loc[0.9,:].values,alpha=0.2, color='orange')
    ax.fill_betweenx(z, shade.loc[0.25,:].values, shade.loc[0.75,:].values,alpha=0.2, color='orange')
    ax.plot(shade.loc[0.5,:].values, z,  color='orange', linestyle=':')
    f = freqs[site].loc[seas=='JJA'].mean(axis=0)
    err = errs[site].loc[[6,7,8],:].mean(axis=0)
    ax.plot(f.values, z, color='orange', linewidth=1)
    ax.plot(f.values - err.values, z, color='orange', linewidth=1, linestyle='--')
    ax.plot(f.values + err.values, z, color='orange', linewidth=1, linestyle='--')

    ax.format(xreverse=False, xlim=(0,1), urtitle=arctic_stations.loc[site, 'name'])