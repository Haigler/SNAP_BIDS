#!/bin/sh
#
# move_events.sh
#
# Moves task event files (.tsv) into the BIDS directory hierarchy.
# Each file is copied into both the rawdata and derivatives trees,
# then ownership is set to dummy-user.
#
# USAGE:
#     bash move_events.sh <task_name>
#
# EXAMPLE:
#     bash move_events.sh cyberball
#
# AVAILABLE TASKS:
#     cyberball
#     (add new task names here as they become available)
#
# The script expects:
#   - Source files in:
#       ../../../../../../Data/Task Behavioral Data for BIDS/Converted Files/SNAP {1,2,3}/<Task>/
#   - A manifest file listing expected filenames (one per line) at:
#       ./manifests/<task_name>.txt
#   - Root of the BIDS hierarchy in:
#     ../../../../../../Data/BIDS/SNAP
#
# Each manifest line should contain just the filename, e.g.:
#       sub-01003_task-cyberball_run-01_events.tsv
#
# -------------------------------------------------------------------