# DICOM Anonymization
## 1. Copy files to be anonymized to the AnonDcm folder 
## 2. Open DicomBrowser by clicking on the icon on your desktop
## 3. Click on 'File' and then Open, navigate to your DICOMs in the AnonDcm folder and load them here. Multiple DICOMs can be chosen at a time. 
## 4. In the left pain, select all subjects
## 5. Click on the value of the below attributes, alter it to "Anonymous"
+ InstanceCreationDate
+ StudyDate
+ SeriesDate
+ AcquisitionDate
+ ContentDate
+ PerformingPhysicianName
+ PatientName
+ PatientID
+ PatientBirthDate
+ PatientSize
+ PatientWeight
+ Private_0029_1019
+ PerformedProcedureStepStartDate
## 6. Check that all of the above fields are now "Anonymous"
## 7. Save these DICOMS by "overwriting existing directory."

http://dicomlookup.com/ is a resource which can help find tags.
