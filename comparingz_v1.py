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
from datetime import datetime

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
                          sheet_name='2022'#, header=[0, 1]
                          )

# label the different levels of the header
#trap_data.columns.names = ['Date', 'Type']

total_cols = trap_data.columns[trap_data.loc[0] != 'Female']  
#women_cols = trap_data.columns[trap_data.loc['Type'] != 'Total']

#women_data = trap_data[women_cols].copy()
total_data = trap_data[total_cols].copy()
# make it so the indices for the dataframe are the area & trap no, not just
# a random index based on the row
#testy = trap_data.set_index([('Area', 'Unnamed: 0_level_1'), 
 #                           ('N. of Trap', 'Unnamed: 1_level_1')]
  #                          )

#print(testy.columns)
print(total_data.columns)
#%%
# make the dataframe into point data with geometries
spray_data_gdb = gpd.GeoDataFrame(trap_data, geometry=gpd.points_from_xy(
                                  trap_data[('Longitude', 'Unnamed: 2_level_1')],
                                  trap_data[('Latitude', 'Unnamed: 3_level_1')]),
                                  crs='EPSG:4326')
print("Successfully made geometries of the trap locations") 

spray_geom = spray_data_gdb['geometry']
#print(spray_data_gdb['geometry']) 

#spray_data_gdb.columns = spray_data_gdb.columns.get_level_values(0)
 # ----------- all below is trying (and afailing) to flatten multiindex columns
#beepboop = 'datetime.datetime'
#new_cols = []
#count = 1

#for x in spray_data_gdb.columns:
 #   if isinstance(x, datetime):

  #      new_cols.append(count)        
   #     count += 1
   # else:
   #     new_cols.append(x)
        
#spray_data_gdb.columns = new_cols

print('hey everyone !!!!!!!! ')
print(spray_data_gdb.columns)

#spray_data_gdb.to_excel('../test_2528feb/withdata.xlsx')


#print(trap_data.columns.levels)
#print('HEYYYYY!')
#print(trap_data.columns.get_level_values(0).map(type))
#print(trap_data.columns.get_level_values(1).map(type).unique())
    
#dtype.to_excel('./trapdatadtype.xlsx')


# reading in path data
buffer_data = gpd.read_file('../test_2528feb/buffertest1.gpkg')

# set a selection for all date in 2022 only
set_year = datetime(2023, 1, 1)
buffer_2022 = buffer_data.loc[buffer_data['date'] < set_year]

print(spray_data_gdb.columns)
print(spray_data_gdb.columns.nlevels)

touches = gpd.sjoin(
    spray_data_gdb,
    buffer_2022,
    predicate='intersects')

print(touches)

touches.to_csv('./testzubisou.csv')

# make a blank data frame to track when spraying happened
spray_ref = pd.DataFrame().reindex_like(testy)

# test that the blank data frame is okay
spray_ref.to_excel('./testing123.xlsx')



