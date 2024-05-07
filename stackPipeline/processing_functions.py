# -*- coding: utf-8 -*-

#nodata check gdal xyz to tif
#progress anschauen
"""
Created on Mon Jan 30 15:03:46 2023

@author: QuadroRTX
"""
import geowombat as gw
import numpy as np
import xarray as xr
import pdal
import json
import glob
import os
import logging
import pyproj
from scipy import stats
import pandas as pd
import multiprocessing
import traceback
import rasterio
import subprocess 
import random
import math
import re


script_directory = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_directory)

   
def xyz_to_tif(xyz_file_path: str, output_folder_dir: str,
               epsg: int, nodata_in=None, nodata_out=None) -> None:
    """
    Converts XYZ files to GeoTIFF format using GDAL.


    Args:
        xyz_file_path (str):
            Path to the xyz file.
        output_folder_dir (str): 
            The path to the output directory where TIFS are
            wrote to.
        epsg (int): 
            The EPSG code for the output coordinate reference system.
        nodata_out: 
            Nodata value for the output tif file. All missing data
            will be filled with this value. This value will also be
            written into the files metadata
    Returns:
        None
    """  
    
    # set up output path
    file_name = os.path.basename(xyz_file_path)
    file_name_tif = os.path.splitext(file_name)[0]+'.tif'
    tif_file_path = os.path.join(output_folder_dir, file_name_tif)
    
    # complex try except structure to avoid cleansing every tile
    # and because gdal warp sometimes raise errors when ungridded (but sometimes not)
    try:
        
        custom_warp_xyz_to_tif(xyz_file_path=xyz_file_path, 
                        tif_file_path=tif_file_path, epsg=epsg,
                        nodata_out=nodata_out, nodata_in=nodata_in)
        
    except:
        
        try:  
            
            # cleansing data to make it gdal available
            # save the cleansed tile to Temp to not overwrite the raw
            clean_folder_dir = os.path.dirname(output_folder_dir)
            os.makedirs(clean_folder_dir, exist_ok=True)
            
            clean_file_name = os.path.basename(xyz_file_path)
            clean_xyz_path = os.path.join(clean_folder_dir, 'xyz_cleansed',
                                         clean_file_name)
            
            xyz_cleansing(xyz_file_path, clean_xyz_path)
            logger.debug(f'XYZ file cleansed: {xyz_file_path}')
            
            custom_warp_xyz_to_tif(xyz_file_path=clean_xyz_path,
                                   tif_file_path=tif_file_path, 
                                   nodata_out=nodata_out, nodata_in=nodata_in)
            
        except:
            
            logger.warning(f'XYZ transformation failed.%f%{xyz_file_path}%f% #failedtile \n{traceback.format_exc()}')

                
def custom_warp_xyz_to_tif(xyz_file_path, tif_file_path, epsg, nodata_out, nodata_in = None):
    """
    Improved gdal.Warp function with enhanced quality control to detect
    corrupted XYZ data during TIFF file processing. It now includes exception
    raising suitable not present in default gdal suited for try-except blocks.

    Args:
        xyz_file_path (str): 
            Path to the xyz file.
        tif_file_path (str): 
            The path path of the tif file which is created.
        epsg (int): 
            The EPSG code for the output coordinate reference system.
        nodata_out: 
                Nodata value for the output tif file. All missing data
            will be filled with this value. This value will also be
            written into the files metadata.
    Returns:
        None
    """  
    # setup input nodata handling for GDAL
    if nodata_in:
        
        nodata_in_arg = ["-srcnodata", str(nodata_in)]
        
    else:
        
       nodata_in_arg = [] 
    
    # Construct the GDAL CMD command
    command = [
        'gdalwarp',
        '-s_srs',
        f'EPSG:{epsg}',
        *nodata_in_arg,
        '-dstnodata',
        str(nodata_out),
        xyz_file_path,
        tif_file_path
        ]

    # Run the GDAL subprocess
    # Special ERROR raising make it available for the logger
    try:
        
        subprocess.run(command, capture_output=True, check=True)
        
    except subprocess.CalledProcessError as e:
        
        raise e
        
    # quality controll
    with rasterio.open(tif_file_path) as raster_ds:
        
        pixel_width = abs(raster_ds.transform[0])
        pixel_height = abs(raster_ds.transform[4])
          
    # Check if pixel size indicates something went wrong
    if pixel_width != pixel_height:
        
        # unlock file
        del raster_ds 
        os.remove(tif_file_path)
        raise RuntimeError(f'{xyz_file_path} was not converted properly into .tif file. '\
                         'Pixel width and legth are not equal. '\
                         'Check if the .xyz file has an error. ')
                     
                           
def xyz_cleansing(file_path, output_dir):
    """
    Cleans and overwrites XYZ files by filtering erroneous points that are
    off-grid. The filtering process involves determining the probable origin
    and resolution of the grid, and then removing all points that do not lie
    on this hypothetical grid. A point is cosnidered on the grid if it is within
    a distance of 0.03, measured in terms of resolution, from the grid.

    Args:
        file_path (str): 
            The path to the XYZ file.
        output_dir (str): 
            The path to write the created files to.
    Returns:
        None
    """
    df = pd.read_csv(file_path, sep =' ', names=['x', 'y', 'z'])
    # sorting wrong sorted values: other option would be deleting
    df.sort_values(['y', 'x'], inplace=True)
    
    # resolution derivation
    # most frequent distance between points = resolution 
    # assumes dx = dy
    
    x_val = df['x']
    # round bc of floating point arethmetic
    resolution = stats.mode(np.diff(x_val).round(2), keepdims=True).mode[0] # keep_dims bc of scipy bug
    
    # origin derivation
    # origin = min x/y value
    # to prevent choosing an outlier a threshold of 50 counts is defined
    threshold = 50
    x_val, counts = np.unique(df['x'], return_counts = True)
    x_origin = x_val[counts > threshold].min()
    y_val, counts = np.unique(df['y'], return_counts = True)
    y_origin = y_val[counts > threshold].min()
    
    logger.debug(f'resolution: {resolution}')
    logger.debug(f'x origin :{x_origin}')
    logger.debug(f'y origin :{y_origin}')

    # Calculate the distance from the virtuell the grid
    df['x_grid_dist'] = ((df['x'] - x_origin) / resolution) % 1
    df['y_grid_dist'] = ((df['y'] - y_origin) / resolution) % 1
    
    # remove all points which are further away then 4 mm
    # this way rounding in a second step is no problem to ensure consistency
    df_valid = df[((np.isclose(df['x_grid_dist']*resolution, 0, atol=0.004) |
                   np.isclose(df['x_grid_dist']*resolution, resolution, atol=0.004))) &
                  ((np.isclose(df['y_grid_dist']*resolution, 0, atol=0.004) |
                   np.isclose(df['y_grid_dist']*resolution, resolution, atol=0.004)))]
    
    # round to align slightly offgrid points which are treated as valid        
    df_valid['x'] = df_valid['x'].round(3)
    df_valid['y'] = df_valid['y'].round(3)
    
    df_valid[['x','y','z']].to_csv(output_dir, index = False, header= False,
                                       sep = ' ', float_format='%.3f')
    

def laz_to_tif(laz_file_path: str, output_folder_dir: str, epsg :int, nodata_out):
    """
    Convert LAZ file to GeoTIFF. An XYZ file is created as an intermediate step.
    Assumes equal CRS for all LAZ files.

    Args:
        laz_file_path (str): 
            Path to laz file.
        output_folder_dir (str): 
            The path to the directory where the results are written to.
        epsg (int): 
            The EPSG code for the output coordinate reference system.

    Returns:
        None
    """
        

    # Set up temporary file path
    file_name = os.path.basename(laz_file_path)
    file_name_xyz = os.path.splitext(file_name)[0] + '.xyz'
    xyz_folder_dir = os.path.join(os.path.dirname(output_folder_dir), 'laz_to_xyz')
    os.makedirs(xyz_folder_dir, exist_ok=True)
    xyz_file_path = os.path.join(xyz_folder_dir, file_name_xyz)
    
    # Create Pipeline to translate .LAZ to XYZ
    pipeline_pdal = [
        {
            'type' : 'readers.las',
            'filename' : laz_file_path
        },
        {
            'type' : 'writers.text',
            'format' : 'csv',
            'order' : 'X,Y,Z',
            'keep_unspecified' : 'false',
            'filename' : xyz_file_path,
            'write_header' : 'false',
            'delimiter' : ' '}   
    ]
    
    # Execute Pipeline
    try:
        
        pipeline = pdal.Pipeline(json.dumps(pipeline_pdal))
        pipeline.execute()
        
    except:
        
        logger.warning(f'LAZ transformation failed. %f%{laz_file_path}%f% #failedtile\n{traceback.format_exc()}')

    # Convert the created XYZ to tif
    xyz_to_tif(xyz_file_path, output_folder_dir=output_folder_dir, epsg=epsg,
               nodata_out = nodata_out)


def jpx_to_tif(jpx_file_path: str, output_folder_dir: str, epsg:int ,
               nodata_in=None, nodata_out=None):
    """
    Converts JP2 and JPG (JPX) files to GeoTIFF format using GDAL.

    Args:
        jpx_file_path (str): 
            Path to the jpx file.
        output_folder_dir (str): 
            The path to the output directory where TIFS are
            wrote to.
        epsg (int): 
            The EPSG code for the output coordinate reference system.
        nodata_out: 
            Nodata value for the output tif file. All missing data
            will be filled with this value. This value will also be
            written into the files metadata
    Returns:
        None
    """  
    # set up output path
    file_name = os.path.basename(jpx_file_path)
    file_name_tif = os.path.splitext(file_name)[0] + '.tif'
    tif_file_path = os.path.join(output_folder_dir,  file_name_tif)
    
    if nodata_in:
        nodata_in_arg = ["-srcnodata", str(nodata_in)]
    else:
       nodata_in_arg = [] 
    
    # Construct the subprocess command
    command = [
        'gdalwarp',  
        '-s_srs',
        f'EPSG:{epsg}',
        *nodata_in_arg,
        '-dstnodata',
        str(nodata_out),
        jpx_file_path,
        tif_file_path
        
    ]
   
    # Run the subprocess
    try:
        subprocess.run(command, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.warning(f'JPx transformation failed.%f%{jpx_file_path}%f% #failedtile\n{e} \n {e.stderr}')

    
def parallel_xyz_tif(xyz_file_paths: list, output_folder_dir: str, epsg: int,
                      nodata_in=None, nodata_out=None, unused_cpus= 2):
    """
    Applies xyz_to_tif for a list of input files using multiprocessing.
    
    Args:
        xyz_file_paths (list): 
            List of input file paths.
        output_folder_dir (str): 
            The path to the folder where all TIFS are saved.
        epsg (int): 
            The EPSG code for the output coordinate reference system.

    Returns:
        None
    """
    with multiprocessing.Pool(multiprocessing.cpu_count()- unused_cpus) as pool:
        
        args_list =  [(f, output_folder_dir, epsg, nodata_in, nodata_out) for f in xyz_file_paths]
        pool.starmap(xyz_to_tif, args_list)


def parallel_laz_tif(laz_file_paths: list, output_folder_dir: str, epsg: int ,
                     nodata_out, unused_cpus=2):
    """
    Applies laz_to_tif for a list of input files using multiprocessing.
    
    Args:
        laz_file_paths (list): 
            List of input file paths.
        output_folder_dir (str): 
            The path to the folder where all TIFS are saved.
        epsg (int): 
            The EPSG code for the output coordinate reference system.

    Returns:
        None
    """
    with multiprocessing.Pool(multiprocessing.cpu_count()-unused_cpus) as pool:
        
        args_list =  [(f,output_folder_dir, epsg, nodata_out) for f in laz_file_paths]
        pool.starmap(laz_to_tif, args_list)



def parallel_jpx_tif(jpx_file_paths: list, output_folder_dir: str, epsg: int ,
                     nodata_in=None, nodata_out=None, unused_cpus = 2):
    """
    Applies jpx_to_tif for a list of input files using multiprocessing.
    
    Args:
        jpx_file_paths (list):
            List of input file paths.
        output_folder_dir (str): 
            The path to the folder where all TIFS are saved.
        epsg (int): 
            The EPSG code for the output coordinate reference system.

    Returns:
        None
    """
    with multiprocessing.Pool(multiprocessing.cpu_count()-unused_cpus) as pool:
        
        args_list =  [(f,output_folder_dir, epsg, nodata_in,  nodata_out) for f in jpx_file_paths]
        pool.starmap(jpx_to_tif, args_list)
    
       
def tiles_to_mosaic(input_folder_dir, output_file_path, epsg : int, resolution = None,
                    nodata_out = None, dtype_out = None ):
    """
    All TIF files within a folder and it's subfolders are mosaiced using gdal.Warp. If
    specified another resolution can be set for the mosaic (keep in mind the
    resampling algorithm).
    Args:
        input_folder_dir (str):
            The path to the folder/subfolders where all TIFS are.
        output_file_path (str):
            The file path to save the  mosaic.
        gdal_dtype :
            GDAL data type for the input and output data.
        resolution (float, int):
            Size for each pixel. If None the input resolution will be used.

    """
         
    # get all files from tiles directory and all subdirs    
    input_folder_dir = os.path.normpath(input_folder_dir)
    file_list = glob.glob(input_folder_dir+'/**/*.tif', recursive=True)
    file_list = [os.path.basename(file) for file in file_list]
    # set relativ path
    relativ_file_paths = [file.replace(f'{input_folder_dir}\\', '') for file in file_list]
    
    # change working dir to make relative paths available
    init_cwd = os.getcwd() # to reset later
    os.chdir(input_folder_dir)
        
    if not relativ_file_paths:
        
        logger.warning(f'Mosaicing failed because there were no input files. {input_folder_dir}')

    args = []
    if resolution:
        
        args = args + ['-tr', str(resolution), str(resolution)]
        
    if dtype_out:
        
        args = args + ['-ot', dtype_out]
        
    if nodata_out:
        
        args = args + ['-dstnodata', nodata_out]
        
        
    # bc Create Process (subprocess) has characters limit ~32.000 for input
    # This limit is exceeded by to many file paths
    # approach to solve this issue:
    # 1. Calculate total length file paths
    # 2. Create sub mosaics if limit is exceeded (limit is set lower 28.000 )
    # 3. include sub mosaics in last mosaicing step
    # 4. delete sub mosiacs
    
    str_len_files = sum([len(file) for file in relativ_file_paths])
    if str_len_files > 28000:
        
        overlap_files_faktor = math.ceil(str_len_files/28000)
        splitted_lst = split_list(relativ_file_paths, overlap_files_faktor)
        
    else:
        
        splitted_lst = [relativ_file_paths]
        
    temp_mosaics = []
    for idx, file_lst in enumerate(splitted_lst):
        
        # include submosaics(if exist) when mosacing the last item of the list
        if idx+1 == len(splitted_lst):
            
            gdal_out_path = output_file_path
            file_lst = file_lst + temp_mosaics
            
        else:
            
            # create sub mosaics (~tempmosaics)
            gdal_out_path = os.path.join(os.path.dirname(output_file_path),
                                        f'mosaicsub{idx}.tif')
            temp_mosaics.append(gdal_out_path)
        
        command = [
        'gdalwarp',
        '-s_srs', 
        f'EPSG:{epsg}',
        *args,
        '-r', 'near',
        '-co', 'COMPRESS=LZW',
        '-co', 'BIGTIFF=YES',
        '-co', 'TILED=YES',
        *file_lst,
        gdal_out_path]
        
        # Run the subprocess
        try:
            
            subprocess.run(command, capture_output=True, check=True, close_fds=True)
            
        except subprocess.CalledProcessError as e:
           
            raise e
            
    # delete the intermediate submosaics       
    [os.remove(temp_mosaic) for temp_mosaic in temp_mosaics]
    command = ['gdaladdo', '-r', 'nearest', '-ro', output_file_path,
               *['4', '8', '16', '32', '64', '128'],'--config', 'COMPRESS_OVERVIEW', 'LZW']
    
    # Run the subprocess
    try:
        
        subprocess.run(command, capture_output=True, check=True)
        
    except subprocess.CalledProcessError as e:
        
        raise e
        
    # reset cwd
    os.chdir(init_cwd)


def generate_nDSM (dsm_file_path, dtm_file_path, ndsm_output_dir,
                   nodata, unused_cpus=2, chunksize = 4096):

    
    #open and resample DTM raster with DSM as reference image for resolution       
    with gw.config.update(ref_image=dsm_file_path,  bigtiff='YES'):
        with gw.open(dtm_file_path, resampling='nearest', chunks=chunksize) as dtm_resample: 
            logger.debug('resampled DTM to match DSM')
            with gw.open(dsm_file_path, chunks=chunksize) as dsm_array:
                
                # Xarray drops attributes, get attributes here
                attrs = dsm_array.attrs.copy()
            
                #get nodata values 
                dsm_nodata=dsm_array.attrs['_FillValue']
                dtm_nodata=dtm_resample.attrs['_FillValue']
                
                #substract DTM from DSM where neither are noData
                data_mask_nodata = np.logical_and(dsm_array!=dsm_nodata,
                                                         dtm_resample!=dtm_nodata)
                nDSM = xr.where(data_mask_nodata, dsm_array-dtm_resample, nodata)
                
                
        #test and logger.debug warning if DSM was lower than DTM by more than 10m 
        nDSM_test_negative = xr.where(nDSM==nodata,0,nDSM)#.values
        if ((nDSM_test_negative<-10).any()):
            logger.debug('!!!Difference between DSM & DTM is greater than 10m in some places!!!')
        
         
        # set nDSM values <=0 to 0  
        nDSM_no_zero = xr.where((nDSM <= 0) & (nDSM != nodata), 0, nDSM)
        logger.debug('nDSM values smaller than 0 were set to 0') 
    
        #export nDSM 
        export_raster = nDSM_no_zero.assign_attrs(**attrs).astype('float32')
        
        export_raster.gw.save(ndsm_output_dir, overwrite=True, nodata=nodata,
                              num_workers = multiprocessing.cpu_count()- unused_cpus)
        
        compress_ndsm_dir = ndsm_output_dir + 'temp.tif'
        # run gdal subprocess
        command = ['gdal_translate', '-co', 'COMPRESS=LZW', '-co',
                              'BIGTIFF=YES', ndsm_output_dir,
                              compress_ndsm_dir]
        # Run the subprocess
        try:
            subprocess.run(command, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise e
        # Delete the uncompressed raster file
        os.remove(ndsm_output_dir)
        # Rename the compressed raster
        os.rename(compress_ndsm_dir, ndsm_output_dir)
        # pyramids
        command = ['gdaladdo', '-r', 'nearest', '-ro', ndsm_output_dir,
                   *['4', '8', '16', '32', '64', '128'],'--config', 'COMPRESS_OVERVIEW', 'LZW']
        # Run the subprocess
        try:
            subprocess.run(command, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise e


def stacking(ndsm_file_path, ortho_file_path,stack_output_dir,
                            nodata, stack_resolution,
                            ndsm_resampling : str, chunksize = 4096, unused_cpus=2):
    """
    Args:
        ndsm_file_path : TYPE
            DESCRIPTION.
        ortho_file_path : TYPE
            DESCRIPTION.
        stack_output_dir : TYPE
            DESCRIPTION.
        nodata : TYPE
            DESCRIPTION.
        stack_resolution : float, int, str
            Stack output resolution. Can be either a number or a path to
            a reference image.
        ndsm_resampling: str
            Resampling method used in geowombat for the ndsm
        chunksize : TYPE, optional
            DESCRIPTION. 

    Returns
        None.
    """
 
    with gw.config.update(ref_bounds=ndsm_file_path, ref_res = stack_resolution,
                          ref_crs = ndsm_file_path, bigtiff='YES'):
        
        with gw.open(ndsm_file_path, chunks=chunksize, resampling=ndsm_resampling) as ndsm_array:
            # get no data value 
            src_nodata = ndsm_array.attrs['_FillValue']
            
            # set no data values to defined nodata
            ndsm_array=ndsm_array.gw.set_nodata(src_nodata=src_nodata, dst_nodata=nodata)
            # set ndsm values below 0 to 0 
            ndsm_array = xr.where(ndsm_array<=0, 0, ndsm_array)
            
        
        with gw.open(ortho_file_path, chunks=chunksize, resampling='nearest') as ortho_array:
            ortho_array=ortho_array.gw.set_nodata(src_nodata=ortho_array.attrs['_FillValue'],
                                                  dst_nodata=nodata)
            ortho_attrs=ortho_array.attrs
            
        # multiply by 256 to stretch and perform uint16 conversion
        ortho_array=xr.where(ortho_array!=nodata,(ortho_array*256), nodata).astype('uint16')
        ndsm_array=xr.where(ndsm_array!=nodata,(ndsm_array*256), nodata).astype('uint16')
        
        # flexibel band numbers to avoid duplicate band names
        band_nums = ortho_array.shape[0] + ndsm_array.shape[0]
        band_names = list(range(1, band_nums+1))
        
        stack=xr.concat((ortho_array, ndsm_array), dim='band').assign_coords(band=band_names).chunk(chunks=chunksize)
        
        #define necessary attributes and prepare for export :assumes same crs
        attrs={'crs':ortho_attrs['crs'], 'transform':ortho_attrs['transform'],'_FillValue':ortho_attrs['_FillValue'], 'res':ortho_attrs['res']}
        export_raster = stack.assign_attrs(attrs)

        export_raster.gw.save(stack_output_dir,
                              num_workers = multiprocessing.cpu_count()-unused_cpus)
        compress_stack_dir = stack_output_dir + 'temp.tif'
        
        # run gdal subprocess
        command = ['gdal_translate', '-co', 'COMPRESS=LZW', '-co',
                              'BIGTIFF=YES', stack_output_dir,
                              compress_stack_dir]
            
        # Run the subprocess
        try:
            subprocess.run(command, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise e
        # Delete the uncompressed raster file
        os.remove(stack_output_dir)
        # Rename the compressed raster
        os.rename(compress_stack_dir, stack_output_dir)
        #build overviews
        logger.debug('building pyramids for compressed stack...')
        command = ['gdaladdo', '-r', 'nearest', '-ro', stack_output_dir,
                   *['4', '8', '16', '32','64', '128'],'--config', 'COMPRESS_OVERVIEW', 'LZW']
        # Run the subprocess
        try:
            subprocess.run(command, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise e      
    

    
def uniform_resolution_check(folder_dir):
    files = glob.glob(folder_dir + '/**/*', recursive=True)
    filtered_files = [file for file in files if file.endswith('.tif')]
    resolution = []
    for file in filtered_files:
        with rasterio.open(file) as src:
            resolution.append(src.res)
       
    unique_res = set([item for sublist in resolution for item in sublist])
    
    if len(unique_res) != 1:
        logger.warning(f'Uneqaul resolution : res: {unique_res}: {folder_dir}')
        raise RuntimeError('Not all rasters had the same resolution. Check if'\
                           ' to_tif transformation was succesful')
    else:
        logger.debug(f'Uniform Resolution confirmed: {resolution[0][0]}')
        return abs(resolution[0][0])
  
    
def get_num_channels_first_tif_in_folder(folder_dir):
    """
    Gets the first tif file of the folder (including subfolders). Returns
    the number of channels. Assumes that all tifs in this folder have the same
    number of channels so the first tif is a representiv sample.
    """
    files = glob.glob(folder_dir + '/**/*', recursive=True)
    filtered_files = [file for file in files if file.endswith('.tif')]
    with rasterio.open(filtered_files[0]) as src:
        num_channels = src.meta['count']
    return num_channels

    
def read_laz_epsg(file):
    pipeline_pdal = [file, {'type' : 'filters.info'}]
    pipeline = pdal.Pipeline(json.dumps(pipeline_pdal))
    pipeline.execute()
    metadata = pipeline.metadata
    try:
        crs_laz = pyproj.CRS(metadata['metadata']['filters.info']['srs']['horizontal']).to_epsg()
    except:
        crs_laz = None
    return crs_laz

    
def get_epsg_folder(path):
    # get all files
    if os.path.isdir(path):
        files = glob.glob(path + '/**/*.*', recursive=True)
    else:
        files = [path]
    
    # ensure only one relevant filetype in the folder. Create list of files
    filetypes = [os.path.splitext(f)[-1] for f in files]
    filetypes = [f for f in filetypes if f in ['.xyz','.tif', '.jpg', '.jp2', '.png', '.laz', '.las']]
    filetype = filetypes[0] if len(set(filetypes)) == 1 else None
    if filetype in ['.xyz', None]:
        return None
    files = [f for f in files if f.endswith(filetype)]
    if not files:
        logger.warning('No files found')
        return
    # seperate laz detection. Sample approach bc not performant
    if filetype in ['.las', '.laz']:
        files = random.sample(files, 3)
        epsg = None
        for file in files:
            # try except bc pdal is creating issues
            try:
                epsg = read_laz_epsg(file)
                break
            except:
                pass
    # check all crs for the rest. Return only if exactly one CRS is defined.
    else:
        if len(files) >= 10:
            files = random.sample(files, 10)
        for file in files:
            epsg = []
            with rasterio.open(file) as dataset:
                crs = dataset.crs
                if crs:
                    epsg.append(crs.to_epsg())
        if len(set(epsg)) == 1:
            epsg = list(set(epsg))[0]
        else:
            epsg = None
            
    
                
    return epsg        
    

def create_temp_folders(json_file_path):
    # Create Temp and Ouput folders : Selection must be made
    with open(json_file_path, 'r') as f:
        input_data_paths = json.load(f)
        for city in input_data_paths.keys():
            for year in input_data_paths[city].keys():
                for desc in input_data_paths[city][year].keys():
                    dataset = city+year+desc
                    temp_dir = os.path.join(root_dir,'data', 'Temp', dataset)
                    os.makedirs(os.path.join(temp_dir, 'DTM', 'laz_to_xyz'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'DTM', 'tif'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'DTM', 'xyz_cleansed'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'DSM', 'laz_to_xyz'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'DSM', 'tif'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'DSM', 'xyz_cleansed'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'nDSM', 'laz_to_xyz'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'nDSM', 'tif'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'nDSM', 'xyz_cleansed'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'ORTHO', 'tif'), exist_ok=True)
                    
            
                    


def setup_metadata_readme(out_dir, creator='noinfo', city='noinfo', year='',
                          description=''):
    with open(os.path.join(root_dir,'templates/metadata_README.md'), 'r') as reader:
        lines = reader.readlines()
    # try except to avoid overwriting using write mode x
    try:
        with open(out_dir, 'x') as writer:
            for line in lines:
                out_line = (line.replace('%creator%', creator))
                out_line = (out_line.replace('%city%', city))
                out_line = (out_line.replace('%year%', year))
                out_line = (out_line.replace('%description%', description))
                
                writer.write(out_line)
    except:
        pass


def split_list(a, n):
    # from stackoverflow
    k, m = divmod(len(a), n)
    return list(a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def my_logger(file_path:str, name: str ):
    """
    Create a logger object with the given name and configure it to log messages
    to a file and the console.

    Args:
        name (str): 
            name of the logger. Preferred: __name__
        file_path (str):
            path where the log file is created
    Returns:
        logger
    """
    
    log = file_path
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Create a file handler

    
    # Add a handler to print to the log file
    file_handler = logging.FileHandler(log)
    log_formatter = logging.Formatter(fmt='%(name)s :: %(levelname)s :: %(asctime)s :: %(message)s')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)    
    logger.addHandler(file_handler)
    
    # Add a handler to print to the console
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(fmt='%(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    return logger


def create_overview_log(log_in_dir, overview_dir):

    with open(log_in_dir, 'r') as file:
        log_lines = file.readlines()


    filtered_log_lines = []
    warning_counter = 0
    failed_ds_counter = 0
    failed_ds = []
    failed_tile_counter = 0
    failed_tiles = []
    

    
    add_line = False
    for line in log_lines:
        if ':: INFO ::' in line:  # Change 'ERROR' to the desired logging level
            add_line = True
        if any([element in line for element in [':: WARNING ::',"':: DEBUG ::'"]]):
            add_line = False
               
        if add_line:
            filtered_log_lines.append(line)
        
        if 'Pipeline process started' in line:
            # only print last run
            filtered_log_lines = []
            filtered_log_lines.append(line)
            warning_counter = 0
            failed_ds_counter = 0
            failed_ds = []
            failed_tile_counter = 0
            failed_tiles = []
        
        if ':: WARNING ::' in line:
            warning_counter += 1
            if '#failedcity' in line:
                failed_ds_counter +=1
                re_pattern = r'%ds%(.*?)%ds%'
                failed_ds.append(re.findall(re_pattern, line)[0])
            if "#failedtile" in line:
                failed_tile_counter += 1
                re_pattern = r'%f%(.*?)%f%'
                failed_tiles.append(re.findall(re_pattern, line)[0])
           
    with open(overview_dir, 'w') as file:
        file.writelines(filtered_log_lines)
        file.write(f'\n{warning_counter} Warning(s)\n\n')
        file.write(f'{failed_ds_counter} Failed dataset(s)\n')
        file.write('\n'.join(failed_ds))
        file.write(f'\n\n{failed_tile_counter} Failed tile(s)\n')
        file.write('\n'.join(failed_tiles))
        
def save_json_to_file(json_filename, data):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(json_filename), exist_ok=True)

    # Write the JSON data to the file
    with open(json_filename, "w") as json_file:
        json.dump(data, json_file, indent=4)

    # Print the path where the JSON file is saved
    print(f"JSON data has been saved to \n{json_filename}")

logger = my_logger(os.path.join(root_dir,'pipeline.log'), __name__)
