#Metadata ReadMe

BIDS requires a couple metadata files to accompany the BIDs dataset. Below are the required files organized by where in the file heirarchy they go:

STUDY
  - dataset_description.json: Key pieces of metadata BIDS requires (template included)
  - README.txt: A description of the dataset that provides an overview of the study, key pieces of metadata, and acquisition information. The example included asks for far more information than BIDS requires, and instead aims to provide all information necessary to write the methods section of a paper. (template included)
  - task-NAME_bold.json: Each functional run should have a task-name_bold.json that defines key pieces of metadata BIDS requires (template included)
  - task-NAME_events: Each functional run that has behavioral data should have a task-name_events that defines the column names in the .tsv file (exceptions: onset and duration, which BIDS can interpret without definitions) (template included)
  - participants.tsv: This file provides key information about each participant and must include the subject no. Age, sex and handedness are also often included. This file is automatically created 
  - participants.json: This file defines all column names in the participants.tsv file. (template included)
  
    Participant:
    - sessions.tsv: If your study includes multiple sessions, BIDS conversion software will create sessions.tsvs
    - sessions.json: If your study includes multiple sessions, this file will define all column names in the sessions.tsv file
  
          ANAT:
          - (Optional) sub-TK_t1w.json: As you convert the MRI data, you have the option to create sidecar .json files that contain key information about the scan not included in the .nii headers
          fMAP:
          - (Optional) sub-TK_FMAPNAME.json: As you convert the MRI data, you have the option to create sidecar .json files that contain key information about the scan not included in the .nii headers
          FUNC:
          - (Optional) sub-TK_task-NAME_run-TK_bold.json: As you convert the MRI data, you have the option to create sidecar .json files that contain key information about the scan not included in the .nii headers
          
  
  
