# UserDoc
>This README provides instructions for any user to run the application. The architecture will just be referenced.

This tool is creating a stacked raster consisting of an Ortho photo and a nDSM. The main goal is to provide a preprocessing tool for the CNN models. The entire process, known as a Pipeline, is thus designed and optimized to achieve this specific objective. This influences the pipelines settings regarding format and resampling of the raster stacks.

The pipeline is capable of processing multiple datasets as a batch process. If you make use of this choose a computer with sufficient hardware and keep in mind that the process can take up to several days depending on the data size.

## Quickstart
>If the Pipeline is not yet installed on the computer you are using, go to the **Setup** section to find out how to install it.

>Running the Pipeline:
1. Execute the exe.bat file and wait for the GUI to load
    - Advanced users can specify parameters in the config.py file
2. Follow the instructions in the GUI as shown in the **User Interface** section
3. The pipeline takes a couple of hours per dataset depending on the size. Wait till the console prints Pipeline completed (if this doesn't happen it indicates an issue)
4. Check the overview.log for informations afterwards. If there are failed datasets or tiles check the pipeline.log for detailed error descriptions. If necessary reach out to your friend with IT knowledge. 

>Advanced Users

1. Specify parameters in the config.py file 
2. Run manuell_input_file_creation.py to create the Input files
3. Modify and complete the created CRSMetadata (location: ..data/Input/CRSMetadata)
4. Enter the paths of the InputFilePointer and the CRSMetadata file in the pipeline.py and execute it.
5. Check the overview.log for informations afterwards. If there are failed datasets or tiles check the pipeline.log for detailed error descriptions.



## Input
The pipeline is structured to handle numerous sets of data (referred to as stacks) within one run. When initiating the pipeline, only two inputs are necessary. These inputs are generated automatically through the graphical user interface (GUI), alleviating the user from the responsibility of understanding the file creation process. Instead, the user's focus remains solely on the file content. In cases where the GUI is not used, these files must be manually generated following the guidelines outlined in the DOCUMENTATION.md.

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



### CRSMetadata

A table where the CRS for every dataset is stored as EPSG code.


## Output and Byproducts

### Folder structure
Within the output folder defined by the user the following folder stucture is created automatically. If the year already exists a _1,_2,... is added as suffix so each dataset is stored into its own folder.
``` bash
outputfolder
└── city
    └── year
        ├── stack.tif
        ├── mosaic1.tif
        ├── mosaic2.tif
        ├── ...
        └── README.md
```

### Stacks
Stack containing layers RGB(I) and nDSM. The resolution is defined in the config.py file.

### Mosaics
If the input data consists of tiles the created mosaics are also saved in the ouput folder.

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
- path_activate_conda: To start the conda environment within the exe.bat file, you need to define the path to "miniconda3\condabin\activate.bat". Please ensure that the path is correctly defined.
- condaenvironment: The name of the created environment
- (opt) chunksize (for xarray), unused_cpu and stack_resolution (output: in meter)

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


