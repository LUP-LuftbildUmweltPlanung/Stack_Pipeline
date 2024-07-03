# UserDoc
>This README provides instructions for any user to run the application. The architecture will just be referenced.

The StackPipeline tool performs various tasks related to mosaicing and stacking of raster data. It functions with various input datatypes for optical and elevation data (.tif, .jp2, .xyz, .laz, .las)

The initial functionality aims at creating a stacked raster consisting of an RGB(I) Orthophoto and a nDSM. This functionality is run through the stack_pipeline_exe.bat. The purpose of this functionality is to automize data pre-processing for usage in CNN models. This influences the pipelines settings regarding format and resampling of the raster stacks. 
>The stacking pipeline is executed by the stack_pipeline_exe.bat, the GUI.py and the pipeline.py.

In an update, the functionality was made more modular, focussing on mosaic and nDSM generation for various datasets rather than stacking. This allows the user to create mosaics of DTM, DSM and/or Orthophoto of different datatypes and hold the advantage of intelligent NoData handling and naming of output files. 
>The modular mosaicing pipeline is executed by the mosaic_pipeline_exe.bat, the mosaic_GUI.py and the mosaic_pipeline.py.



## Quickstart
>If the Pipeline is not yet installed on the computer you are using, go to the **Setup** section to find out how to install it. Both the stack pipeline and the more modular mosaic pipeline functionality are run through the .bat files in the main directory.

>Running the Pipeline:
1. Execute the stack_pipeline_exe.bat or mosaic_pipeline_exe.bat file and wait for the respective GUI to load
    - Advanced users can specify parameters in the config.py file
2. Follow the instructions in the GUI as shown in the **User Interface** section
3. Fill in missing EPSG Codes in the epsg_input_data_{DATE}.csv file.  
3. Run the pipeline and wait until the console prints Pipeline completed (if this doesn't happen it indicates an issue)
4. Check the overview.log for information afterwards. If there are failed datasets or tiles check the pipeline.log for detailed error descriptions. If necessary reach out to your friend with IT knowledge. 

>Advanced Users

1. Specify parameters in the config.py file 
2. You may run manuell_input_file_creation.py or mosaic_input_file_creation.py to create the input .json files for the pipeline.
3. Modify and complete the created CRSMetadata (location: ..data/Input/CRSMetadata)
4. Enter the paths of the InputFilePointer and the CRSMetadata file in the pipeline.py and execute it.
5. Check the overview.log for informations afterwards. If there are failed datasets or tiles check the pipeline.log for detailed error descriptions.


## Input
The stack pipeline (**pipeline.py**) is designed to handle numerous sets of data (referred to as stacks) within one run. For each run, a Digital Surface Model (DSM), Digital Terrain Model (DTM) (if a normalized Digital Surface Model (nDSM) is already available, this may be used instead) and Orthophoto (ORHTO) is needed as input. When initiating the pipeline, an input .json file for the datasets and .csv for the EPSG codes is necessary. These inputs are generated automatically through the graphical user interface (GUI). In cases where the GUI is not used, these files must be manually generated following the guidelines outlined in the DOCUMENTATION.md.

The mosaic pipeline (**mosaic_pipeline.py**) is designed to mosaic DTM, DSM and ORTHO datasets and create nDSMs if needed. The difference to the stack pipeline is that no stack is created, but each mosaicing functionality can be accessed individually through a more concise GUI. 

### InputFilePointer
Here the input raster data will be defined. For every dataset this comprises
- nDSM or DSM+DTM
- ORTHO (RGB or RGBI)

The raster data can be either a mosaic or a folder with tiles which are going to be mosaiced within the pipeline. If the inputs are tiles the folder can contain all files or multiple subfolders containing the tiles. There is no need to move the files. So far the pipeline can handle
- XYZ, TXT containing XYZ
- LAS, LAZ
- JP2, JPG, TIF

Additionally there needs to be stored metadata required to identify the dataset and name the produced files. This includes:
- cityname, year, description
- year, description for tiles to name the mosaic
- true Orthophoto or normal Orthophoto?
- output folder for the produced files
- name of the creator
- (boolean process switch for mosaic pipeline)

For the mosaic pipeline (**mosaic_pipeline.py**) the input .json file pointer is structure the same, with the addition of a boolean **process** key indicating whether this datasets should be processed (**True**) or not (**False**)





### CRSMetadata

A table where the CRS for every dataset is stored as EPSG code.


## Output and Byproducts

### Folder structure
Within the output folder defined by the user the following folder stucture is created automatically. If the year already exists a _1,_2,... is added as suffix so each dataset is stored into its own folder.
``` bash
outputfolder
└── city
    └── year
        ├── stack.tif (if run through stack pipeline)
        ├── mosaic1.tif
        ├── mosaic2.tif
        ├── ...
        └── README.md
```

### Stacks
Stack containing layers RGB(I) and nDSM. The resolution is defined in the config.py file.

### Mosaics
If the input data consists of tiles the created mosaics (DSM, DTM, nDSM, ORTHO) are also saved in the ouput folder.

### README.md
Template like file to document stack issues and reference the data source. This  provides a medium to document issues and information occuring after the creation.


## Setup

### 1. Copy the entire repository into a folder on your computer. 
### 2. Conda environment

Before running the application, you need to set up a conda environment with specific packages. 
To do this, you need to use the provided environment.yml file using your favorite Python package management system.
Using Anaconda Prompt, the environment can be installed by providing the path to the environment.yml file as follows: 
```
conda env create -f PATH:\PATHTOPIPELINE\environment.yml
```


If you setup the pipeline on a new device you need to alter the config.py to be able to run the Pipeline with the exe.bat and without a console. Please check and update the paths accordingly:
### 3. Config.py
- path_activate_conda: To start the conda environment within the mosaic_pipeline_exe.bat of stack_pipeline_exe.bat file, you need to define the path to "miniconda3\condabin\activate.bat". Please ensure that the path is correctly defined.
- condaenvironment: The name of the created environment
- (optional) chunksize (for xarray), unused_cpu and stack_resolution (output: in meter)

### Assumptions
All files within one input folder have the same crs

## Technical Specifications

This is a simple overview over the implementation details of the pipeline. For further information refer to the DOCUMENTATION.md

Function                | Resampling                                                            | Compression    | Resolution
------------------------|-----------------------------------------------------------------------|----------------|---------
Tile conversion (to TIF)| None                                                                  | None           | Input resolution
Mosaicing               | if < 20cm : nearest                                                   | LZW            | min. 20 cm
nDSM creation           | DTM : nearest                                                         | LZW            | DSM
Stacking                | ORTHO : nearest,<br> nDSM : cubic (upsampling) nearest (downsampling) | LZW            | config.py





## Further Information

## Issues
>Please document any issues and solutions here


