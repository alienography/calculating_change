# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 17:13:04 2026

@author: simme
"""
# v12
# this is to generate an output raw data file for use in seasonal/area
# analysis that doesn't include joins, to use as a 'raw' comparison with
# the joined data, while excluding duplicates


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
#buffer_data = gpd.read_file('../MY_INPUTS/buffer50.gpkg')

#buffer_dates = buffer_data['date'].unique()

#np.savetxt('./comparedates.txt', buffer_dates, fmt='%s')

# make a dataframe of all intersections between points and buffers
#touches = gpd.sjoin(
 #   spray_data_regions,
 #   buffer_data,
 #   predicate='intersects')

# make a blank data frame to track when spraying happened
spray_ref = pd.DataFrame().reindex_like(spray_data_regions)

# copying in area and numbers for reference
spray_ref['Area'] = spray_data_regions['Area']
spray_ref['N. of Trap'] = spray_data_regions['N. of Trap']

# merge the highlighted points into one dataframe
results = spray_ref.merge(
    spray_data_regions,
    on=['Area', 'N. of Trap'], 
    how='inner'
    )

# drop unnecessary columns
results_simple = results.drop(columns=['Longitude_x', 'Latitude_x', 'geometry_x', 'Longitude_y', 'Latitude_y', 'geometry_y'])

# ------------ OUTPUT 1 ----------------
results_simple.to_csv('./notouchtest/points.csv')

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
#merge_everything['date'] = pd.to_datetime(merge_everything['date'])

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

# --------------- OUTPUT 2 ------------------
# dataframe showing sprayed date, and data (for total nos only)
merge_everything.to_excel('../MY_INPUTS/filtered_trap_raw.xlsx')

