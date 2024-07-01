# -*- coding: utf-8 -*-
"""
Created on Tue May  9 12:42:23 2023

@author: process
"""
import os
import sys
import glob
import json
import time
import traceback
from statistics import mode

import numpy as np
import pandas as pd
import rasterio
import shutil
import subprocess

# Get the absolute path of the current script and its parent directory
script_directory = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_directory)

# Add the project root and the current directory to the Python path
sys.path.append(root_dir)
sys.path.append(script_directory)

# Now use absolute imports from the project root
from processing.config import unused_cpus, chunksize
from processing import default_nodata_dict
from processing.processing_functions import (
    create_temp_folders, generate_nDSM,
    get_num_channels_first_tif_in_folder, my_logger, parallel_jpx_tif,
    parallel_laz_tif, parallel_xyz_tif, tiles_to_mosaic, uniform_resolution_check
)

# Change the working directory to the script directory
# Note: Changing the working directory can have side effects,
# so be cautious about how this might affect other parts of your code
os.chdir(script_directory)


## Manual Control Configuration ###############################################

input_file_pointer_path_manuell = os.path.normpath(
    r'Q:\MnD\Methoden\Code_GitHub\Stack_Pipeline_CNN\data\Input\InputFilePointer\Input_27_06_2024-15_08.json')
crs_metadata_path_manuell = os.path.normpath(
    r'Q:\MnD\Methoden\Code_GitHub\Stack_Pipeline_CNN\data\Input\CRSMetadata\epsg_input_data_27_06_2024-15_08.csv')


###############################################################################

def should_process(dataset, key):
    """
    Determine whether to process a specific part of the dataset.
    """
    # Default to True if 'process' key is not present (backward compatibility)
    return dataset.get(key, {}).get('process', True)


def main_application(input_file_pointer_path, crs_metadata_path):
    ## Setup ######################################################################
    pipeline_start = time.time()  # absolute start time

    script_directory = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_directory)
    os.chdir(script_directory)

    logger = my_logger(os.path.join(root_dir, 'pipeline.log'), __name__)
    logger.info('Pipeline process started')
    logger.info(f'InputFilePointer: {input_file_pointer_path}')
    logger.info(f'CRSMetadata: {crs_metadata_path}')

    crs_metadata = pd.read_csv(crs_metadata_path, index_col=[0, 1, 2], dtype={'year': str})

    create_temp_folders(input_file_pointer_path)

    with open(input_file_pointer_path, 'r') as f:
        input_file_pointer = json.load(f)

    # dataset is identifiable through key consisting of city, year, desc
    for city in input_file_pointer.keys():
        for year in input_file_pointer[city].keys():
            for desc in input_file_pointer[city][year].keys():
                # setup output folder structure
                base_out_folder_dir = os.path.join(input_file_pointer[city][year][desc]["METADATA"]["output_dir"], city,
                                                   year)
                counter = 2
                output_folder_dir = base_out_folder_dir
                while os.path.isdir(output_folder_dir):
                    output_folder_dir = f"{base_out_folder_dir}_{counter}"
                    counter += 1
                os.makedirs(output_folder_dir, exist_ok=True)

                try:
                    ds_dict = input_file_pointer[city][year][desc]

                    # define mosaic output path and file names (naming convention)
                    mosaic_dir = {}
                    if should_process(ds_dict, 'DSM'):
                        filename = f"{city}_{ds_dict['DSM']['year']}_{ds_dict['DSM']['description']}_DSM_mosaic_%resolution%.tif"
                        mosaic_dir['DSM'] = os.path.join(output_folder_dir, filename)

                    if should_process(ds_dict, 'DTM'):
                        filename = f"{city}_{ds_dict['DTM']['year']}_DTM_mosaic_%resolution%.tif"
                        mosaic_dir['DTM'] = os.path.join(output_folder_dir, filename)

                    if should_process(ds_dict, 'nDSM'):
                        filename = f"{city}_{ds_dict['nDSM']['year']}_{ds_dict['nDSM']['description']}_nDSM_mosaic_%resolution%.tif"
                        mosaic_dir['nDSM'] = os.path.join(output_folder_dir, filename)

                    if should_process(ds_dict, 'ORTHO'):
                        filename = f"{city}_{ds_dict['ORTHO']['year']}_{ds_dict['ORTHO']['description']}_{ds_dict['ORTHO']['dop_tdop']}_%channels%_mosaic_%resolution%.tif"
                        mosaic_dir['ORTHO'] = os.path.join(output_folder_dir, filename)

                    for key in mosaic_dir.keys():
                        for i in range(5):
                            mosaic_dir[key] = mosaic_dir[key].replace('__', '_')

                    folder_name = city + year + desc

                    ## Tile conversion ############################################################
                    for data_name in ['DTM', 'DSM', 'ORTHO']:
                        if not should_process(ds_dict, data_name):
                            logger.info(f'Skipping {data_name} for {city}-{year}-{desc}')
                            continue

                        start = time.time()
                        desc_key = np.nan if desc == '' else desc  # if no description provided

                        # get Metadata from CRSMetadata and InputFilePointer file
                        epsg = crs_metadata.loc[(city, year, desc_key), data_name]
                        nodata_in = ds_dict[data_name]['noData']

                        temp_folder = os.path.join(os.path.dirname(os.getcwd()), 'data', 'Temp', folder_name, data_name)
                        os.makedirs(temp_folder, exist_ok=True)

                        if ds_dict[data_name]['tiles']:
                            logger.info(f'Processing {city}-{year}-{desc}: {data_name} tiles')
                            input_folder = ds_dict[data_name]['tiles']
                            input_folder = os.path.normpath(input_folder)
                            output_folder = os.path.join(temp_folder, 'tif')

                            # get file format (most frequent extension)
                            files = glob.glob(input_folder + '/**/*', recursive=True)
                            split_files = [os.path.splitext(file) for file in files]
                            exts = [split_file[1] for split_file in split_files]
                            filtered_exts = [ext for ext in exts if
                                             ext in [".xyz", ".txt", ".las", ".laz", ".jp2", ".jpg", ".tif"]]
                            ext = mode(filtered_exts) if filtered_exts else None

                            if ext in [".xyz", ".txt"]:
                                filtered_files = [file for file in files if file.endswith(ext)]
                                with rasterio.open(filtered_files[0]) as src:
                                    ras_dtype = src.dtypes[0]
                                nodata_out = default_nodata_dict.nodata_values[ras_dtype]
                                parallel_xyz_tif(xyz_file_paths=filtered_files,
                                                 output_folder_dir=output_folder,
                                                 unused_cpus=unused_cpus,
                                                 epsg=epsg, nodata_out=nodata_out,
                                                 nodata_in=nodata_in)

                            elif ext in [".las", ".laz"]:
                                logger.info('Tiles LAS/LAZ to TIF conversion')
                                filtered_files = [file for file in files if file.endswith(ext)]
                                nodata_out = default_nodata_dict.nodata_values['float32']
                                parallel_laz_tif(laz_file_paths=filtered_files,
                                                 output_folder_dir=output_folder,
                                                 unused_cpus=unused_cpus, epsg=epsg,
                                                 nodata_out=nodata_out)

                            elif ext in [".jp2", ".jpg"]:
                                logger.info('Tiles JPx to TIF conversion')
                                filtered_files = [file for file in files if file.endswith(ext)]
                                with rasterio.open(filtered_files[0]) as src:
                                    ras_dtype = src.dtypes[0]
                                nodata_out = default_nodata_dict.nodata_values[ras_dtype]
                                parallel_jpx_tif(jpx_file_paths=filtered_files,
                                                 output_folder_dir=output_folder,
                                                 unused_cpus=unused_cpus, epsg=epsg,
                                                 nodata_out=nodata_out,
                                                 nodata_in=nodata_in)
                            else:
                                output_folder = input_folder

                            if ext in [".tif"]:
                                #be sure to get files that have the correct extension
                                filtered_files = [file for file in files if file.endswith(ext)]

                                if ds_dict[data_name]['noData'] is None:
                                    # get dtype of Ortho files to mosaic to set nodata
                                    with rasterio.open(filtered_files[0]) as src:
                                        ras_dtype = src.dtypes[0]

                                    nodata_out = default_nodata_dict.nodata_values[ras_dtype]
                                else:
                                    nodata_out = ds_dict[data_name]['noData']

                            if output_folder != input_folder:
                                end = time.time()
                                logger.info(
                                    f'Tiles conversion {city}-{year}-{desc}: {data_name} -- Runtime: {end - start}')
                                logger.info(f'Number of input tiles: {len(filtered_files)}')
                                if data_name != "ORTHO":
                                    cleansed_tiles = glob.glob(
                                        os.path.join(os.path.dirname(output_folder), "xyz_cleansed", "*"))
                                    logger.info(f'Number of cleansed tiles: {len(cleansed_tiles)}')
                                out_tiles = glob.glob(os.path.join(output_folder, "*"))
                                logger.info(f'Number of converted tiles: {len(out_tiles)}')

                            ## Mosaicing ##############################################################
                            start = time.time()
                            logger.info(f'Mosaicing {city}-{year}-{desc}: {data_name}')

                            # Quality control: all tiles having same resolution
                            resolution = uniform_resolution_check(output_folder)

                            # mosaic resampling config: res shouldn't be smaller than 20cm
                            if resolution * 100 >= 100:
                                res_desc = str(int(resolution)) + 'm'
                            else:
                                res_desc = str(int(resolution * 100)) + 'cm'

                            if resolution < 0.2:
                                resolution = 0.2
                                res_desc = str(int(resolution * 100)) + 'cm'
                            else:
                                resolution = None  # for mosaicing keep native resolution

                            # rename output file (add resolution)
                            mosaic_dir[data_name] = mosaic_dir[data_name].replace('%resolution%', res_desc)

                            if data_name == 'ORTHO':

                                num_channels = get_num_channels_first_tif_in_folder(output_folder)
                                if num_channels == 3:
                                    channels = 'RGB'
                                elif num_channels == 4:
                                    channels = 'RGBI'
                                else:
                                    channels = 'undefinedchannels'
                                mosaic_dir[data_name] = mosaic_dir[data_name].replace('%channels%', channels)


                            tiles_to_mosaic(input_folder_dir=output_folder,
                                            output_file_path=mosaic_dir[data_name],
                                            resolution=resolution, epsg=epsg,
                                            nodata_out = f"{nodata_out}")

                            end = time.time()
                            logger.info(f'Mosaicing {city}-{year}-{desc}: {data_name} -- Runtime: {end - start}')
                        elif ds_dict[data_name]['mosaic']:
                            mosaic_dir[data_name] = ds_dict[data_name]['mosaic']

                        # create storage capacity
                        try:
                            shutil.rmtree(temp_folder)
                        except OSError as e:
                            logger.warning(f'Folder could not be deleted: {e.strerror}')

                    ## nDSM generation ############################################################
                    if should_process(ds_dict, 'nDSM'):
                        if (not ds_dict['nDSM']['tiles'] and not ds_dict['nDSM']['mosaic']):
                            start = time.time()
                            logger.info(f'nDSM creation {city}-{year}-{desc}')

                            # set x res of dsm in file name
                            with rasterio.open(mosaic_dir['DSM']) as src:
                                dsm_res = src.res[0]

                            if dsm_res * 100 >= 100:
                                res_desc = str(int(dsm_res)) + 'm'
                            else:
                                res_desc = str(int(dsm_res * 100)) + 'cm'

                            filename = f"{city}_{ds_dict['DSM']['year']}_{ds_dict['DSM']['description']}_nDSM_mosaic_{res_desc}.tif"
                            mosaic_dir['nDSM'] = os.path.join(output_folder_dir, filename)
                            os.makedirs(os.path.dirname(mosaic_dir['nDSM']), exist_ok=True)
                            generate_nDSM(dsm_file_path=mosaic_dir['DSM'],
                                          dtm_file_path=mosaic_dir['DTM'],
                                          ndsm_output_dir=mosaic_dir['nDSM'],
                                          nodata=default_nodata_dict.nodata_values['float32'],
                                          unused_cpus=unused_cpus,
                                          chunksize=chunksize)
                            end = time.time()
                            logger.info(f'nDSM creation {city}-{year}-{desc} -- Runtime: {end - start}')
                except Exception as e:
                    logger.warning(f'City failed: {city} {year} {desc} #failedcity\n{traceback.format_exc()} ')
                    if isinstance(e, subprocess.CalledProcessError):
                        logger.warning(f'{e} \n {e.stderr}')
                folder_name = city + year + desc
                # delete Temp folder
                try:
                    shutil.rmtree(os.path.join(root_dir, 'data', 'Temp', folder_name))
                except OSError as e:
                    logger.warning(f'Temp folder could not be deleted: {e.strerror}')

    end = time.time()
    logger.info(f'Pipeline complete -- Total Runtime: {end - pipeline_start}')
    #create_overview_log(os.path.join(root_dir, "pipeline.log"), os.path.join(root_dir, "overview.log"))


# just for running without GUI
if __name__ == '__main__':
    main_application(input_file_pointer_path=input_file_pointer_path_manuell,
                     crs_metadata_path=crs_metadata_path_manuell)
