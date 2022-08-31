# Team Post TASK
# This script converts the original Team Post-Task (i.e. Memory Task) files that were exported from ePrime to the BIDS compliant tsv format.
# Only data deemed relevant for analysis have been retained, however this has been construed broadly.

from os import listdir
from os.path import isfile, join
import numpy as np
import pandas

# turning off a warning that occurs with some chained commands.
pandas.options.mode.chained_assignment = None

# path to data
# note that this task has data split across several folders
basefolder = "/mnt/magaj/SNAP/Data/Task Behavioral Data for BIDS/"
snap1datadir1 = basefolder + "SNAP 1/Team Game/Post Scan Memory/Edat/"
snap1datadir2 = basefolder + "SNAP 1/Team Game/Post Scan Memory/New Edat/"

# output folder
snap1outdir = basefolder + "Converted Files/SNAP 1/Team/Post Scan Memory/"
