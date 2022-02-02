# Team TASK
# This script converts the original Team files that were exported from ePrime to the BIDS compliant tsv format.
# Only data deemed relevant for analysis have been retained, however this has been construed broadly.

from os import listdir
from os.path import isfile, join
import numpy as np
import pandas


class Data:
    def __init__(self, dataFileName):
        self.contents = None
        self.dataFile = dataFileName
        self.stimuli = [Team()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'image_onset', 'image_duration', 'reaction_time',
                       'reaction_scantime', 'response', 'group_affiliation', 'team', 'gender', 'race',
                       'filename', 'trial', 'block']
        return writeFields

    def load(self):
        try:
            self.contents = pandas.read_csv(self.dataFile, sep='\t', usecols=self.readFields)
        except:
            raise Exception('Unable to load {}'.format(self.dataFile))

    def clean(self):
        cleanedData = pandas.DataFrame(columns=self.writeFields)

        # go through each stimuli type and reorganize data belonging to this type
        for stimType in self.stimuli:
            stimData = stimType.clean(self.contents, self.writeFields)
            cleanedData = pandas.concat([cleanedData, stimData])

        # shift all time stamps so the experiment starts at time 0
        # cleanedData = self.__shiftTime(cleanedData)

        # replace all nan with 'NA'
        cleanedData.replace(np.nan, 'NA', inplace=True)

        # sort by onset time
        cleanedData.sort_values(by='onset', inplace=True)

        self.contents = cleanedData

    def __shiftTime(self, data):
        firstOnset = data['onset'].min()

        data['onset'] = data['onset'].astype(int) - firstOnset
        data['image_onset'] = data['image_onset'].astype(int) - firstOnset
        data['reaction_scantime'] = data['reaction_scantime'].astype('Int64') - firstOnset
        data['jitter_onset'] = data['jitter_onset'].astype(int) - firstOnset

        return data

    def write(self, outputfile):
        if self.contents is not None:
            self.contents.to_csv(outputfile, sep='\t', index=False)


# specific types of stimuli in the task
class Team:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = None
        self.image_onset = None
        self.image_duration = 3000
        self.reaction_time = None
        self.reaction_scantime = None
        self.response = None
        self.group_affiliation = None
        self.team = None
        self.gender = None
        self.race = None
        self.filename = None
        self.trial = None
        self.block = None

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['Stim.OnsetTime', 'HereWeGo.OnsetTime']
        self.durationField = ['Stim.OnsetTime']
        self.image_onsetField = ['Stim.OnsetTime', 'HereWeGo.OnsetTime']
        self.reaction_timeField = ['Jitter.RTTime', 'Stim.RTTime', 'Stim.OnsetTime']
        self.reaction_scantimeField = ['Jitter.RT', 'Stim.RTTime']
        self.responseField = ['Jitter.RESP', 'Stim.RESP']
        self.group_affiliationField = ['In1_Out2_C3']
        self.teamField = ['Team']
        self.genderField = ['Gender']
        self.raceField = ['Race']
        self.filenameField = ['Image']
        self.trialField = ['Trial']
        self.blockField = ['Block']
        self.inputFields = list(set(self.onsetField + self.durationField + self.image_onsetField \
                                    + self.reaction_timeField + self.reaction_scantimeField \
                                    + self.responseField + self.group_affiliationField + self.teamField \
                                    + self.genderField + self.raceField + self.filenameField \
                                    + self.trialField + self.blockField))

    def error_check(self, dataName, data):
        if dataName == 'response':
            # Verify that no response also has no reaction time and no reaction scan time recorded
            timeNAmatches = (pandas.isna(data['response']) == pandas.isna(data['reaction_time']))
            scanTimeNAmatches = (pandas.isna(data['response']) == pandas.isna(data['reaction_scantime']))
            if not timeNAmatches.all() or not scanTimeNAmatches.all():
                raise Exception('Mismatch in blank entries for response and response timings (RT and/or scan time).')

    def clean(self, rawData, outputFields):
        # calculate onset time
        onset = rawData['Stim.OnsetTime'] - rawData['HereWeGo.OnsetTime']
        onset = onset.to_frame('onset')

        # combine duration data into one column
        duration = rawData[self.durationField]
        duration = duration.diff()
        duration = duration.reindex(index=np.roll(duration.index, -1)).reset_index(drop=True)
        duration = duration.rename(columns={duration.columns[0]: 'duration'}).astype('Int64')

        # calculate image onset time
        image_onset = rawData['Stim.OnsetTime'] - rawData['HereWeGo.OnsetTime']
        image_onset = image_onset.to_frame('image_onset')

        # calculate reaction time
        # replace missing values in the probe reaction time with any responses made during the jitter
        reaction_time = rawData[self.reaction_timeField]
        reaction_time[['Stim.RTTime', 'Jitter.RTTime']] = reaction_time[['Stim.RTTime', 'Jitter.RTTime']].replace(0, np.NaN)  # no response made during probe or jitter
        reaction_time['Stim.RTTime'] = reaction_time['Stim.RTTime'].fillna(reaction_time['Jitter.RTTime'])  # replace missing stim time with jitter
        reaction_time = reaction_time['Stim.RTTime'] - reaction_time['Stim.OnsetTime']
        reaction_time = reaction_time.to_frame('reaction_time').astype('Int64')

        # calculate reaction scan time
        reaction_scantime = rawData['Stim.RTTime'].replace(0, np.NaN) - rawData['FixationInput.OffsetTime'] + 1
        reaction_scantime = reaction_scantime.to_frame('reaction_scantime').astype('Int64')

        # calculate jitter onset
        jitter_onset = rawData['jitter.OnsetTime'] - rawData['FixationInput.OffsetTime'] + 1
        jitter_onset = jitter_onset.to_frame('jitter_onset')

        # extract jitter duration
        jitter_duration = rawData[self.jitter_durationField]
        jitter_duration = jitter_duration.rename(columns={jitter_duration.columns[0]: 'jitter_duration'})

        # recode values for response
        response = rawData[self.responseField]
        # some are strings, others are floats, casting all to int for recoding.
        response = response.squeeze().astype('str').str.strip()
        response = response.to_frame('response').replace('', np.nan).astype('float').astype('Int64')
        responseRecodeVals = {2: "right", 7: "left"}
        response = response.replace({'response': responseRecodeVals})

        self.error_check('response', pandas.concat([response, reaction_time, reaction_scantime], axis=1))

        # recode correct response
        correct_response = rawData[self.correct_responseField]
        correct_response = correct_response.squeeze().astype('str').str.strip()
        correct_response = correct_response.to_frame('correct_response').replace('', np.nan).astype('float').astype(
            'Int64')  # cast to int for recoding
        correct_responseRecodeVals = {2: "right", 7: "left"}
        correct_response = correct_response.replace({'correct_response': correct_responseRecodeVals})

        # recode accuracy
        # if the correct response was NaN, also make NaN.
        accuracy = rawData['Stim.ACC']
        m = pandas.isna(correct_response).squeeze()
        accuracy = accuracy.to_frame('accuracy').mask(m, np.nan)
        accuracyRecodeVals = {1: "correct", 0: "incorrect"}
        accuracy = accuracy.replace({'accuracy': accuracyRecodeVals})

        # recode trial type
        trial_type = rawData[self.trial_typeField]
        trial_typeRecodeVals = {1: "ShapesMatch", 2: "NegObserve", 3: "NegMatch", 4: "ShapesMatch", 5: "NegObserve",
                                6: "NegMatch", 7: "PosObserve", 8: "PosObserve", 9: "PosMatch", 10: "PosMatch"}
        trial_type = trial_type.rename(columns={trial_type.columns[0]: 'trial_type'}).replace(
            {'trial_type': trial_typeRecodeVals})

        # extract target label
        target_label = rawData[self.target_labelField]
        target_label = target_label.squeeze().astype('str').str.strip()
        target_label = target_label.to_frame('target_label')

        # extract distractor label
        distractor_label = rawData[self.distractor_labelField]
        distractor_labelRecodeVals = {' ': np.nan}
        distractor_label = distractor_label.rename(columns={distractor_label.columns[0]: 'distractor_label'}).replace(
            {'distractor_label': distractor_labelRecodeVals})

        # extract ethnicity
        ethnicity = rawData[self.ethnicityField]
        ethnicityRecodeVals = {' ': np.nan}
        ethnicity = ethnicity.rename(columns={ethnicity.columns[0]: 'ethnicity'}).replace(
            {'ethnicity': ethnicityRecodeVals})

        # extract image file name
        image_file = rawData[self.image_fileField]
        image_file = image_file.rename(columns={image_file.columns[0]: 'image_file'})

        # extract set name
        set = rawData[self.setField]
        set = set.rename(columns={set.columns[0]: 'set'})

        # extract trial number
        trial = rawData[self.trialField]
        trial = trial.rename(columns={trial.columns[0]: 'trial'})

        # extract block number
        block = rawData[self.blockField]
        block = block.rename(columns={block.columns[0]: 'block'})

        data = pandas.concat([onset, duration, image_onset, image_duration, reaction_time, reaction_scantime,
                              jitter_onset, jitter_duration, response, correct_response, accuracy, trial_type,
                              target_label, distractor_label, ethnicity, image_file, set, trial, block], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data


# path to data
# note that this task has data split across several folders
basefolder = "/mnt/magaj/SNAP/Data/Task Behavioral Data for BIDS/"
# snap1datadir = basefolder + "SNAP 1/Team Game/Pre Scan Training/Edat/"
# snap1datadir = basefolder + "SNAP 1/Team Game/Pre Scan Training/New Edat/"
snap1datadir = basefolder + "SNAP 1/Team Game/Scan Task/Edat/"
# snap1datadir = basefolder + "SNAP 1/Team Game/Scan Task/New Edat/"
# snap1datadir = basefolder + "SNAP 1/Team Game/Post Scan Memory/Edat/"
# snap1datadir = basefolder + "SNAP 1/Team Game/Post Scan Memory/New Edat/"

# output folder
# snap1outdir = basefolder + "Converted Files/SNAP 1/Team/Pre Scan Training/"
snap1outdir = basefolder + "Converted Files/SNAP 1/Team/Scan Task/"
# snap1outdir = basefolder + "Converted Files/SNAP 1/Team/Post Scan Memory/"

# Error check to make sure the right input/output pair is in place
assert ("Pre Scan Training" in snap1datadir and "Pre Scan Training" in snap1outdir) or \
       ("Scan Task" in snap1datadir and "Scan Task" in snap1outdir) or \
       ("Post Scan Memory" in snap1datadir and "Post Scan Memory" in snap1outdir), \
       "Input and output directories don't correspond."

# getting list of files
snap1files = [f for f in listdir(snap1datadir) if isfile(join(snap1datadir, f))]

# output folder
snap1outdir = basefolder + "Converted Files/SNAP 1/Team/"

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
            if "Pre Scan Training" in snap1outdir:
                outputfile = "sub-" + subjID.zfill(5) + "_task-prescan-team_events.tsv"
            elif "Post Scan Memory" in snap1outdir:
                outputfile = "sub-" + subjID.zfill(5) + "_task-postscan-team_events.tsv"
            elif "Scan Task" in snap1outdir:
                outputfile = "sub-" + subjID.zfill(5) + "_task-team_run01_events.tsv"

        thisData.write(join(snap1outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))
