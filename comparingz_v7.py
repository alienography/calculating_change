# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 17:13:04 2026

@author: simme
"""

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

# reading in path data
buffer_data = gpd.read_file('../test_2528feb/buffertest1.gpkg')

# set a selection for all date in 2022 only
set_year = datetime(2025, 1, 1)
buffer_2225 = buffer_data.loc[buffer_data['date'] < set_year]

# make a dataframe of all intersections between points and buffers
touches = gpd.sjoin(
    spray_data_gdb,
    buffer_2225,
    predicate='intersects')

# make a blank data frame to track when spraying happened
spray_ref = pd.DataFrame().reindex_like(spray_data_gdb)

# copying in area and numbers for reference
spray_ref['Area'] = spray_data_gdb['Area']
spray_ref['N. of Trap'] = spray_data_gdb['N. of Trap']

# merge the highlighted points into one dataframe
results = spray_ref.merge(
    touches,
    on=['Area', 'N. of Trap'], 
    how='inner'
    )

# drop unnecessary columns
results_simple = results.drop(columns=['Longitude_x', 'Latitude_x', 'geometry_x', 'Longitude_y', 'Latitude_y', 'index_right'])

# test that the blank data frame is okay
results_simple.to_excel('./testing123.xlsx')

# export the results to a geodataframe - only needed for outputs
#results_gdf = gpd.GeoDataFrame(results_simple, geometry='geometry_y')
#%%
# rename the indices
results_reworked = results_simple.set_index(['Area', 'N. of Trap'])

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

# print to excel for test
merge_everything.to_excel('./testymerge.xlsx')

#%%

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
    area, trap = idx
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
    merged_wide[(area, trap, select_date)] = desired_values
    
 # convert into a dataframe   
wide_dataframe = pd.DataFrame(merged_wide).T

#%%
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
    ) * 100

# compare % change for 10 days before & after spraying
wide_dataframe['% change (20 days)'] = (
    (wide_dataframe['-10 Days'] -
    wide_dataframe['10 Days']) /
    wide_dataframe['-10 Days'].replace(0, np.nan)
    ) * 100


# print to excel
wide_dataframe.to_excel('./widetest.xlsx')
print('okay!!')
    

