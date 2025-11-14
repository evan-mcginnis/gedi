import argparse
import sys
import logging
import logging.config
import os
from os import path
import threading
import time
import glob
from typing import List

from geotiff import GeoTiff
import numpy as np
import matplotlib.pyplot as plt

from networkx.algorithms import components

DATAFILE_PATTERN = "*.tif"
UNITS_BIOMASS = "Mg ha-1"
UNITS_PERCENT = "%"
FILENAME_DELIMITER = "_"
FILENAME_COMPONENTS = 7
POSITION_MISSION_TIMEFRAME = 2
POSITION_SPATIAL = 6
POSITION_TYPE = 7

# Extent of the dataset
LAT_WESTERNMOST = -180
LAT_EASTERNMOST = 180
LONG_NORTHERMOST = 52
LONG_SOUTHERMOST = -52

# File names are broken down thusly
# GEDI04_B_<start_mission_wk_end_mission_wk>_<ppds>_<release_num>_<product_ver>_<spatial_resolution>_<variable>.tif
# Each component may have a different NaN value
COMPONENT_NAN = "nan"
COMPONENT_READABLE = "readable"
TYPE_MU = "MU"

dataFiles = {
    "MU": {COMPONENT_READABLE: "Mean", COMPONENT_NAN: -9999},
    "V1": {COMPONENT_READABLE: "Variance component 1", COMPONENT_NAN: -9999},
    "V2": {COMPONENT_READABLE: "Variance component 2", COMPONENT_NAN: -9999},
    "SE": {COMPONENT_READABLE: "Standard Error", COMPONENT_NAN: -9999},
    "PE": {COMPONENT_READABLE: "Percentage Std Error", COMPONENT_NAN: 255},
    "NC": {COMPONENT_READABLE: "Number of Clusters", COMPONENT_NAN: 0},
    "NS": {COMPONENT_READABLE: "Number of Samples", COMPONENT_NAN: 0},
    "QF": {COMPONENT_READABLE: "Quality", COMPONENT_NAN: 0},
    "PS": {COMPONENT_READABLE: "Predicted Stratum", COMPONENT_NAN: 0},
    "MI": {COMPONENT_READABLE: "Mode of Interference", COMPONENT_NAN: 0}
}

# Used in command line processing so we can accept thresholds that are tuples
def tuple_type(strings):
    strings = strings.replace("(", "").replace(")", "")
    mappedFloat = map(float, strings.split(","))
    return tuple(mappedFloat)

parser = argparse.ArgumentParser("Biomass Processing")

parser.add_argument("-f", "--file", action="store", required=True, help="Source file or directory")
parser.add_argument("-l", "--location", action="store", required=True, type=tuple_type, help="Location of upper left corner of ROI in decimal degrees (lat, long)")
parser.add_argument("-le", "--length", action="store", required=True, type=int, help="Length of ROI in whole km")
parser.add_argument("-lg", "--logging", action="store", default="logging.ini", help="Logging configuration file")
parser.add_argument("-s", "--summary", action="store_true", default=False, help="Summarize the files")
parser.add_argument("-t", "--target", action="store", required=False, choices=dataFiles.keys(), help="Target file")
parser.add_argument("-p", "--plot", action="store_true", required=False, default=False, help="Plot area")

arguments = parser.parse_args()

if not os.path.isfile(arguments.logging):
    print("Unable to access logging configuration file {}".format(arguments.logging))
    sys.exit(1)

logging.config.fileConfig(arguments.logging)

logger = logging.getLogger(__name__)
logger.info("Starting")

if os.path.isdir(arguments.file):
    filesToProcess = glob.glob(path.join(arguments.file, DATAFILE_PATTERN))
    if arguments.target is None:
        print("Target must be specified if directory is")
        sys.exit(-1)
elif os.path.isfile(arguments.file):
    filesToProcess = [arguments.file]
else:
    print("Unable to find file or directory {}".format(arguments.file))
    sys.exit(-1)

if len(filesToProcess) == 0:
    logger.error("No files found to process")
    sys.exit(1)

for file in filesToProcess:
    print(f"Processing {file}")
    # Filenames are in this format.  Drop the extension and split up for components
    # GEDI04_B_<start_mission_wk_end_mission_wk>_<ppds>_<release_num>_<product_ver>_<spatial_resolution>_<variable>.tif
    baseFilename = os.path.splitext(file)[0]
    comp = baseFilename.split(FILENAME_DELIMITER)
    assert len(comp) == FILENAME_COMPONENTS + 1


    tiff = GeoTiff(file)
    zArray = tiff.read()
    # The datapoints from the NASA fit in memory on my machine
    array = np.array(zArray)

    # Clean the array with the correct NaN
    nanValue = dataFiles[comp[POSITION_TYPE]][COMPONENT_NAN]
    print(f"Nan: {nanValue}")
    array = np.where(array == nanValue, np.nan, array)

    print(f"Shape: {tiff.tif_shape} 84: {tiff.tif_bBox_wgs_84} (10,100) {tiff.get_wgs_84_coords(10,100)}")
    #area_box = ((33.38667, -112.36222), (33.38056, -112.339722))

    # Bounding box of ROI
    # latUL = 33.38667
    # longUL = -112.36222
    # latLR = 33.12333
    # longLR = -111.943611

    # Bounding box for most of arizona
    # latUL = 36.733478
    # longUL = -113.92295
    # latLR = 31.403289
    # longLR = -109.149958

    # Bounding box of Gila River study area
    latUL = 33.34765
    longUL = -112.622607
    latLR = 33.327916
    longLR = -112.575544

    area_box = ((longUL, latUL), (longLR, latLR))
    subset = tiff.read_box(area_box)
    nanValue = dataFiles[comp[POSITION_TYPE]][COMPONENT_NAN]
    print(f"Nan: {nanValue}")
    subset = np.where(subset == nanValue, np.nan, subset)

    print(f"Read subset: {subset.shape}")
    print(f"Max: {np.nanmax(subset)} Min {np.nanmin(subset)} Mean: {np.nanmean(subset)} Std: {np.nanstd(subset)} shape: {subset.shape}")

    if comp[POSITION_TYPE] == TYPE_MU:
        if arguments.plot:
            plt.imshow(subset, interpolation="none", cmap="BuGn")
            plt.colorbar(label="Mean Above Ground Biomass (Mg per HA)", orientation="vertical")
            plt.show()
        else:
            print(f"---------\nTotal Mass Mg per HA: {np.sum(subset)}")
