# -*- coding: utf-8 -*-
"""
Creates the required input files for the stack_pipeline_CNN
without the GUI. The Output consists of the InputFilePointer JSON and
the CRSMetadata CSV. Run the whole script and follow the provided instructions.
Rewiew and complete the CRSMetadata file after
running the script because it is possible and likely that not all CRS are
detcted.
Some preknowledge about the pipeline and the data which is entered is required
because the instructions are not fully self explaining. Use this script for further
development.
"""


import json
import os
import pandas as pd
import datetime
import numpy as np

from processing_functions import get_epsg_folder

script_directory = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_directory)
os.chdir(script_directory)


data = {}
print("Press enter if data is not available")
print("Only provide path for either mosaic or tiles. Any path format is supported. ")
while True:
    
    # Add new dataset
    
    city = ""
    # force user to enter a city name at least
    while city == "": 
        city = input("New Dataset: Enter City (or 'quit' to exit): ")
    # exit point
    if city.lower() == "quit": 
        break
    
    year = input("Enter stack Year: ")
    desc = input("Enter stack Description: ")
    
    if city not in data:
        data[city] = {}
    
    if year not in data[city]:
        data[city][year] = {}
        
    
    if desc in data[city][year]:
        print("No duplicates of keys is allowed")
        continue
    
    data[city][year][desc] = {}
    
    data[city][year][desc]["METADATA"] = {
        "README_name": input("Enter README Name: "),
        "output_dir": os.path.normpath(input("Enter Output Directory: "))
    }
    
    
    # for every raster: If input is tiles further information needs to be
    # stored to name the created raster
    
    ndsm = ""
    while ndsm.lower() not in ["y","n"]:
        
        ndsm = input("nDSM availabe [Y/N]: ") # either nDSM or DSM+DTM as input
        
    if ndsm.lower() == "y":
        
        mosaic_path = input("Enter nDSM Mosaic Path if available else press ENTER : ")
        if mosaic_path:
            tiles_path = None
            mosaic_path = os.path.normpath(mosaic_path)
            nodata = None
            mosaic_year = None
            mosaic_desc = None
        else:
            mosaic_path = None
            tiles_path = os.path.normpath(input("Enter nDSM Tiles Path : "))
            nodata = input("Enter tiles nodata value if existing and only if not defined in header\n(opt not available for las/laz): ")
            mosaic_year = input("Enter the nDSM year for labeling the generated mosaic: ")
            mosaic_desc = input("Enter a nDSM description for labeling the generated mosaic: ")
            
        data[city][year][desc]["nDSM"] = {
            "mosaic": mosaic_path,
            "tiles": tiles_path,
            "year": mosaic_year,
            "description": mosaic_desc,
            "noData": nodata
        }
            
        # empty dict entry for DSM and DTM
        
        data[city][year][desc]["DSM"] = {
            "mosaic": None,
            "tiles": None,
            "year": None,
            "description": None,
            "noData":None
        }
        
        data[city][year][desc]["DTM"] = {
            "mosaic": None,
            "tiles": None,
            "year": None,
            "noData":None
        }
        
    else:
        
        mosaic_path = input("Enter DSM Mosaic Path if available else press ENTER : ")
        if mosaic_path:
            tiles_path = None
            mosaic_path = os.path.normpath(mosaic_path)
            nodata = None
            mosaic_year = None
            mosaic_desc = None
            
        else:
            
            mosaic_path = None
            tiles_path = os.path.normpath(input("Enter DSM Tiles Path : "))
            nodata = input("Enter tiles nodata value if existing and only if not defined in header\n(opt not available for las/laz): ")
            mosaic_year = input("Enter the DSM year for labeling the generated mosaic: ")
            mosaic_desc = input("Enter a DSM description for labeling the generated mosaic: ")
            
        data[city][year][desc]["DSM"] = {
            "mosaic": mosaic_path,
            "tiles": tiles_path,
            "year": mosaic_year,
            "description": mosaic_desc,
            "noData": nodata
        }
        
        mosaic_path = input("Enter DTM Mosaic Path if available else press ENTER : ")
        if mosaic_path:
            tiles_path = None
            mosaic_path = os.path.normpath(mosaic_path)
            nodata = None
            mosaic_year = None
        else:
            mosaic_path = None
            tiles_path = os.path.normpath(input("Enter DTM Tiles Path : "))
            nodata = input("Enter tiles nodata value if existing and only if not defined in header\n(opt not available for las/laz): ")
            mosaic_year = input("Enter the DTM year for labeling the generated mosaic: ")

            
        data[city][year][desc]["DTM"] = {
            "mosaic": mosaic_path,
            "tiles": tiles_path,
            "year": mosaic_year,
            "noData": nodata
        }
        
        # empty dict entry for DSM and DTM
        data[city][year][desc]["nDSM"] = {
            "mosaic": None,
            "tiles": None,
            "year": None,
            "description": None,
            "noData":None
        }
    
    mosaic_path = input("Enter ORTHO Mosaic Path if available else press ENTER : ")
    if mosaic_path:
        tiles_path = None
        mosaic_path = os.path.normpath(mosaic_path)
        nodata = None
        mosaic_year = None
        mosaic_desc = None
        mosaic_dop_tdop = None
    else:
        mosaic_path = None
        tiles_path = os.path.normpath(input("Enter ORTHO Tiles Path : "))
        nodata = input("Enter tiles nodata value if existing and only if not defined in header\n(opt not available for las/laz): ")
        mosaic_year = input("Enter the ORTHO year for labeling the generated mosaic: ")
        mosaic_desc = input("Enter a ORTHO description for labeling the generated mosaic: ")
        mosaic_dop_tdop = input("Enter tdop/dop for labeling the generated mosaic: ")

        
    data[city][year][desc]["ORTHO"] = {
        "mosaic": mosaic_path,
        "tiles": tiles_path,
        "year": mosaic_year,
        "description": mosaic_desc,
        "dop_tdop": mosaic_dop_tdop,
        "noData": nodata
    }

timestamp = datetime.datetime.now().strftime("%d_%m_%Y-%H_%M")
json_filename = os.path.join(root_dir, "data", "Input", "InputFilePointer",f"Input_{timestamp}.json" )



with open(json_filename, "w") as json_file:
    json.dump(data, json_file, indent=4)

print(f"JSON data has been saved to \n{json_filename}")


## CRS file creation ##########################################################

# CRS detection is also included here

column_names = ["city","year","desc","DSM","DTM","nDSM","ORTHO"]  # Replace with your column names
df_epsg = pd.DataFrame(columns=column_names)
df_epsg.set_index(["city","year","desc"], inplace=True)


for city in data.keys():
    for year in data[city].keys():
        for desc in data[city][year].keys():
            ds_epsg = []
            for column_name in ["DSM", "DTM", "nDSM", "ORTHO"]:
                ds_folder_dir = data[city][year][desc][column_name]
                if ds_folder_dir["tiles"]:
                    epsg = get_epsg_folder(ds_folder_dir["tiles"])
                elif ds_folder_dir["mosaic"]:
                    epsg = get_epsg_folder(ds_folder_dir["mosaic"])
                else:
                    epsg = np.nan
                
                ds_epsg.append(epsg)
                
            df_epsg.loc[(city, year, desc),:] = ds_epsg
epsg_filename = os.path.join(root_dir, "data", "Input", "CRSMetadata",f"epsg_input_data_{timestamp}.csv" )
df_epsg.to_csv(epsg_filename, index=True, float_format='%.0f')
print(f"Check the CRSMetadata file and insert any missing epsg code by hand\n {epsg_filename}")