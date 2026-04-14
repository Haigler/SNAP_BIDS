# Event File Conversion Scripts
This is a collection of scripts that were used to convert the event files generated during runs from their original stored format to the BIDS compliant tsv/json format.

# Code Inventory
## `createTSV` scripts
These are separate scripts for converting each task's event files. They handle subject-specific malformations of the data internally which are documented in embedded comments. Summaries of deviations from expected format are summarized in the QC tracking documents for the study which should be kept in the `sourcedata` folder.

Run example:
`python createTSV_Cyberball.py`

They do not require input. Folder paths are hardcoded in the script and must be changed manually. A conda `environment.yml` and pip `requirements.txt` file have been provided to document package versions used.

## `move_eventfiles` script
This shell script moves all event files for a specified task into the BIDS hierarchy. It verifies event files present against a manifest (`./manifest`) of expected files. See the QC tracking documents (in the `sourcedata` folder) for further information about missing files.

Run example:
`move_eventfiles.sh cyberball`

Available tasks:
    + cyberball
    + **TK**

Folder paths are hardcoded in the script and must be changed manually.

## Progress
Below is the current state of the event file conversions.

+ **Cyberball** -- Needs diffcheck QC review and json creation.
+ **GoNoGo** -- Ready for code review.
+ **DotProbe** -- Ready for code review.
+ **Driving** -- Ready for code review.
+ **Driving Practice** -- Need to review source event files to determine data to keep.
+ **Emotion** -- Ready for code review.
+ **Feedback** -- Ready for code review.
+ **Team** -- Ready for code review.
+ **Team Pre** -- Ready for code review.
+ **Team Post** -- Ready for code review.

## Process
The process of event file conversion includes the following stages.

1. code development
2. code review and testing against all event files
3. tsv output review -- visual inspection of converted event files to note an gross deviation from expected output, with additional code updates as needed.
4. tsv output review -- 10% of files checked against manual conversion by an independent reviewer
5. json creation and review
6. organization of tsv/json into the BIDS data hierarchy

### Before Code Development
Note that prior to code development, work began with 

1. Locating and collecting all event files into a single development location with renaming as needed to distinguish multiple runs.
2. A thorough review of the source event files to identify what data to keep, 
3. Creation of a flow chart outlining in step-by-step fashion how to convert a file by hand, 
4. Creation of an example tsv file from a single subject, 
5. Creation of a template json file for each task. 

These preliminaries represent a substantial amount of upfront work, but is highly recommended to streamline the conversion proccess.

### Note on Code Review
To aid code review, a single manually generated tsv file created by graduates students in consultation with the creators of the tasks (step 3 in [Before Code Development](#before-code-development)) was compared to the code-generated tsv file for a subject and differences highlighted. This process was distinct and occurred before the 10% tsv file review described in [step 3 of Process](#process)


