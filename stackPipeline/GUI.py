## GUI maily made with CHATGPT: no proper knowledge of tkinter

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import pandas as pd
import datetime
import subprocess
import platform
import threading
import customtkinter

# Get the absolute path of the current script and its parent directory
script_directory = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_directory)

# Add the project root to the Python path
sys.path.append(root_dir)

# Now use absolute imports from the project root
from processing.processing_functions import get_epsg_folder, save_json_to_file
import mosaic_pipeline

# Change the working directory to the script directory
# Note: Changing the working directory can have side effects,
# so be cautious about how this might affect other parts of your code
os.chdir(script_directory)

customtkinter.set_appearance_mode("dark")



class GUI:
    def __init__(self):
        # self.root = tk.Tk()
        self.current_window = None
        self.input_dict = {}
        
        self.header_args = {"font":("Frutiger", 40, "bold"),}
        self.intro_args = {"font":("Frutiger", 18, "roman")
                           , "fg_color": "white", "text_color" : "black"}
        self.text_args = {"font":("Frutiger", 15, "roman")}
        
        self.root = customtkinter.CTk()

        self.root.geometry("900x900")
        self.root.minsize(400, 300)  # Set minimum window size
        self.root.title("Stack Pipeline")
        self.icon_path = "../Images/icon.ico"
        test = os.path.normpath(self.icon_path)
        self.root.iconbitmap(os.path.normpath(self.icon_path))
        
        
        
        
        
        self.root2 = customtkinter.CTk()
        self.root2.withdraw()
        self.root2.geometry("900x800")
        self.root2.minsize(400, 300)  # Set minimum window size
        self.root2.title("Stack Pipeline - EPSG")
        self.root2.iconbitmap(os.path.normpath("../Images/icon.ico"))
        
        
        self.create_window_1()
        
        
        # init vars which should not be overwritten for every new data set
        self.output_folder = None

    def create_window_1(self):
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root)
        
        self.current_window.pack(fill="both", expand=True)

        header = customtkinter.CTkLabel(master=self.current_window, text="__STaRT__", **self.header_args)
        header.pack(pady=(20, 10))
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Create a new InputFilePointer file(JSON)\n"\
                                                "or run the pipeline if the JSON file already exists.",
                                                **self.intro_args)
        question_label.pack(pady=(20, 10))
        
        no_button = customtkinter.CTkButton(master=self.current_window, text="Create new JSON", command=self.create_window_cityname)
        no_button.pack(pady=10)
        
        yes_button = customtkinter.CTkButton(master=self.current_window, text="Run the pipeline", command=self.create_window_json_in)
        yes_button.pack(pady=10)

        

    def create_window_cityname(self):
        self.destroy_current_window()
        # reset all storage variables
        
        self.tiles_folder_path_dtm = None
        self.tiles_folder_path_dsm = None
        self.tiles_folder_path_ortho = None
        self.tiles_folder_path_ndsm = None
        self.mosaic_path_dtm = None
        self.mosaic_path_dsm = None
        self.mosaic_path_ortho = None
        self.mosaic_path_ndsm = None
        self.stack_year = None
        self.stack_desc = "undefined"
        self.dtm_year = None
        self.dsm_year = None
        self.dsm_desc= "undefined"
        self.ndsm_year = None
        self.ndsm_desc= "undefined"
        self.ortho_year = None
        self.ortho_desc= "undefined"
        self.ortho_dop_top = None
        

        self.current_window = customtkinter.CTkFrame(master=self.root)
        self.current_window.pack(fill="both", expand=True)
        header = customtkinter.CTkLabel(master=self.current_window, text="STACK", **self.header_args)
        header.pack(pady=(20, 10))
        text="Add a new dataset to build a stack.\n"\
            "The entered information will be used to identify the dataset and name the stack.\n"\
            "The mosaics and the stack will be saved into the output folder.\n"\
            "Automatically, a city-named folder will be created in the output folder\n"\
            "so multiple datasets can be saved into the same output folder\n"\
            "Your name will be written into the stack documentation"
        question_label = customtkinter.CTkLabel(master=self.current_window,
                                                text=text,
                                                **self.intro_args)
        question_label.pack(pady=(20, 10))
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter your Name",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
            
        self.text_box_readme_name = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_readme_name.pack(pady=10)
        self.text_box_readme_name.focus_set()
        if hasattr(self, "readme_name"):
            self.text_box_readme_name.insert(0, self.readme_name)
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Select the output folder",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        output_folder_button = customtkinter.CTkButton(master=self.current_window, text="BROWSE",
                                                command=self.select_output_folder)
        output_folder_button.pack(pady=10)
        
        if hasattr(self, "output_folder"):
            text = self.output_folder
        else:
            text = ""
        self.output_folder_label = customtkinter.CTkLabel(master=self.current_window, text=text,
                                                          **self.text_args)
        self.output_folder_label.pack(pady=(20, 10))
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter the city name",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_city = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_city.pack(pady=10)
        self.text_box_city.focus_set()
        
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter the Year for the stack (i.e. 2022)\n If from multiple years: 2018x2022 ",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_year = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_year.pack(pady=10)
        self.text_box_year.focus_set()
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter a unique descriptor like a month or 'belaubt'/'unbelaubt'\n to differentiate the dataset from others in the same city and year.",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_desc = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_desc.pack(pady=10)
        self.text_box_desc.focus_set()
        
        
        
        
        enter_button = customtkinter.CTkButton(master=self.current_window, text="NEXT", command=self.get_stack_data_forward)
        enter_button.pack(pady=10)
        



    def create_window_ndsm(self, event=None):
        
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root)
        self.current_window.pack(fill="both", expand=True)
        

        question_label = customtkinter.CTkLabel(master=self.current_window, text="Is the nDSM already available? If not, you will be asked to input the DEM and DSM in the following steps?",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))

        yes_button = customtkinter.CTkButton(master=self.current_window, text="YES", command=self.create_window_ndsm_in)
        yes_button.pack(pady=10)

        no_button = customtkinter.CTkButton(master=self.current_window, text="NO", command=self.create_window_dtm_in)
        no_button.pack(pady=10)

    def create_window_json_in(self):
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root)
        self.current_window.pack(fill="both", expand=True)
        
        header = customtkinter.CTkLabel(master=self.current_window, text="INPUT", **self.header_args)
        header.pack(pady=(20, 10))

        prompt_label = customtkinter.CTkLabel(master=self.current_window, text="Select InputFilePointer (JSON) file:")
        prompt_label.pack(pady=(20, 10))

        mosaic_button = customtkinter.CTkButton(master=self.current_window, text="BROWSE", command=self.select_json_file)
        mosaic_button.pack(pady=10)
        
        

    def create_window_ndsm_in(self):
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root)
        self.current_window.pack(fill="both", expand=True)
        
        header = customtkinter.CTkLabel(master=self.current_window, text="nDSM", **self.header_args)
        header.pack(pady=(20, 10))
        
        prompt_text = "Please provide the normalized Digital Surface Model (nDSM) / normalisiertes digitales"\
                    " Höhenemodell (nDHM) \n. You may provide a single nDSM mosaic OR a folder"\
                    " containing nDSM tiles.\n The folder may include all files"\
                    " \n or subfolders containing the files. "
        prompt_label = customtkinter.CTkLabel(master=self.current_window,
                                              text=prompt_text,
                                              **self.intro_args)
        prompt_label.pack(pady=(20, 10))

        separator = ttk.Separator(self.current_window, orient='horizontal')
        separator.pack(fill='x')
        
        tiles_button = customtkinter.CTkButton(master=self.current_window, text="Tiles",
                                               command=self.select_ndsm_tiles_folder)
        
        tiles_button.pack(pady=10)
        
        
        self.tiles_path_label = customtkinter.CTkLabel(master=self.current_window, text="",
                                                       **self.text_args)
        self.tiles_path_label.pack(pady=(20, 10))
        
        
        or_label = customtkinter.CTkLabel(master=self.current_window,
                                                         text="OR",font=("Gobold", 52, "bold"))
        or_label.pack(pady=(20, 10))
        
        
        
        mosaic_button = customtkinter.CTkButton(master=self.current_window, text="Mosaic",
                                                command=self.select_ndsm_mosaic)
        mosaic_button.pack(pady=10)
        
        self.mosaic_path_label = customtkinter.CTkLabel(master=self.current_window, text="",
                                                        **self.text_args)
        self.mosaic_path_label.pack(pady=(20, 10))
        
        separator = ttk.Separator(self.current_window, orient='horizontal')
        separator.pack(fill='x')
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter the Year for the nDSM (i.e. 2022)\n If from multiple years: 2018x2022 ",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_year = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_year.pack(pady=10)
        self.text_box_year.focus_set()
        
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter a unique descriptor like a month or 'belaubt'/'unbelaubt'\n to differentiate the dataset from others in the same city and year."
                                                "otherwise a descriptor like 'belaubt'/'unbelaubt'",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_desc = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_desc.pack(pady=10)
        self.text_box_desc.focus_set()
        
        
        enter_button = customtkinter.CTkButton(master=self.current_window, text="NEXT", command=self.get_ndsm_data_forward)
        enter_button.pack(pady=10)

    def create_window_dtm_in(self):
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root)
        self.current_window.pack(fill="both", expand=True)
        
        header = customtkinter.CTkLabel(master=self.current_window, text="DTM", **self.header_args)
        header.pack(pady=(20, 10))
        
        prompt_text = "Please provide the Digital Terrain Model (DTM) / digitales \n"\
                    " Geländemodell (DGM).  \n You may provide a single DTM mosaic OR a"\
                    " folder containing DTM tiles. \n The folder may include all"\
                    " files \n or subfolders containing the files."
            
        prompt_label = customtkinter.CTkLabel(master=self.current_window,
                                              text=prompt_text,
                                              **self.intro_args)
        prompt_label.pack(pady=(20, 10))
        
        separator = ttk.Separator(self.current_window, orient='horizontal')
        separator.pack(fill='x')

        tiles_button = customtkinter.CTkButton(master=self.current_window, text="Tiles",
                                               command=self.select_dtm_tiles_folder)
        tiles_button.pack(pady=10)

        self.tiles_path_label = customtkinter.CTkLabel(master=self.current_window, text="",
                                                       **self.text_args)
        self.tiles_path_label.pack(pady=(20, 10))
        
        or_label = customtkinter.CTkLabel(master=self.current_window,
                                                         text="OR",font=("Gobold", 52, "bold"))
        or_label.pack(pady=(20, 10))

        mosaic_button = customtkinter.CTkButton(master=self.current_window, text="Mosaic",
                                                command=self.select_dtm_mosaic)
        mosaic_button.pack(pady=10)
        
        self.mosaic_path_label = customtkinter.CTkLabel(master=self.current_window, text="",
                                                        **self.text_args)
        self.mosaic_path_label.pack(pady=(20, 10))
        
        separator = ttk.Separator(self.current_window, orient='horizontal')
        separator.pack(fill='x')
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter the Year for the DTM (i.e. 2022)\n If from multiple years: 2018x2022 ",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_year = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_year.pack(pady=10)
        self.text_box_year.focus_set()
        
        
        
        
        enter_button = customtkinter.CTkButton(master=self.current_window, text="NEXT", command=self.get_dtm_data_forward)
        enter_button.pack(pady=10)

    def create_window_dsm_in(self):
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root)
        self.current_window.pack(fill="both", expand=True)
        
        header = customtkinter.CTkLabel(master=self.current_window, text="DSM", **self.header_args)
        header.pack(pady=(20, 10))
        
        prompt_text = "Please provide the Digital Surface Model (DSM) / digitales"\
                    " Geländemodell (DHM).\n You may provide a single DSM mosaic OR a"\
                    " folder containing DSM tiles.\n The folder may include all"\
                    " files \n or subfolders containing the files."
        prompt_label = customtkinter.CTkLabel(master=self.current_window,
                                              text=prompt_text,
                                              **self.intro_args)
        prompt_label.pack(pady=(20, 10))
        
        separator = ttk.Separator(self.current_window, orient='horizontal')
        separator.pack(fill='x')

        tiles_button = customtkinter.CTkButton(master=self.current_window, text="Tiles",
                                               command=self.select_dsm_tiles_folder)
        tiles_button.pack(pady=10)

        self.tiles_path_label = customtkinter.CTkLabel(master=self.current_window, text="",
                                                       **self.text_args)
        self.tiles_path_label.pack(pady=(20, 10))
        
        or_label = customtkinter.CTkLabel(master=self.current_window,
                                                         text="OR",font=("Gobold", 52, "bold"))
        or_label.pack(pady=(20, 10))

        mosaic_button = customtkinter.CTkButton(master=self.current_window, text="Mosaic",
                                                command=self.select_dsm_mosaic)
        mosaic_button.pack(pady=10)
        
        self.mosaic_path_label = customtkinter.CTkLabel(master=self.current_window, text="",
                                                        **self.text_args)
        self.mosaic_path_label.pack(pady=(20, 10))
        
        separator = ttk.Separator(self.current_window, orient='horizontal')
        separator.pack(fill='x')
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter the Year for the DSM (i.e. 2022)\n"\
                                                "If from multiple years: 2018x2022\nThis year will also be used to name the created nDSM",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_year = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_year.pack(pady=10)
        self.text_box_year.focus_set()
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter a unique descriptor like a month or 'belaubt'/'unbelaubt'\n to differentiate the dataset from others in the same city and year.",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_desc = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_desc.pack(pady=10)
        self.text_box_desc.focus_set()
        
        
        enter_button = customtkinter.CTkButton(master=self.current_window, text="NEXT", command=self.get_dsm_data_forward)
        enter_button.pack(pady=10)

    def create_window_ortho_in(self):
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root)
        self.current_window.pack(fill="both", expand=True)
        
        header = customtkinter.CTkLabel(master=self.current_window, text="ORTHO", **self.header_args)
        header.pack(pady=(20, 10))
        
        prompt_text = "Please provide the Orthophoto (ORTHO).\n"\
                    " You may provide a single ORTHO mosaic OR a"\
                    " folder containing ORTHO tiles.\n The folder may include all"\
                    " files \n or subfolders containing the files."
        prompt_label = customtkinter.CTkLabel(master=self.current_window,
                                              text=prompt_text,
                                              **self.intro_args)
        prompt_label.pack(pady=(20, 10))

        prompt_label = customtkinter.CTkLabel(master=self.current_window, text="Input ortho file:",
                                                **self.text_args)
        prompt_label.pack(pady=(20, 10))
        
        separator = ttk.Separator(self.current_window, orient='horizontal')
        separator.pack(fill='x')

        tiles_button = customtkinter.CTkButton(master=self.current_window, text="Tiles",
                                               command=self.select_ortho_tiles_folder)
        tiles_button.pack(pady=10)

        self.tiles_path_label = customtkinter.CTkLabel(master=self.current_window, text="",
                                                       **self.text_args)
        self.tiles_path_label.pack(pady=(20, 10))
        
        or_label = customtkinter.CTkLabel(master=self.current_window,
                                                         text="OR",font=("Gobold", 52, "bold"))
        or_label.pack(pady=(20, 10))

        mosaic_button = customtkinter.CTkButton(master=self.current_window, text="Mosaic",
                                                command=self.select_ortho_mosaic)
        mosaic_button.pack(pady=10)
        
        self.mosaic_path_label = customtkinter.CTkLabel(master=self.current_window, text="",
                                                        **self.text_args)
        self.mosaic_path_label.pack(pady=(20, 10))
        
        separator = ttk.Separator(self.current_window, orient='horizontal')
        separator.pack(fill='x')
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter the Year for the ORTHO (i.e. 2022)\n If from multiple years: 2018x2022 ",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_year = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_year.pack(pady=10)
        self.text_box_year.focus_set()
        
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Enter a unique descriptor like a month or 'belaubt'/'unbelaubt'\n to differentiate the dataset from others in the same city and year.",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
        self.text_box_desc = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_desc.pack(pady=10)
        self.text_box_desc.focus_set()
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Select if the Ortho is a True"\
                                                " Orthophoto or Digital Orthophoto",
                                                **self.text_args)
        question_label.pack(pady=(20, 10))
        
    
        
        
        
        self.combobox_dop_top = customtkinter.CTkComboBox(self.current_window, values=["DOP", "tDOP"])
        self.combobox_dop_top.pack()
        
        
        enter_button = customtkinter.CTkButton(master=self.current_window, text="NEXT", command=self.get_ortho_data_forward)
        enter_button.pack(pady=10)

    def create_window_add_another_dataset(self):
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root)
        self.current_window.pack(fill="both", expand=True)

        question_label = customtkinter.CTkLabel(master=self.current_window, text="Add another dataset?",
                                                **self.header_args)
        question_label.pack(pady=(20, 10))

        yes_button = customtkinter.CTkButton(master=self.current_window, text="YES", command=self.create_window_cityname)
        yes_button.pack(pady=10)

        no_button = customtkinter.CTkButton(master=self.current_window, text="NO. SUBMIT",
                                            command=self.create_json_file)
        no_button.pack(pady=10)

    def create_wait_epsg_window(self):
        
        self.current_window = customtkinter.CTkFrame(master=self.root2)
        self.current_window.pack(fill="both", expand=True)
        question_label = customtkinter.CTkLabel(master=self.current_window, text="CRS are getting extracted from the files.\n This can take a couple of minutes",
                                                **self.header_args)
        question_label.pack(pady=(20, 10))
        self.current_window.update_idletasks()
        
        
        self.df_epsg_in = self.create_epsg_df(self.file_path_json)
        self.create_window_epsg_table()
        

    def create_window_epsg_table(self):
        
        self.destroy_current_window()

        self.current_window = customtkinter.CTkFrame(master=self.root2)
        self.current_window.pack(fill="both", expand=True)
        self.current_window.update_idletasks()
        self.table_data = []
        self.table_entries = []
        wait_label = customtkinter.CTkLabel(master=self.current_window, text="Check if EPSG codes are correct. Add if missing.",
                                            **self.intro_args)
        wait_label.grid(row=0, column =2,
                         columnspan=5)
        self.create_grid(self.df_epsg_in)


        # Add a button to store the table data as a Pandas DataFrame
        save_button = customtkinter.CTkButton(master=self.current_window, text="Save & Run", command=self.save_table)
        save_button.grid(row=self.num_rows + 7 ,
                         columnspan=self.num_columns + 2)  # Add 1 to row and column indexes to accommodate headers
        
        epsg_label = customtkinter.CTkLabel(master=self.current_window, text="Enter the epsg to set in all empty cells",
                                            **self.text_args)
        epsg_label.grid(row=self.num_rows + 4,
                         columnspan=self.num_columns + 2)
        self.text_box_epsg_all = customtkinter.CTkEntry(master=self.current_window)
        self.text_box_epsg_all.grid(row=self.num_rows + 5,
                         columnspan=self.num_columns + 2,  padx=5, pady=5)
        fill_epsg_button = customtkinter.CTkButton(master=self.current_window, text="Fill all empty cells", command=self.fill_cells_epsg)
        fill_epsg_button.grid(row=self.num_rows + 6,
                         columnspan=self.num_columns + 3,  padx=5, pady=15)
        
        # Bind the click event to the table cells
        for row in self.table_entries:
            for entry in row:
                entry.bind("<Button-1>", self.edit_cell)
                
                
                
    

    def create_epsg_df(self, file_path_json):
        self.column_names = ["DSM", "DTM", "nDSM", "ORTHO"]
        data = []
    
        with open(file_path_json, 'r') as f:
            input_json = json.load(f)
    
        for city in input_json.keys():
            for year in input_json[city].keys():
                for desc in input_json[city][year].keys():
                    row_data = [city, year, desc]
                    for column_name in self.column_names:
                        ds_folder_dir = input_json[city][year][desc][column_name]
                        
    
                        if ds_folder_dir["tiles"]:
                            epsg = get_epsg_folder(ds_folder_dir["tiles"])
                        elif ds_folder_dir["mosaic"]:
                            epsg = get_epsg_folder(ds_folder_dir["mosaic"])
                        else:
                            epsg = np.nan
                            args_font = {}
                            args_deact = {"state": "disabled", "font": ("", 12), "fg_color": "grey"}
    
    
                        if epsg is None:
                            epsg = ""
                        row_data.append(epsg)
                    data.append(row_data)
    
        df = pd.DataFrame(data, columns=["City", "Year", "Description"] + self.column_names)
        return df


    
    
    
    
    def create_grid(self, df):
        self.num_rows, self.num_columns = df.shape[0], df.shape[1]
    
        for j in range(3,self.num_columns):
            header_label = customtkinter.CTkLabel(self.current_window, text=df.columns[j])
            header_label.grid(row=2, column=j, padx=5, pady=5)
        self.row_indexes = []
        for i in range(self.num_rows):
            index_label = customtkinter.CTkLabel(self.current_window, text=f"{df.at[i, 'City']}, {df.at[i, 'Year']}, {df.at[i, 'Description']}")
            self.row_indexes.append((df.at[i, 'City'], df.at[i, 'Year'], df.at[i, 'Description']))
            index_label.grid(row=i+4, column=0, padx=5, pady=5)
            self.entries_row = []
            for j in range(3, self.num_columns):  # Exclude the "City", "Year", and "Description" columns
                epsg = str(df.iloc[i, j])
                entry_var = tk.StringVar(value=epsg)  # Skip the first 3 columns
                entry = customtkinter.CTkEntry(self.current_window, textvariable=entry_var)
                entry.insert(0, epsg)
                
                
                if epsg == "nan":
                    args_font = {}
                    args_deact = {"state":"disabled",
                                 "font":("", 12),
                                   "fg_color":"grey"}
                else:
                    args_font = {"font": ("", 12, "bold", "italic")}
                    args_deact = {}  
                self.entries_row.append(entry)    
                entry.configure(**args_deact, **args_font)
                
                entry.grid(row=i+4, column=j, padx=5, pady=5)
            self.table_entries.append(self.entries_row)
    
        
    

##################################################################################################
        
       
    def select_json_file(self):
        
        self.file_path_json = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")],
                                                         initialdir=os.path.join("..",
                                                                                 "data/Input/InputFilePointer"))
        if self.file_path_json:
            # change root (because of pack and grid manager two roots exist)
            
            self.root.withdraw()
            
            self.root2.deiconify()
            
            self.create_wait_epsg_window()
            #self.create_window_epsg_table()
            
            
        
    def select_output_folder(self):
        self.output_folder = filedialog.askdirectory()
        
        self.output_folder_label.configure(text=self.output_folder)
    
    
    
    def select_ndsm_mosaic(self):
        self.mosaic_path_ndsm = filedialog.askopenfilename(filetypes=[("GeoTIFF files", "*.tif")])
        self.tiles_folder_path_ndsm = None
        self.mosaic_path_label.configure(text=self.mosaic_path_ndsm)
        
        
    def select_ndsm_tiles_folder(self):
        self.tiles_folder_path_ndsm = filedialog.askdirectory()
        self.mosaic_path_ndsm = None
        self.tiles_path_label.configure(text=self.tiles_folder_path_ndsm)
        


    def select_dtm_mosaic(self):
        self.mosaic_path_dtm = filedialog.askopenfilename(filetypes=[("GeoTIFF files", "*.tif")])
        self.tiles_folder_path_dtm = None
        self.mosaic_path_label.configure(text=self.mosaic_path_dtm)
    
    def select_dtm_tiles_folder(self):
        self.tiles_folder_path_dtm = filedialog.askdirectory()
        self.mosaic_path_dtm = None
        self.tiles_path_label.configure(text=self.tiles_folder_path_dtm)

    def select_dsm_mosaic(self):
        self.mosaic_path_dsm = filedialog.askopenfilename(filetypes=[("GeoTIFF files", "*.tif")])
        self.tiles_folder_path_dsm = None
        self.mosaic_path_label.configure(text=self.mosaic_path_dsm)
    
    def select_dsm_tiles_folder(self):
        self.tiles_folder_path_dsm = filedialog.askdirectory()
        self.mosaic_path_dsm = None
        self.tiles_path_label.configure(text=self.tiles_folder_path_dsm)

    def select_ortho_mosaic(self):
        self.mosaic_path_ortho = filedialog.askopenfilename(filetypes=[("GeoTIFF files", "*.tif")])
        self.tiles_folder_path_ortho = None
        self.mosaic_path_label.configure(text=self.mosaic_path_ortho)
    
    def select_ortho_tiles_folder(self):
        self.tiles_folder_path_ortho = filedialog.askdirectory()
        self.mosaic_path_ortho = None
        self.tiles_path_label.configure(text=self.tiles_folder_path_ortho)
        
    def get_stack_data_forward(self):
        self.readme_name = self.text_box_readme_name.get()
        self.stack_year = self.text_box_year.get()
        self.stack_desc = self.text_box_desc.get()
        self.city_name = self.text_box_city.get()
        if all([self.stack_year, self.city_name, self.output_folder]):
            self.create_window_ndsm()
        
        else:
            self.create_popup("City, Year and Outputfolder are mandatory\n Enter this information")
            
    def get_ndsm_data_forward(self):
        year = self.text_box_year.get()
        desc = self.text_box_desc.get()
        
        if self.tiles_folder_path_ndsm or self.mosaic_path_ndsm:
            self.ndsm_year = year
            self.ndsm_desc = desc
            
            
            self.create_window_ortho_in()
        else:
            self.create_popup("Select either a folder or a mosaic")
            

    

            
    def get_dtm_data_forward(self):
        year = self.text_box_year.get()
        
        
        if self.tiles_folder_path_dtm or self.mosaic_path_dtm:
            self.dtm_year = year
            
            
            
            self.create_window_dsm_in()
        else:
            self.create_popup("Select either a folder or a mosaic")
            
    def get_dsm_data_forward(self):
        year = self.text_box_year.get()
        desc = self.text_box_desc.get()
        
        if self.tiles_folder_path_dsm or self.mosaic_path_dsm:
            self.dsm_year = year
            self.dsm_desc = desc
            
            
            self.create_window_ortho_in()
        else:
            self.create_popup("Select either a folder or a mosaic")
            
    def get_ortho_data_forward(self):
        year = self.text_box_year.get()
        desc = self.text_box_desc.get()
        dop_top = self.combobox_dop_top.get()
        if self.tiles_folder_path_ortho or self.mosaic_path_ortho:
            self.ortho_year = year
            self.ortho_desc = desc
            self.ortho_dop_top = dop_top
            
            self.create_dashboard_window()
        else:
            self.create_popup("Select either a folder or a mosaic")

    def add_to_dict(self):
        
        if any([bool(self.mosaic_path_dtm or self.tiles_folder_path_dtm) != bool(
                self.mosaic_path_dsm or self.tiles_folder_path_dsm),
                bool(self.mosaic_path_dtm or self.tiles_folder_path_dtm) == bool(
                        self.mosaic_path_ndsm or self.tiles_folder_path_ndsm),
                not bool(self.mosaic_path_ortho or self.tiles_folder_path_ortho)]):
            
            var1 = self.mosaic_path_dtm
            var2 = self.tiles_folder_path_dtm
            var3 = self.mosaic_path_dsm
            var4 = self.tiles_folder_path_dsm
            var5 = self.mosaic_path_ndsm
            var6 = self.tiles_folder_path_ndsm
            var7 = self.mosaic_path_ortho
            var8 = self.tiles_folder_path_ortho
            
            self.create_popup("Check that there a paths to Ortho and nDSM or DSM+DTM"\
                              f"{var1}/n{var2}/n{var3}/n{var4}/n{var5}/n{var6}/n{var7}/n{var8}")
        
        
            
            
        
        else:
            if self.city_name not in self.input_dict:
                self.input_dict[self.city_name] = {}
            if self.stack_year not in self.input_dict[self.city_name]:
                self.input_dict[self.city_name][self.stack_year] = {}
            self.input_dict[self.city_name][self.stack_year][self.stack_desc] = {
                                                "nDSM": {
                                                    "mosaic": self.mosaic_path_ndsm,
                                                    "tiles": self.tiles_folder_path_ndsm,
                                                    "year": self.ndsm_year,
                                                    "description": self.ndsm_desc,
                                                    "noData": None
                                                },
                                                "DTM": {
                                                    "mosaic": self.mosaic_path_dtm,
                                                    "tiles": self.tiles_folder_path_dtm,
                                                    "year": self.dtm_year,
                                                    "noData": None
                                                    
                                                },
                                                "DSM": {
                                                    "mosaic": self.mosaic_path_dsm,
                                                    "tiles": self.tiles_folder_path_dsm,
                                                    "year": self.dsm_year,
                                                    "description": self.dsm_desc,
                                                    "noData": None
                                                    
                                                },
                                                "ORTHO": {
                                                    "mosaic": self.mosaic_path_ortho,
                                                    "tiles": self.tiles_folder_path_ortho,
                                                    "year": self.ortho_year,
                                                    "description": self.ortho_desc,
                                                    "dop_tdop":self.ortho_dop_top,
                                                    "noData": None
                                                    
                                                    
                                                },
                                                "METADATA": {
                                                    "README_name": self.readme_name,
                                                    "output_dir": self.output_folder,
                                                }}
                                                
            
            self.create_window_add_another_dataset()
        
    def create_json_file(self):
        timestamp = datetime.datetime.now().strftime("%d_%m_%Y-%H_%M")
        os.makedirs("../data/Input/InputFilePointer", exist_ok=True)
        with open(f'../data/Input/InputFilePointer/Input_{timestamp}.json', 'w') as fp:
            json.dump(self.input_dict, fp)
        self.create_window_1()
        
        
    def destroy_current_window(self):
        if self.current_window:
            self.current_window.destroy()

    def run(self):
        self.root.mainloop()
        self.root2.mainloop()
   
    ## epsg funcitons
    
    def edit_cell(self, event):
        entry = event.widget
        entry.config( font=("", 12))
        entry.focus_set()

    def save_table(self):
        timestamp = datetime.datetime.now().strftime("%d_%m_%Y-%H_%M")
        self.crs_metadata_path = f"../data/Input/CRSMetadata/epsg_input_data_{timestamp}.csv"
        table_values = [[entry.get() if self.is_float(entry.get())
                         else -999.5 for entry in row] for row in self.table_entries]
        print(table_values)
        df = pd.DataFrame(table_values, columns=self.column_names, index=self.row_indexes)
        print(df)
        df.index = pd.MultiIndex.from_tuples(df.index, names=["city", "year", "desc"])
        df = df.astype("float")
        if df.applymap(lambda x:  (np.isclose(x%1, 0) or np.isnan(x))).all(axis=None):
            try:
                os.makedirs(os.path.dirname(self.crs_metadata_path), exist_ok=True)
                df.to_csv(self.crs_metadata_path, index=True, float_format='%.0f')
                # start main application
                self.root2.withdraw()
                
                pipeline_thread = threading.Thread(target=pipeline.main_application,
                                                   args=(self.file_path_json,
                                                         self.crs_metadata_path))
                pipeline_thread.start()
                #self.root.destroy()
            except:
                self.create_window_epsg_table()
        else:
            self.create_popup("No empty cells allowed.\n"\
                              "Fill all cells with integers.")
            
    def is_float(self,value):
        try:
            float(value)
            return True
        except ValueError:
            return False
        
        
        

        
    def fill_cells_epsg(self):
        font_set = ("", 12)
        epsg_fill = self.text_box_epsg_all.get()
        entry_list = ([item for row in self.table_entries for item in row if item.get() == "" ])
        [item.delete(0,"end") for item in entry_list]
        [item.insert(0,epsg_fill) for item in entry_list]
        
        [item.configure(font=font_set) for item in entry_list]

    def create_dashboard_window(self):
        self.destroy_current_window()
        
    
    
        self.current_window = customtkinter.CTkFrame(master=self.root)
        
        self.current_window.pack(fill="both", expand=True)
        
        
        
        header = customtkinter.CTkLabel(master=self.current_window, text=f"{self.city_name} {self.stack_year} {self.stack_desc}", **self.header_args)
        header.grid(row=0 ,columnspan=6)
        
        question_label = customtkinter.CTkLabel(master=self.current_window, text="Check if the paths are correct.",
                                                **self.text_args)
        question_label.grid(row=1, column=3)
    
        # Create grid layout
        font = customtkinter.CTkFont(family='Arial', size=14, weight="bold")  # Font for headers
        dataset_names = ["Ortho", "", "", "", "DTM", "DSM", "OR", "nDSM"]
    
        # Add column headers
        dataset_name_label = customtkinter.CTkLabel(master=self.current_window, text="Dataset Name", font=font)
        dataset_name_label.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
    
        mosaic_label = customtkinter.CTkLabel(master=self.current_window, text="Mosaic", font=font)
        mosaic_label.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")
        
        tiles_label = customtkinter.CTkLabel(master=self.current_window, text="OR", font=font)
        tiles_label.grid(row=2, column=3, padx=10, pady=5, sticky="nsew")
        
        tiles_label = customtkinter.CTkLabel(master=self.current_window, text="Tiles", font=font)
        tiles_label.grid(row=2, column=4, padx=10, pady=5, sticky="nsew")
    
        # Calculate the number of columns in the grid
        num_columns = 4
    
        for i, dataset_name in enumerate(dataset_names):
            row_index = i + 3  # Adjust row index to account for the headers
    
            # Dataset name (column 1)
            dataset_label = customtkinter.CTkLabel(master=self.current_window, text=dataset_name, font=font)
            dataset_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="nsew")
            if dataset_name not in ["OR", ""]:
                # Mosaic path (column 2)
                mosaic_value = getattr(self, f"mosaic_path_{dataset_name.lower()}")
                mosaic_path_label = customtkinter.CTkLabel(master=self.current_window, text=mosaic_value, wraplength=200)
                mosaic_path_label.grid(row=row_index, column=1, padx=10, pady=5, sticky="nsew")
        
                mosaic_modify_button = customtkinter.CTkButton(master=self.current_window, text="Modify",
                                                               command=lambda ds=dataset_name.lower(): self.modify_path(ds, "mosaic"))
                mosaic_modify_button.grid(row=row_index, column=2, padx=(0, 10), pady=5, sticky="nsew")
        
                # Tiles file path (column 3)
                tiles_value = getattr(self, f"tiles_folder_path_{dataset_name.lower()}")
                tiles_path_label = customtkinter.CTkLabel(master=self.current_window, text=tiles_value, wraplength=200)
                tiles_path_label.grid(row=row_index, column=4, padx=10, pady=5, sticky="nsew")
        
                tiles_modify_button = customtkinter.CTkButton(master=self.current_window, text="Modify",
                                                              command=lambda ds=dataset_name.lower(): self.modify_path(ds, "tiles_folder"))
                tiles_modify_button.grid(row=row_index, column=5, padx=(0, 10), pady=5, sticky="nsew")
        
            num_columns = max(num_columns, 5)  # Update the number of columns if needed
    

        commit_button = customtkinter.CTkButton(master=self.current_window, text="Commit",
                                            command=self.add_to_dict, font=font, height=2, width=20)
        commit_button.grid(row=len(dataset_names) + 5, columnspan=num_columns+1, pady=(20, 10),
                           padx=(60,60),sticky="nsew")
        
    

        
# =============================================================================
#         # Update the root window's grid weight to make the window responsive
#         self.root.grid_rowconfigure(0, weight=1)
#         self.root.grid_columnconfigure(0, weight=1)
# =============================================================================


        
    def modify_path(self, dataset_name, path_type):
        
        # ensure that input data are valid
        print(dataset_name, path_type)
        if "mosaic" in path_type:
            file_folder_path = filedialog.askopenfilename(filetypes=[("GeoTIFF files", "*.tif")])
            setattr(self, f"tiles_folder_path_{dataset_name}", None)
        else:
            file_folder_path = filedialog.askdirectory()
            setattr(self, f"mosaic_path_{dataset_name}", None)
        setattr(self, f"{path_type}_path_{dataset_name}", file_folder_path)
        if dataset_name == "ndsm":
            setattr(self, f"mosaic_path_dtm", None)
            setattr(self, f"tiles_folder_path_dtm", None)
            setattr(self, f"mosaic_path_dsm", None)
            setattr(self, f"tiles_folder_path_dsm", None)
        elif dataset_name in ["dsm", "dtm"]:
            setattr(self, f"mosaic_path_ndsm", None)
            setattr(self, f"tiles_folder_path_ndsm", None)
            
        
            
        self.create_dashboard_window()



## pop up
    def create_popup(self, error_message):
        tk.messagebox.showwarning(title="Warning", message=error_message)





    
def main():
    gui = GUI()
    gui.run()


if __name__ == "__main__":
    main()




