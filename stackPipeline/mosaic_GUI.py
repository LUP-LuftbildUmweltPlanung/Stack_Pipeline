import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import pandas as pd
import datetime
import subprocess
import platform
import threading

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

class RasterInfoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Raster Info Collector")
        self.data = {}
        self.path_mode = {}  # Dictionary to store whether the path is for tiles or mosaic

        # Create all input fields and options in a single page
        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        tk.Label(frame, text="Dataset Name:").grid(row=0, column=0, sticky=tk.W)
        self.city_entry = tk.Entry(frame)
        self.city_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame, text="Year:").grid(row=1, column=0, sticky=tk.W)
        self.year_entry = tk.Entry(frame)
        self.year_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame, text="Description ('belaubt' or 'unbelaubt'):").grid(row=2, column=0, sticky=tk.W)
        self.desc_entry = tk.Entry(frame)
        self.desc_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(frame, text="README Name:").grid(row=3, column=0, sticky=tk.W)
        self.readme_entry = tk.Entry(frame)
        self.readme_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(frame, text="Output Directory:").grid(row=4, column=0, sticky=tk.W)
        self.output_entry = tk.Entry(frame)
        self.output_entry.grid(row=4, column=1, padx=5, pady=5)
        tk.Button(frame, text="Browse", command=self.browse_output_directory).grid(row=4, column=2, padx=5, pady=5)

        tk.Label(frame,
                 text="Use checkboxes to select which kind of dataset you want to mosaic and provide the folder to the tiles (in .tif or .jp2 or .laz or .xyz format). In case nDSM creation is checked, DSM and/or DTM Path needs to be specified, pointing to either mosaic location or tile folder.",
                 wraplength=500, justify="left").grid(row=5, column=0, columnspan=3, pady=5)

        self.raster_info_frames = []
        raster_types = ["DSM", "DTM", "ORTHO"]
        for i, raster_type in enumerate(raster_types):
            raster_frame = tk.LabelFrame(frame, text=raster_type)
            raster_frame.grid(row=6 + i, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
            self.create_raster_info_widgets(raster_frame, raster_type)
            self.raster_info_frames.append(raster_frame)

        tk.Label(frame,
                 text="For nDSM creation, data specified for DSM and DTM will be used. Resolution and other specifications will be taken from DSM for nDSM creation.",
                 wraplength=500, justify="left").grid(row=9, column=0, columnspan=3, pady=5)

        # Adding nDSM specific frame
        ndsm_frame = tk.LabelFrame(frame, text="nDSM")
        ndsm_frame.grid(row=10, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        self.create_ndsm_info_widgets(ndsm_frame)

        tk.Button(frame, text="Generate Input Files and Run Pipeline", command=self.generate_files_and_run_pipeline).grid(row=11, column=0, columnspan=3, pady=10)

    def create_raster_info_widgets(self, parent, raster_type):
        var = tk.BooleanVar()
        tk.Checkbutton(parent, variable=var).grid(row=0, column=0)
        setattr(self, f"{raster_type.lower()}_var", var)

        tk.Label(parent, text=f"Select either {raster_type} tiles folder or mosaic file:").grid(row=0, column=1,
                                                                                                columnspan=3,
                                                                                                sticky=tk.W)

        tk.Label(parent, text=f"{raster_type} Path:").grid(row=1, column=1, sticky=tk.W)
        path_entry = tk.Entry(parent)
        path_entry.grid(row=1, column=2, padx=5, pady=5)
        tk.Button(parent, text="Browse Tiles", command=lambda e=path_entry, t=f"Select {raster_type} tile folder path",
                                                              m="tiles": self.browse_directory(e, t, m)).grid(row=1,
                                                                                                              column=3,
                                                                                                              padx=5,
                                                                                                              pady=5)
        if raster_type in ["DSM", "DTM"]:
            tk.Button(parent, text="Browse Mosaic",
                      command=lambda e=path_entry, t=f"Select {raster_type} mosaic file", m="mosaic": self.browse_file(
                          e, t, m)).grid(row=1, column=4, padx=5, pady=5)
        setattr(self, f"{raster_type.lower()}_path_entry", path_entry)

        tk.Label(parent, text=f"{raster_type} Year:").grid(row=2, column=1, sticky=tk.W)
        year_entry = tk.Entry(parent)
        year_entry.grid(row=2, column=2, padx=5, pady=5)
        setattr(self, f"{raster_type.lower()}_year_entry", year_entry)

        tk.Label(parent, text=f"{raster_type} Description (belaubt/unbelaubt):").grid(row=3, column=1, sticky=tk.W)
        description_entry = tk.Entry(parent)
        description_entry.grid(row=3, column=2, padx=5, pady=5)
        setattr(self, f"{raster_type.lower()}_description_entry", description_entry)

        if raster_type == "ORTHO":
            tk.Label(parent, text="ORTHO Type (tdop/dop):").grid(row=4, column=1, sticky=tk.W)
            ortho_type_entry = tk.Entry(parent)
            ortho_type_entry.grid(row=4, column=2, padx=5, pady=5)
            setattr(self, "ortho_dop_tdop_entry", ortho_type_entry)

    def create_ndsm_info_widgets(self, parent):
        self.ndsm_var = tk.BooleanVar()
        tk.Checkbutton(parent, variable=self.ndsm_var).grid(row=0, column=0)

        tk.Label(parent, text="nDSM Year:").grid(row=0, column=1, sticky=tk.W)
        self.ndsm_year_entry = tk.Entry(parent)
        self.ndsm_year_entry.grid(row=0, column=2, padx=5, pady=5)

        tk.Label(parent, text="nDSM Description (belaubt/unbelaubt):").grid(row=1, column=1, sticky=tk.W)
        self.ndsm_description_entry = tk.Entry(parent)
        self.ndsm_description_entry.grid(row=1, column=2, padx=5, pady=5)

    def browse_directory(self, entry, title, mode):
        directory = filedialog.askdirectory(title=title)
        entry.delete(0, tk.END)
        entry.insert(0, directory)
        self.path_mode[entry] = mode

    def browse_file(self, entry, title, mode):
        file_path = filedialog.askopenfilename(title=title, filetypes=[("Mosaic Files", "*.tif;*.jp2;*.laz;*.xyz")])
        entry.delete(0, tk.END)
        entry.insert(0, file_path)
        self.path_mode[entry] = mode

    def browse_output_directory(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, directory)

    def add_dataset(self):
        city = self.city_entry.get()
        year = self.year_entry.get()
        desc = self.desc_entry.get()

        if not city or not year or not desc:
            messagebox.showerror("Error", "Dataset Name, Year, and Description fields cannot be empty")
            return

        if city not in self.data:
            self.data[city] = {}

        if year not in self.data[city]:
            self.data[city][year] = {}

        if desc in self.data[city][year]:
            messagebox.showerror("Error", "No duplicates of keys city and year is allowed for new dataset")
            return

        self.data[city][year][desc] = {}

        readme_name = self.readme_entry.get()
        output_dir = self.output_entry.get()

        self.data[city][year][desc]["METADATA"] = {
            "README_name": readme_name,
            "output_dir": os.path.normpath(output_dir)
        }

        raster_types = {
            "DSM": self.dsm_var.get(),
            "DTM": self.dtm_var.get(),
            "ORTHO": self.ortho_var.get()
        }

        for raster_type, create in raster_types.items():
            if create:
                path_entry = getattr(self, f"{raster_type.lower()}_path_entry")
                year_entry = getattr(self, f"{raster_type.lower()}_year_entry")
                description_entry = getattr(self, f"{raster_type.lower()}_description_entry")

                path = path_entry.get().strip()
                path_mode = self.path_mode.get(path_entry, None)

                if path_mode == "tiles":
                    tiles_path = path
                    mosaic_path = None
                elif path_mode == "mosaic":
                    tiles_path = None
                    mosaic_path = path
                else:
                    messagebox.showerror("Error",
                                         f"Please provide either a tiles folder or a mosaic file for {raster_type}.")
                    return

                self.data[city][year][desc][raster_type] = {
                    "process": True,
                    "tiles": tiles_path,
                    "mosaic": mosaic_path,
                    "year": year_entry.get(),
                    "description": description_entry.get(),
                    "noData": None
                }

                if raster_type == "ORTHO":
                    ortho_dop_tdop_entry = getattr(self, "ortho_dop_tdop_entry")
                    self.data[city][year][desc][raster_type]["dop_tdop"] = ortho_dop_tdop_entry.get()
            else:
                self.data[city][year][desc][raster_type] = {
                    "process": False,
                    "tiles": None,
                    "mosaic": None,
                    "year": None,
                    "description": None,
                    "noData": None
                }

        if self.ndsm_var.get():
            ndsm_year = self.ndsm_year_entry.get()
            ndsm_description = self.ndsm_description_entry.get()

            self.data[city][year][desc]["nDSM"] = {
                "process": True,
                "mosaic": None,
                "tiles": None,
                "year": ndsm_year,
                "description": ndsm_description,
                "noData": None
            }
        else:
            self.data[city][year][desc]["nDSM"] = {
                "process": False,
                "mosaic": None,
                "tiles": None,
                "year": None,
                "description": None,
                "noData": None
            }


    def generate_files_and_run_pipeline(self):
        self.add_dataset()

        timestamp = datetime.datetime.now().strftime("%d_%m_%Y-%H_%M")
        json_filename = os.path.join(root_dir, "data", "Input", "InputFilePointer", f"Input_{timestamp}.json")
        save_json_to_file(json_filename, self.data)

        column_names = ["city", "year", "desc", "DSM", "DTM", "nDSM", "ORTHO"]
        df_epsg = pd.DataFrame(columns=column_names)
        df_epsg.set_index(["city", "year", "desc"], inplace=True)

        for city in self.data.keys():
            for year in self.data[city].keys():
                for desc in self.data[city][year].keys():
                    ds_epsg = []
                    for column_name in ["DSM", "DTM", "nDSM", "ORTHO"]:
                        ds_folder_dir = self.data[city][year][desc][column_name]
                        if ds_folder_dir["tiles"]:
                            epsg = get_epsg_folder(ds_folder_dir["tiles"])
                        elif ds_folder_dir["mosaic"]:
                            epsg = get_epsg_folder(ds_folder_dir["mosaic"])
                        else:
                            epsg = None
                        ds_epsg.append(epsg)
                    df_epsg.loc[(city, year, desc), :] = ds_epsg

        epsg_filename = os.path.join(root_dir, "data", "Input", "CRSMetadata", f"epsg_input_data_{timestamp}.csv")
        os.makedirs(os.path.dirname(epsg_filename), exist_ok=True)
        df_epsg.to_csv(epsg_filename, index=True, float_format='%.0f')

        # Open the CSV file with the default application
        try:
            if platform.system() == 'Windows':
                subprocess.call(['start', epsg_filename], shell=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', epsg_filename])
            else:  # Linux
                subprocess.call(['xdg-open', epsg_filename])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open the file: {e}")

        # Wait for user confirmation before running the pipeline
        self.root.after(1000, self.check_for_user_confirmation, json_filename, epsg_filename)


    def check_for_user_confirmation(self, json_filename, epsg_filename):
        if messagebox.askyesno("Confirmation", f"Input files generated successfully. EPSG file has been opened and may be edited to include missing EPSG Codes. Upon complection, save the csv and confirm this dialogue to start the processing pipeline. Have you finished editing the and are ready to start the pipeline?"):
            self.run_pipeline(json_filename, epsg_filename)
        else:
            self.root.after(5000, self.check_for_user_confirmation, json_filename, epsg_filename)

    def run_pipeline(self, json_filename, epsg_filename):
        try:
            # Close the main application window
            self.root.destroy()
            # Run the main pipeline function
            mosaic_pipeline.main_application(json_filename, epsg_filename)
        except Exception as e:
            # Show an error message if the pipeline execution fails
            messagebox.showerror("Error", f"Pipeline execution failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RasterInfoApp(root)
    root.mainloop()
