#!/bin/bash
#
# move_eventfiles.sh - copy converted task event files into the BIDS hierarchy.
#
# Copies task event files (.tsv) into the BIDS directory hierarchy from a staging area.
# Each file is placed into BOTH the rawdata and derivatives trees:
#   - derivatives: copied verbatim; the converted files already use the unpadded
#                  run label fMRIPrep produces (run-1, run-2)
#   - rawdata:     the run label is zero-padded (run-1 -> run-01) to match the
#                  bold filenames in rawdata
# Both copies are required: the BIDS Inheritance Principle does not cross dataset
# boundaries. The staging copy is left in place; nothing is deleted or moved.
#
# BEFORE each copy, ownership and permissions are set on the STAGING file, and
# 'cp -p' carries them through to both destinations:
#   - owner/group -> $OWNER:$GROUP  (set in SETTINGS)
#   - owner perms -> left as-is  (not modified)
#   - group       -> read/write only   (execute removed)
#   - world       -> no access   (read, write, execute all removed)
# This ordering is deliberate. If the script is run without sudo, the chown fails
# before anything has been written into the BIDS tree, rather than scattering
# wrongly-owned files across it. Nothing is ever placed in the BIDS tree without
# its final permissions already set.
#
# The staging file's original owner, group, and mode are saved beforehand and
# restored once both copies are made, so staging is left exactly as it was found.
# Be aware that if the script is aborted mid-run this restoring might not happen.
#
# Must be run under sudo (chown/chmod require it). A dry run does not.
#
# Usage:   sudo bash move_eventfiles.sh [--dry-run] <task_name>
# Example: sudo bash move_eventfiles.sh --dry-run cyberball
#
# Run this from the directory that contains this script and manifests/.
#
# The task name is validated against ALLOWED_TASKS in the SETTINGS block, which
# is the single place to edit when a new task is converted.
#
# The script expects:
#   - Source files in the directories listed in STAGING_<cohort> (SETTINGS block),
#     one entry per cohort, e.g.
#       .../Converted Files/SNAP 1/Cyberball/
#     The task folder is the task_name with its first letter capitalized.
#   - A manifest listing expected filenames (one per line) at:
#       ./manifests/<task_name>.txt
#   - Destination subject directories under the paths listed in RAWDATA_<cohort> and
#     DERIVATIVES_<cohort> (SETTINGS block). These must already exist; a file whose
#     target func/ directory is missing is reported and skipped.
#
# The manifest is a WHITELIST of the files to place. Omitting a file is how you
# deliberately leave a problematic event file behind:
#   - a file listed in the manifest and found in staging is placed;
#   - a file found in staging but NOT listed is reported and left untouched;
#   - a file listed in the manifest but not placed is reported as NOT PLACED, whether
#     it was never found in staging or was found but could not be copied.
# The script exits non-zero if any listed file was NOT PLACED, if a target func/
# directory was missing, or if a staging directory was missing. Files left behind on purpose
# do not affect the exit code. A failed chown or cp aborts the script on the spot.

set -e -u -o pipefail


# ---------------------------------------------------------------------------
# SETTINGS - everything you would need to change lives in this block.
# ---------------------------------------------------------------------------

# Tasks this script will accept. Adding a task is a one-word edit here,
# provided its staging folder is named after it (see STAGING_ below).
ALLOWED_TASKS=('cyberball')

# Owner and group applied to every file before it is copied.
OWNER='dummy-user'
GROUP='fslab-snap'

# The task argument, capitalized, is the name of the staging subfolder
# ('cyberball' -> 'Cyberball'). Set after the argument is read, below.
TASK=''
TASK_FOLDER=''

# Staging directories, one per cohort. Note the space in 'SNAP 1' etc.
STAGING_SNAP1='../../../../../../Data/Task Behavioral Data for BIDS/Converted Files/SNAP 1'
STAGING_SNAP2='../../../../../../Data/Task Behavioral Data for BIDS/Converted Files/SNAP 2'
STAGING_SNAP3='../../../../../../Data/Task Behavioral Data for BIDS/Converted Files/SNAP 3'

# Destination roots. Subject directories already exist under each of these.
RAWDATA_SNAP1='../../../../../../Data/BIDS/SNAP/rawdata/SNAP1'
RAWDATA_SNAP2='../../../../../../Data/BIDS/SNAP/rawdata/SNAP2'
RAWDATA_SNAP3='../../../../../../Data/BIDS/SNAP/rawdata/SNAP3'

DERIVATIVES_SNAP1='../../../../../../Data/BIDS/SNAP/derivatives/fmriprep-SNAP1'
DERIVATIVES_SNAP2='../../../../../../Data/BIDS/SNAP/derivatives/fmriprep-SNAP2'
DERIVATIVES_SNAP3='../../../../../../Data/BIDS/SNAP/derivatives/fmriprep-SNAP3'


# ---------------------------------------------------------------------------
# ARGUMENTS
# ---------------------------------------------------------------------------

DRY_RUN=false

if [ "${1:-}" = '--dry-run' ]; then
    DRY_RUN=true
    shift
fi

if [ $# -ne 1 ]; then
    echo 'Usage: sudo bash move_eventfiles.sh [--dry-run] <task_name>'
    exit 1
fi

# Lowercase the task name so 'Cyberball' and 'cyberball' both work.
TASK="${1,,}"

TASK_IS_ALLOWED=false

for allowed in "${ALLOWED_TASKS[@]}"; do
    if [ "$TASK" = "$allowed" ]; then
        TASK_IS_ALLOWED=true
    fi
done

if ! $TASK_IS_ALLOWED; then
    echo "Unknown task: '$1'"
    echo "Allowed tasks: ${ALLOWED_TASKS[*]}"
    exit 1
fi

# 'cyberball' -> 'Cyberball', the capitalized staging subfolder name.
TASK_FOLDER="${TASK^}"

MANIFEST="./manifests/${TASK}.txt"

if [ ! -f "$MANIFEST" ]; then
    echo "Manifest not found: $MANIFEST"
    exit 1
fi


# ---------------------------------------------------------------------------
# MANIFEST - a whitelist. Only files listed here are copied. A file left out
# of the manifest is a file deliberately left behind.
# ---------------------------------------------------------------------------

LISTED_FILES=()

while IFS=$' \t\n' read -r line || [ -n "$line" ]; do
    # Skip blank lines and '#' comments.
    if [ -z "$line" ] || [ "${line:0:1}" = '#' ]; then
        continue
    fi
    LISTED_FILES+=("$line")
done < "$MANIFEST"

# Filenames actually placed. Anything listed in the manifest but never added here
# is reported as not placed at the end.
declare -A PLACED=()

# Counts for the closing report.
COUNT_COPIED=0
COUNT_LEFT_BEHIND=0
COUNT_ERRORS=0


is_listed_in_manifest() {
    local filename="$1"
    local listed
    for listed in "${LISTED_FILES[@]}"; do
        if [ "$listed" = "$filename" ]; then
            return 0
        fi
    done
    return 1
}



# ---------------------------------------------------------------------------
# COPY EVENT FILES TO BIDS HIERARCHY
#
# Uses the subject ID from the event filename to determine that file's
# destination func/ in both trees:
#
# E.g,
#   sub-01003_task-cyberball_run-01_events.tsv  ->  sub-01003  ->  sub-01003/func/
# ---------------------------------------------------------------------------

process_cohort() {
    local staging_root="$1"
    local rawdata_root="$2"
    local derivatives_root="$3"

    local staging_dir="${staging_root}/${TASK_FOLDER}"

    echo ''
    echo "=== $staging_dir"

    if [ ! -d "$staging_dir" ]; then
        echo "  ERROR: staging directory not found"
        COUNT_ERRORS=$((COUNT_ERRORS + 1))
        return
    fi

    local source_file filename subject rawdata_func derivatives_func rawdata_name
    local original_ownership original_mode

    for source_file in "$staging_dir"/*.tsv; do

        # If the folder holds no .tsv files, the '*.tsv' pattern does not
        # expand and is passed through as a literal. Nothing to do here.
        if [ ! -e "$source_file" ]; then
            echo '  (no .tsv files in this folder)'
            break
        fi

        filename=$(basename "$source_file")

        if ! is_listed_in_manifest "$filename"; then
            echo "  LEFT BEHIND (not in manifest): $filename"
            COUNT_LEFT_BEHIND=$((COUNT_LEFT_BEHIND + 1))
            continue
        fi

        # REQUIRES sub-<val> to be the first entity in the filename.
        # EXPECTS converted TSV files to not use leading zeros in the run value.
        subject="${filename%%_*}"                    # sub-01003_task-... -> sub-01003
        rawdata_name="${filename/_run-/_run-0}"      # run-1 -> run-01

        rawdata_func="${rawdata_root}/${subject}/func"
        derivatives_func="${derivatives_root}/${subject}/func"

        # The subject directories already exist. If one is missing, that is a
        # real problem with the data, not something to paper over by creating
        # a directory, so report it and move on.
        if [ ! -d "$rawdata_func" ]; then
            echo "  ERROR: no such directory, skipping: $rawdata_func"
            COUNT_ERRORS=$((COUNT_ERRORS + 1))
            continue
        fi

        if [ ! -d "$derivatives_func" ]; then
            echo "  ERROR: no such directory, skipping: $derivatives_func"
            COUNT_ERRORS=$((COUNT_ERRORS + 1))
            continue
        fi

        if $DRY_RUN; then
            echo "  WOULD COPY: $filename"
            echo "      -> ${rawdata_func}/${rawdata_name}"
            echo "      -> ${derivatives_func}/${filename}"
            PLACED["$filename"]=1
            COUNT_COPIED=$((COUNT_COPIED + 1))
            continue
        fi

        # Ownership and permissions are set on the STAGING file first, and the
        # copies inherit them via 'cp -p'. This ordering is deliberate: if this
        # script is run without sudo, the chown fails here, before anything has
        # been written into the BIDS tree.
        #
        # The staging file's original owner, group, and mode are saved first and
        # put back once both copies are made, so staging is left as it was found.
        original_ownership=$(stat -c '%U:%G' "$source_file")
        original_mode=$(stat -c '%a' "$source_file")

        chown "${OWNER}:${GROUP}" "$source_file"
        chmod g+rw,o-rwx "$source_file"

        cp -p "$source_file" "${rawdata_func}/${rawdata_name}"
        cp -p "$source_file" "${derivatives_func}/${filename}"

        chown "$original_ownership" "$source_file"
        chmod "$original_mode" "$source_file"

        echo "  COPIED: $filename"
        echo "      -> ${rawdata_func}/${rawdata_name}"
        echo "      -> ${derivatives_func}/${filename}"
        PLACED["$filename"]=1
        COUNT_COPIED=$((COUNT_COPIED + 1))
    done
}


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

if $DRY_RUN; then
    echo "DRY RUN - nothing will be changed. Task: $TASK"
else
    echo "Task: $TASK"
fi

process_cohort "$STAGING_SNAP1" "$RAWDATA_SNAP1" "$DERIVATIVES_SNAP1"
process_cohort "$STAGING_SNAP2" "$RAWDATA_SNAP2" "$DERIVATIVES_SNAP2"
process_cohort "$STAGING_SNAP3" "$RAWDATA_SNAP3" "$DERIVATIVES_SNAP3"


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

echo ''
echo '=== Manifest entries not placed'

COUNT_NOT_PLACED=0

# A listed file lands here for either reason: it was never found in staging, or
# it was found but could not be placed (see the ERROR lines above).
for listed in "${LISTED_FILES[@]}"; do
    if [ -z "${PLACED[$listed]:-}" ]; then
        echo "  NOT PLACED: $listed"
        COUNT_NOT_PLACED=$((COUNT_NOT_PLACED + 1))
    fi
done

if [ "$COUNT_NOT_PLACED" -eq 0 ]; then
    echo '  (none)'
fi

echo ''
echo '=== Summary'
echo "  event files placed:                        $COUNT_COPIED"
echo "  staging files not in manifest, left alone: $COUNT_LEFT_BEHIND"
echo "  manifest entries not placed:               $COUNT_NOT_PLACED"
echo "  errors:                                    $COUNT_ERRORS"

# A file listed but never placed, or a missing directory, means the run did not
# do what the manifest asked for. Files left behind on purpose are not errors.
if [ "$COUNT_NOT_PLACED" -gt 0 ] || [ "$COUNT_ERRORS" -gt 0 ]; then
    exit 1
fi

exit 0