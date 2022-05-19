# DotProbe TASK
# This script converts the original GoNoGo files that were exported from ePrime to the BIDS compliant tsv format.
# Only data deemed relevant for analysis have been retained, however this has been construed broadly.

from os import listdir
from os.path import isfile, join
import numpy as np
import pandas

# turning off a warning that occurs with some chained commands.
pandas.options.mode.chained_assignment = None


class Data:
    def __init__(self, dataFileName):
        self.contents = None
        self.dataFile = dataFileName
        self.stimuli = [Drive()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'yellow_light_onset', 'reaction_time', 'reaction_scantime',
                       'red_light_onset', 'crash_onset', 'trial_type', 'decision', 'decision_timing', 'outcome',
                       'trial']
        return writeFields

    def load(self):
        # These try-except blocks have been tailored to the particular data files being parsed in order to accommodate
        # the different encodings that were encountered
        try:
            self.contents = pandas.read_csv(self.dataFile, usecols=self.readFields)
        except:
            raise Exception('Unable to load {}'.format(self.dataFile))

    def clean(self):
        cleanedData = pandas.DataFrame(columns=self.writeFields)

        # go through each stimuli type and reorganize data belonging to this type
        for stimType in self.stimuli:
            stimData = stimType.clean(self.contents, self.writeFields)
            cleanedData = pandas.concat([cleanedData, stimData])

        # replace all nan with 'NA'
        cleanedData.replace(np.nan, 'NA', inplace=True)

        # sort by onset time
        cleanedData.sort_values(by='onset', inplace=True)

        self.contents = cleanedData

    def write(self, outputfile):
        if self.contents is not None:
            self.contents.to_csv(outputfile, sep='\t', index=False)


# specific types of stimuli in the task
class Drive:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.yellow_light_onset = None
        self.reaction_time = None
        self.reaction_scantime = None
        self.red_light_onset = None
        self.crash_onset = None
        self.trial_type = None
        self.decision = None
        self.decision_timing = None
        self.outcome = None
        self.trial = None

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['DriveOnset']
        self.yellow_light_onsetField = ['YellowOnset']
        self.reaction_timeField = ['DecisionOnset', 'YellowOnset']
        self.reaction_scantimeField = ['DecisionOnset']
        self.red_light_onsetField = ['RedOnset']
        self.crash_onsetField = ['CrashOnset']
        self.trial_typeField = ['TrialTypeWord']
        self.decisionField = ['DecisionEventName']
        self.decision_timingField = ['RedEventName']
        self.outcomeField = ['CrashEventName']
        self.trialField = ['Round']
        self.inputFields = list(set(self.onsetField + self.yellow_light_onsetField \
                                    + self.reaction_timeField + self.reaction_scantimeField \
                                    + self.red_light_onsetField + self.crash_onsetField + self.trial_typeField \
                                    + self.decisionField + self.decision_timingField + self.outcomeField \
                                    + self.trialField))

    def error_check(self, dataName, data, dataDict=None):
        if dataName == 'decision_timing':
            # Check if there exists other event names to recode since documentation was lacking on this aspect.
            possibleVals = set(dataDict.values()) | set([np.nan])
            entriesNotConverted = set(data.iloc[:, 0]).difference(possibleVals)
            if entriesNotConverted:
                pass
                #raise Exception('Entries not accounted for in recoding of decision_timing values')

    def clean(self, rawData, outputFields):
        # sort raw data by onset - needed for some calculations
        rawData = rawData.sort_values(by=self.onsetField).reset_index(drop=True)
        # Some missing entries had spaces, replacing these with NaN
        rawData = rawData.replace('^\s*$', np.NaN, regex=True)

        # extract onset time
        # note that collaborators in Oregon decided that the 2050 value added to the onsets and scan time was needed to correct timing differences in the original code after porting to ePrime, however the exact justification for this was not recorded. This information was obtained from Dr. Eva Telzer during a meeting on Feb 16th, 2021.
        onset = rawData[self.onsetField] + 2050
        onset = onset.rename(columns={onset.columns[0]: 'onset'})

        # calculate trial duration data
        duration = rawData[self.onsetField].diff()
        indx = duration.index.tolist()[1:] + [0]
        duration = duration.reindex(indx).reset_index(drop=True) # shifting calculated durations one row up
        duration = duration.rename(columns={duration.columns[0]: 'duration'})

        # extract yellow light onset
        yellow_light_onset = rawData[self.yellow_light_onsetField].astype(float).astype('Int64')
        yellow_light_onset = yellow_light_onset + 2050
        yellow_light_onset = yellow_light_onset.rename(columns={yellow_light_onset.columns[0]: 'yellow_light_onset'})

        # calculate reaction time
        reaction_time = rawData[self.reaction_timeField].astype(float).astype('Int64')
        reaction_time = reaction_time['DecisionOnset'] - reaction_time['YellowOnset']
        reaction_time = reaction_time.to_frame('reaction_time')

        # extract reaction scan time
        reaction_scantime = rawData[self.reaction_scantimeField].astype(float).astype('Int64')
        reaction_scantime = reaction_scantime + 2050
        reaction_scantime = reaction_scantime.rename(columns={reaction_scantime.columns[0]: 'reaction_scantime'})

        # extract red light onset
        red_light_onset = rawData[self.red_light_onsetField].astype(float).astype('Int64')
        red_light_onset = red_light_onset + 2050
        red_light_onset = red_light_onset.rename(columns={red_light_onset.columns[0]: 'red_light_onset'})

        # extract crash onset
        crash_onset = rawData[self.crash_onsetField].astype(float).astype('Int64')
        crash_onset = crash_onset + 2050
        crash_onset = crash_onset.rename(columns={crash_onset.columns[0]: 'crash_onset'})

        # extract trial type
        trial_type = rawData[self.trial_typeField]
        trial_type = trial_type.rename(columns={trial_type.columns[0]: 'trial_type'})

        # extract decision
        decision = rawData[self.decisionField]
        decision = decision.rename(columns={decision.columns[0]: 'decision'})

        # recode decision timing
        decision_timing = rawData[self.decision_timingField]
        decision_timingRecodeVals = {"red": "DecisionBeforeRed", "cra": "GoAfterRed", "Bra": "Brake"}
        decision_timing = decision_timing.rename(columns={decision_timing.columns[0]: 'decision_timing'})
        decision_timing = decision_timing.replace({"decision_timing": decision_timingRecodeVals})
        self.error_check('decision_timing', decision_timing, decision_timingRecodeVals)

        # fix crash onset timing for delayed decisions
        if (decision_timing['decision_timing'] == "GoAfterRed").any():
            bar = 2 #debugging
        crash_onset.loc[decision_timing['decision_timing'] == "GoAfterRed", 'crash_onset'] += 300

        # extract outcome
        outcome = rawData[self.outcomeField]
        outcome = outcome.rename(columns={outcome.columns[0]: 'outcome'})

        # strip leading string from trial
        trial = rawData[self.trialField]
        trial = trial.rename(columns={trial.columns[0]: 'trial'})
        trial = trial['trial'].replace('^round-', '', regex=True)

        data = pandas.concat([onset, duration, yellow_light_onset, reaction_time, reaction_scantime, red_light_onset,
                              crash_onset, trial_type, decision, decision_timing, outcome, trial], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data


# path to data
basefolder = "/mnt/magaj/SNAP/Data/Task Behavioral Data for BIDS/"
snap1datadir = basefolder + "SNAP 1/Driving/Driving Scan CSV/"
snap1practiceDatadir = basefolder + "SNAP 1/Driving/Driving Practice CSV/"

# getting list of files
snap1files = [f for f in listdir(snap1datadir) if isfile(join(snap1datadir, f))]
snap1pacticeFiles = [f for f in listdir(snap1practiceDatadir) if isfile(join(snap1practiceDatadir, f))]

# output folder
snap1outdir = basefolder + "Converted Files/SNAP 1/Driving/"
snap1practiceOutdir = basefolder + "Converted Files/SNAP 1/Driving/Driving Practice/"

# read, clean, and write data
seenIDs = []
for datafile in snap1files:
    thisData = Data(join(snap1datadir, datafile))
    subjID = str(''.join(filter(str.isdigit, datafile)))

    try:
        thisData.load()
        thisData.clean()

        if subjID in seenIDs:
            # making sure there is no duplicate file as this would silently overwrite output from the first file
            raise Exception('Two file names found with the numbers {}. Rename to prevent overwriting.'.format(subjID))
        else:
            seenIDs.append(subjID)
            outputfile = "sub-" + subjID.zfill(5) + "_task-driving_run01_events.tsv"

        thisData.write(join(snap1outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))

# Disabling until it's decided how to handle the practice files
if False:
    seenIDs = []
    for datafile in snap1pacticeFiles:
        thisData = Data(join(snap1practiceDatadir, datafile))
        subjID = str(''.join(filter(str.isdigit, datafile)))

        try:
            thisData.load()
            thisData.clean()

            if subjID in seenIDs:
                # making sure there is no duplicate file as this would silently overwrite output from the first file
                raise Exception('Two file names found with the numbers {}. Rename to prevent overwriting.'.format(subjID))
            else:
                seenIDs.append(subjID)
                outputfile = "sub-" + subjID.zfill(5) + "_task-drivingPractice_run01_events.tsv"

            thisData.write(join(snap1practiceOutdir, outputfile))
        except:
            raise Exception('Unable to process subject {}'.format(subjID))
