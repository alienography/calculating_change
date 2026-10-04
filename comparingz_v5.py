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

# setting column names then to datetime format
merge_everything.columns = pd.to_datetime(merge_everything.columns, errors='ignore')

# print to excel for test
merge_everything.to_excel('./testymerge.xlsx')

print("made merged file")

column_ref = merge_everything.columns
keep_columns = []

for eachrow in merge_everything.itertuples():
    
    date = eachrow.d
    datelow = eachrow.d - timedelta(days=4)
    datehigh = eachrow.d + timedelta(days=4)

    date_list = pd.date_range(datelow, datehigh, freq='D')
    print(date_list, column_ref)
    col_ref = np.isin(column_ref, date_list)
    print(col_ref)
    break

keep_columns = merge_everything.columns[
                merge_everything.columns]






