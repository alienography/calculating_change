# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 17:13:04 2026

@author: simme
"""
#**********************
# includes a map
# this file reads in the data, and the buffers of spraying
# it then finds which points are within buffers, and the date that buffer
# was created (i.e., when those points were sprayed)
# it then finds the no. of olive flies 5, 10 and 15 days before spraying, and
# the same time after, and calculates the % differences
# it also then splits this into the 8 regions and calculates the differences
# by region

# ------- outputs -------
# 1. all sprayed points (as excel, because gpkg doesn't allow multiindex)
# 2. dataframe of all instances of spraying (minus filtered ones) + olive fly no.
# 3. dataframe of % change before/after spraying, made into quartiles
# 4. a map output of average change by region


# importing relevant packages
import geopandas as gpd
import pandas as pd
import fiona
import shapely
from shapely.geometry import Point, LineString, shape, Polygon
from io import StringIO
from pathlib import Path
import os
import numpy as np
from datetime import datetime, timedelta

# import mapping packages
import matplotlib.pyplot as plt
from matplotlib.pyplot import subplots, savefig, close

# so define whether traps are sprayed or not sprayed based on dates
# then compare averages to original value, and averages of sprayed vs. non-sprayed
# basically

# take 2022 for example and try to figure out which traps were sprayed vs.
# which weren't for example

# ============= READ IN DATA =============
# first need to rearrange trap data, because it's structured in a horrible way
# actually do i?

# reading in trap data
trap_data = pd.read_excel('../../Samos 2022-2024-20251120T120022Z-1-001/Samos 2022-2024/Traps Samos 2022-2024.xlsx',
                          sheet_name='2022', usecols=['Area', 'N. of Trap', 'Longitude', 'Latitude']#, header=[0, 1]
                          )


# read in olive fly number data
fly_numbers = pd.read_excel('../../Samos 2022-2024-20251120T120022Z-1-001/Samos 2022-2024/Traps Samos 2022-2024.xlsx',
                          sheet_name=['2022', '2023', '2024'], dtype={1: 'float64'}, header=[0, 1]
                          )

# read in regions of samos - DONE WITH FINISHED REGIONS
samos_regions = gpd.read_file('../MY_INPUTS/samos_regions.gpkg')

samos_regions = samos_regions.to_crs('EPSG:4326')

samos_regions = samos_regions.drop(['EKTASH', 'PERIMETROS', 'NAME_GREEK', 'NAME_LATIN', 'TYPOS', 'path'], axis=1)


# set area and trap number as a multiindex
for sheet in fly_numbers:
    fly_numbers[sheet] = fly_numbers[sheet].set_index([('Area', 'Unnamed: 0_level_1'), 
                                                       ('N. of Trap', 'Unnamed: 1_level_1')]
                                                       )

# combine the different years into one year
merged_flies = pd.concat(fly_numbers.values(), axis=1)

# get rid of duplicate latitude, longitude & altitude columns
merged_flies = merged_flies.loc[:, ~merged_flies.columns.duplicated()]

# make the dataframe into point data with geometries
spray_data_gdb = gpd.GeoDataFrame(trap_data, geometry=gpd.points_from_xy(
                                  trap_data[('Longitude')],
                                  trap_data[('Latitude')]),
                                  crs='EPSG:4326')
print("Successfully made geometries of the trap locations") 

spray_data_regions = gpd.sjoin(
    spray_data_gdb,
    samos_regions,
    predicate='intersects')

spray_data_regions = spray_data_regions.drop(['index_right'], axis=1)

# reading in path data
buffer_data = gpd.read_file('../MY_INPUTS/buffer50.gpkg')

buffer_dates = buffer_data['date'].unique()

np.savetxt('./comparedates.txt', buffer_dates, fmt='%s')

# make a dataframe of all intersections between points and buffers
touches = gpd.sjoin(
    spray_data_regions,
    buffer_data,
    predicate='intersects')

touches.to_excel('./touches.xlsx')

# make a blank data frame to track when spraying happened
spray_ref = pd.DataFrame().reindex_like(spray_data_regions)

# copying in area and numbers for reference
spray_ref['Area'] = spray_data_regions['Area']
spray_ref['N. of Trap'] = spray_data_regions['N. of Trap']

# merge the highlighted points into one dataframe
results = spray_ref.merge(
    touches,
    on=['Area', 'N. of Trap'], 
    how='inner'
    )

# drop unnecessary columns
results_simple = results.drop(columns=['Longitude_x', 'Latitude_x', 'geometry_x', 'Longitude_y', 'Latitude_y', 'index_right', 'vehicle_id', 'segment_no', 'geometry_y'])

# ------------ OUTPUT 1 ----------------
results_simple.to_csv('../MY_INPUTS/only_sprayed_points.csv')

#%% renaming columns and sorting out indices
# rename the indices
results_reworked = results_simple.set_index(['Area', 'N. of Trap', 'layer_y'])

# rename the indices pt. II
merged_flies.index.set_names(['Area', 'N. of Trap'], inplace=True)

# label the different levels of the header
merged_flies.columns.names = ['Date', 'Type']

# take out either total numbers or female fly numbers
total_cols = merged_flies.columns[
              merged_flies.columns.get_level_values('Type') != 'Female']  
female_cols = merged_flies.columns[
              merged_flies.columns.get_level_values('Type') != 'Total']

# seperating data on female/total flies
Female_data = merged_flies[female_cols].copy()
total_data = merged_flies[total_cols].copy()

# make a blank data frame to track when spraying happened - is this necessary?
blank_results = pd.DataFrame().reindex_like(merged_flies)

# merge the fly data & buffer data into one file
merge_everything = total_data.merge(results_reworked, left_index=True, right_index=True, how='inner')

# ensuring the data is in datetime format
merge_everything['date'] = pd.to_datetime(merge_everything['date'])

# deleting redundant layer
merge_everything = merge_everything.drop(['layer_x'], axis=1)

# renaming columns to remove the 'total' part
saus = merge_everything.columns
saus1 = []

# looping through column names and only taking the dates
for element in saus:
    
    element = element[0]
    saus1.append(element)

# setting the simplified versions to the column names
merge_everything.columns = saus1

# make a list of columns that need to be changed to datetime
cols_to_change = list(merge_everything.columns)

# convert these to datetime
cols_to_change[2:] = pd.to_datetime(cols_to_change[2:], errors='ignore')

# merge back into the original dataframe
merge_everything.columns = cols_to_change


#%% filtering out spraying dates that are within 2 days of each other

# sort values by date
#merge_everything = merge_everything.sort_values('d')

# calculate the difference between subsequent dates
#non_date_cols = merge_everything.columns.difference(['d']).tolist()


# check how many groups per region
#test = merge_everything.groupby(level=['Area', 'N. of Trap', 'layer_y']).apply(
 #   lambda x: x[non_date_cols].drop_duplicates().shape[0]
#)

#print(test.values)


# if the difference between spraying dates is too little, delete
def drop_near_duplicates(case, days=2):       # THIS IS A KEY VARIABLE, ESSENTIALLY HOW CLOSE SPRAYING EVENTS CAN BE TOGETHER
    case = case.sort_values('d', ascending=False)
    
    keep_cases = case['d'].diff().dt.days.abs().fillna(days+1) > days
    return case[keep_cases]

# call the function
merge_everything = merge_everything.groupby(['Area', 'N. of Trap', 'layer_y'],
                                            group_keys=False).apply(drop_near_duplicates)

print(merge_everything.index.get_level_values(2).unique())

                                                

                                                
# --------------- OUTPUT 2 ------------------
# dataframe showing sprayed date, and data (for total nos only)
merge_everything.to_excel('../MY_INPUTS/sprayed_data_raw.xlsx')

#%% only selecting the columns that are just before & after spraying

# okay, trying two different ways. one is a wide merge, the next a long merge
# this is the wide version

# define a dictionary (merged_wide)
merged_wide = {}

# filter out the columns that are labelled with a date
date_cols = merge_everything.columns[pd.to_datetime(merge_everything.columns, errors='coerce').notna()]

# define a standard set of labels
expect_labels = ['-15 Days', '-10 Days',
                '-5 Days', '0 Days', '5 Days',
                '10 Days', '15 Days']


# create a loop to extract only data near the spray date
for idx, row in merge_everything.iterrows():
    
    # define the index
    area, trap, l = idx
    # select the spray date of the site
    select_date = row['d']
    
    # define a start date 15 days before spraying
    start = select_date - pd.Timedelta(days=15)
    # define an end date 15 days after spraying
    end = select_date + pd.Timedelta(days=15)
    
    # only select columns within this 30 day range
    select_cols = date_cols[(date_cols >= start) & (date_cols <= end)]
    
    # take the values from within this range
    desired_values = row[select_cols]
    
    # convert this to datetime
    select_cols_datetime = pd.DatetimeIndex(select_cols)
        
    # define an offset from the spraying date
    offset = np.round((select_cols_datetime - select_date).days / 5) * 5
    offset = offset.astype(int)
    
    # set the week name to be this offset
    desired_values.index = [f'{week} Days' for week in offset]
    
    # reindex the columns to standard labels
    desired_values = desired_values.reindex(expect_labels)
    
    # make a dictionary linking index to the wanted values
    merged_wide[(area, trap, l, select_date)] = desired_values
    
 # convert into a dataframe   
wide_dataframe = pd.DataFrame(merged_wide).T

wide_dataframe.to_excel('./wideandlong.xlsx')

#%% calculating percentage change
# then calculating the percentage difference between the first and last values (i.e., change)
# maybe could make this a bit more customisable?
# like that it could change b/w 1st/2nd/3rd week before etc

#withna = wide_dataframe.fillna(method='bfill', axis=1)
#withna.to_excel('./nas.xlsx')

# compare % change between 15 days before and after spraying
wide_dataframe['% change (30 days)'] = (
    (wide_dataframe['-15 Days'] - 
    wide_dataframe['15 Days']) / 
    wide_dataframe['-15 Days'].replace(0, np.nan)
    ) * -100

# compare % change for 10 days before & after spraying
wide_dataframe['% change (20 days)'] = (
    (wide_dataframe['-10 Days'] -
    wide_dataframe['10 Days']) /
    wide_dataframe['-10 Days'].replace(0, np.nan)
    ) * -100

# compare % changr for 5 days before & after spraying
wide_dataframe['% change (10 days)'] = (
    (wide_dataframe['-5 Days'] - 
     wide_dataframe['5 Days']) /
    wide_dataframe['-5 Days'].replace(0, np.nan)
    ) * -100

print('okay!!')

#%% testing for normal distribution

       # get rid of % change columns
#        towreck = wide_dataframe.drop(columns=['% change (30 days)', '% change (20 days)', '% change (10 days)'])

# melt the three datasets into one for plotting       
#        wide_melt = pd.melt(towreck, ignore_index=False)
 
# plot a frequency histogram with olive fly values       
#        plt.hist(wide_melt['value'], bins=250, color='Black', edgecolor='Black')   
#        plt.xlabel('Values')
#        plt.ylabel('Frequency')                                                 

# save figure       
#        savefig('./testplot.png', dpi=300)
#        close()
#        print("[DONE] Saved map for plot")  
    

#%% categorising into groups of 25
# define given quartile bins
bins_u = [-100, -75, -50, -25, 0, 25, 50, 75, 100, 7100] 

# rename the multi-level index
wide_dataframe.index.rename(['Area', 'Trap', 'Region', 'date'], inplace=True)

# sift the changes after 10 days into bins based on percentage change
category20 = (wide_dataframe.groupby(level='Region')['% change (20 days)'].value_counts(bins=bins_u)
              )

# sift the changes after 10 days into bins based on percentage change
category10 = (wide_dataframe.groupby(level='Region')['% change (10 days)'].value_counts(bins=bins_u)
              )

# sift the changes after 10 days into bins based on percentage change
category30 = (wide_dataframe.groupby(level='Region')['% change (30 days)'].value_counts(bins=bins_u)
              )

# merge the three categorised datasets into one
categorised = pd.concat([category10, category20, category30], axis=1)

# sort the index numerically
categorised = categorised.sort_index()

# ----------- OUTPUT 3 --------------------
# export % change, categorised into quartiles, as an excel file
categorised.to_excel('../MY_INPUTS/spraying_chg_categorised.xlsx')

#%% making a map from the outputs
# rename the layers of the samos regions
samos_regions = samos_regions.rename({'layer': 'Region'}, axis=1)

# convert to greek grid
samos_regions = samos_regions.to_crs('epsg:2100')

# calculate the mean of average change
average_change = categorised.groupby('Region')['% change (20 days)'].mean()

# calculate the median average regional change
median_change = categorised.groupby('Region')['% change (20 days)'].median()

# initialise a dataframe with averages
average = pd.DataFrame({'Region':average_change.index, 'Mean Change':average_change.values, 'Median Change':median_change.values})

# merge averages with geometry
average_map = average.merge(
    samos_regions,
    on='Region', 
    )

# make into a geodataframe
average_gpd = gpd.GeoDataFrame(average_map, geometry='geometry')

# convert to greek grid
average_gpd = average_gpd.to_crs('epsg:2100')

# Set up the 2x2 map grid
fig, (my_ax1, my_ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Plot total production (Top left)
average_gpd.plot(
    ax=my_ax1,
    column='Mean Change',
    edgecolor=None,
    cmap='Wistia',
    linewidth=0.5,
    legend=True,
    legend_kwds={'label': "% change between 10 days before and after spraying", 'shrink': 0.6}
)

samos_regions.plot(
    ax=my_ax1,
    facecolor='none',
    edgecolor='black',
    linewidth=0.4
)

# Plot total production (Top left)
average_gpd.plot(
    ax=my_ax2,
    column='Median Change',
    edgecolor=None,
    cmap='Wistia',
    linewidth=0.5,
    legend=True,
    legend_kwds={'label': "% change between 10 days before and after spraying", 'shrink': 0.6}
)

samos_regions.plot(
    ax=my_ax2,
    facecolor='none',
    edgecolor='black',
    linewidth=0.4
)
my_ax1.set(title="Mean % change by region")
my_ax1.axis('off')

my_ax2.set(title="Median % change by region")
my_ax2.axis('off')

# ------------------- OUTPUT 4 ----------------------
# customisable map of averages
savefig("./OutputMap.png", dpi=300)
close()
print("[DONE] Saved map!")    