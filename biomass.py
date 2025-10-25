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
from networkx.algorithms import components

DATAFILE_PATTERN = "*.tif"
UNITS_BIOMASS = "Mg ha-1"
UNITS_PERCENT = "%"
FILENAME_DELIMITER = "_"
FILENAME_COMPONENTS = 7
POSITION_MISSION_TIMEFRAME = 2
POSITION_SPATIAL = 6
POSITION_TYPE = 7

# File names are broken down thusly
# GEDI04_B_<start_mission_wk_end_mission_wk>_<ppds>_<release_num>_<product_ver>_<spatial_resolution>_<variable>.tif
# Each component may have a different NaN value
COMPONENT_NAN = "nan"
COMPONENT_READABLE = "readable"

dataFiles = {
    "MU": {COMPONENT_READABLE: "Mean" , COMPONENT_NAN: -9999},
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

def parseFileName(fileName: str) -> List[str]:
    comp = fileName.split(FILENAME_DELIMITER)
    return comp

parser = argparse.ArgumentParser("Biomass Processing")

parser.add_argument("-f", "--file", action="store", required=True, help="Source file or directory")
parser.add_argument("-lg", "--logging", action="store", default="logging.ini", help="Logging configuration file")
parser.add_argument("-s", "--summary", action="store_true", default=False, help="Summarize the files")

arguments = parser.parse_args()

if not os.path.isfile(arguments.logging):
    print("Unable to access logging configuration file {}".format(arguments.logging))
    sys.exit(1)

logging.config.fileConfig(arguments.logging)

logger = logging.getLogger(__name__)
logger.info("Starting")

if os.path.isdir(arguments.file):
    filesToProcess = glob.glob(path.join(arguments.file, DATAFILE_PATTERN))
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
    array = np.array(zArray)

    # Clean the array with the correct NaN
    nanValue = dataFiles[comp[POSITION_TYPE]][COMPONENT_NAN]
    array = np.where(array == nanValue, np.nan, array)
    print(f"Max: {np.nanmax(array)} Min {np.nanmin(array)} Mean: {np.nanmean(array)} Std: {np.nanstd(array)} shape: {array.shape}")


