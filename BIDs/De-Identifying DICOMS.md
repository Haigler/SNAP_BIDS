# DICOM Anonymization
## 1. Download DicomBrowser https://nrg.wustl.edu/software/dicom-browser/
## 2. Running java -jar packagename.jar in the Terminal to run the application (We changed the package name to DicomBrowser.jar)
## 3. Click on 'File' and then Open, navigate to your DICOMs and load them here. Multiple DICOMs can be chosen at a time. 
## 4. Click on the value of an attribute, alter it to what you want, this would change all the subsequent values. We made the following attributes anonymous:
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

## 5. Save these DICOMS in CALM/Data/CALM_fMRI/AnonDcm with -anon appended.

http://dicomlookup.com/ is a resource which can help find tags.
