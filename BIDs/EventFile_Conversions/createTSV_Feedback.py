# Feedback TASK
# This script converts the original Feedback files that were exported from ePrime to the BIDS compliant tsv format.
# Only data deemed relevant for analysis have been retained, however this has been construed broadly.

from os import listdir
from os.path import isfile, join
import numpy as np
import pandas


class Data:
    def __init__(self, dataFileName):
        self.contents = None
        self.dataFile = dataFileName
        self.stimuli = [Choice()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'stim_onset', 'stim_duration', 'reaction_time',
                       'reaction_scantime', 'anticipation_onset', 'anticipation_duration', 'feedback_onset',
                       'feedback_duration', 'feedback_type', 'stim_category', 'left_word', 'right_word',
                       'response', 'trial', 'block']
        return writeFields

    def load(self):
        try:
            self.contents = pandas.read_csv(self.dataFile, sep='\t', usecols=self.readFields, encoding='utf_16_le')
        except:
            raise Exception('Unable to load {}'.format(self.dataFile))

    def clean(self):
        cleanedData = pandas.DataFrame(columns=self.writeFields)

        # go through each stimuli type and reorganize data belonging to this type
        for stimType in self.stimuli:
            stimData = stimType.clean(self.contents, self.writeFields)
            cleanedData = pandas.concat([cleanedData, stimData])

        # shift all time stamps so the experiment starts at time 0
        #cleanedData = self.__shiftTime(cleanedData)

        # sort by onset time -- some of the onset data is incomplete so sorting before replacing NaNs.
        cleanedData.sort_values(by='onset', inplace=True, na_position='last')

        # replace all nan with 'NA'
        cleanedData.replace(np.nan, 'NA', inplace=True)

        self.contents = cleanedData

    def __shiftTime(self, data):
        firstOnset = data['onset'].min()

        data['onset'] = data['onset'].astype(int) - firstOnset
        data['stim_onset'] = data['stim_onset'].astype(int) - firstOnset
        data['reaction_scantime'] = data['reaction_scantime'].astype(int) - firstOnset
        data['anticipation_onset'] = data['anticipation_onset'].astype(int) - firstOnset
        data['feedback_onset'] = data['feedback_onset'].astype(int) - firstOnset

        return data

    def write(self, outputfile):
        if self.contents is not None:
            self.contents.to_csv(outputfile, sep='\t', index=False)


# specific types of stimuli in the task
class Choice:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = None
        self.stim_onset = None
        self.stim_duration = None
        self.reaction_time = None
        self.reaction_scantime = None
        self.anticipation_onset = None
        self.anticipation_duration = 2000
        self.feedback_onset = None
        self.feedback_duration = None
        self.feedback_type = None
        self.stim_category = None
        self.left_word = None
        self.right_word = None
        self.response = None
        self.trial = None
        self.block = None
        # column headers of the specific data to import for this stimuli
        self.onsetField = ['Stim.OnsetTime', 'fix.OnsetTime']
        self.durationField = ['Stim.OnsetTime']
        self.stim_onsetField = ['Stim.OnsetTime', 'fix.OnsetTime']
        self.stim_durationField = ['Stim.RT']
        self.reaction_timeField = ['Stim.RT']
        self.reaction_scantimeField = ['Stim.RTTime', 'fix.OnsetTime']
        self.anticipation_onsetField = ['Anticipation.OnsetTime', 'fix.OnsetTime']
        self.feedback_onsetField = ['Feedback.OnsetTime', 'fix.OnsetTime']
        self.feedback_durationField = ['Feedback.Duration']
        self.feedback_typeField = ['Feedbacktype']
        self.stim_categoryField = ['Category']
        self.left_wordField = ['LeftWord']
        self.right_wordField = ['RightWord']
        self.responseField = ['Stim.RESP']
        self.trialField = ['Trial']
        self.blockField = ['Block']
        self.inputFields = list(set(self.onsetField + self.durationField + self.stim_onsetField \
                                    + self.stim_durationField + self.reaction_timeField \
                                    + self.reaction_scantimeField + self.anticipation_onsetField \
                                    + self.feedback_onsetField + self.feedback_durationField \
                                    + self.feedback_typeField + self.stim_categoryField + self.left_wordField \
                                    + self.right_wordField + self.responseField + self.trialField \
                                    + self.blockField ))

    def clean(self, rawData, outputFields):
        # calculate onset time
        onset = rawData['Stim.OnsetTime'] - rawData['fix.OnsetTime']
        onset = onset.to_frame('onset').astype('Int64')

        # combine duration data into one column
        duration = rawData[self.durationField]
        duration = duration.diff()
        duration = duration.reindex(index=np.roll(duration.index, -1)).reset_index(drop=True)
        duration = duration.rename(columns={duration.columns[0]: 'duration'}).astype('Int64')

        # calculate stimuli onset time
        stim_onset = rawData['Stim.OnsetTime'] - rawData['fix.OnsetTime']
        stim_onset = stim_onset.to_frame('stim_onset').astype('Int64')

        # extract stimuli duration data
        stim_duration = rawData[self.stim_durationField]
        stim_duration = stim_duration.rename(columns={stim_duration.columns[0]: 'stim_duration'})

        # extract reaction time
        reaction_time = rawData[self.reaction_timeField]
        reaction_time = reaction_time.rename(columns={reaction_time.columns[0]: 'reaction_time'})
        # change reaction time to nan when there is no response
        response = rawData[self.responseField]
        reaction_time.loc[np.isnan(response.iloc[:,0]), 'reaction_time'] = np.nan
        reaction_time = reaction_time.astype('Int64')

        # calculate reaction scan time
        reaction_scantime = rawData['Stim.RTTime'] - rawData['fix.OnsetTime']
        reaction_scantime = reaction_scantime.to_frame('reaction_scantime')
        # change reaction scan time to nan when there is no response
        response = rawData[self.responseField]
        reaction_scantime.loc[np.isnan(response.iloc[:, 0]), 'reaction_scantime'] = np.nan
        reaction_scantime = reaction_scantime.astype('Int64')

        # calculate anticipation onset
        anticipation_onset = rawData['Anticipation.OnsetTime'] - rawData['fix.OnsetTime']
        anticipation_onset = anticipation_onset.to_frame('anticipation_onset').astype('Int64')

        # calculate feedback onset
        feedback_onset = rawData['Feedback.OnsetTime'] - rawData['fix.OnsetTime']
        feedback_onset = feedback_onset.to_frame('feedback_onset').astype('Int64')

        # extract feedback duration
        feedback_duration = rawData[self.feedback_durationField]
        feedback_duration = feedback_duration.rename(columns={feedback_duration.columns[0]: 'feedback_duration'})

        # recode values for feedback type
        feedback_type = rawData[self.feedback_typeField]
        feedback_typeRecodeVals = {"Pos": "pos", "Neg": "neg", "Neut": "neu"}
        feedback_type = feedback_type.rename(columns={feedback_type.columns[0]: 'feedback_type'})
        feedback_type = feedback_type.replace({"feedback_type": feedback_typeRecodeVals})

        # extract stimulus category
        stim_category = rawData[self.stim_categoryField]
        stim_category = stim_category.rename(columns={stim_category.columns[0]: 'stim_category'})

        # extract information about word displayed on the left side
        left_word = rawData[self.left_wordField]
        left_word = left_word.rename(columns={left_word.columns[0]: 'left_word'})

        # extract information about word displayed on the right side
        right_word = rawData[self.right_wordField]
        right_word = right_word.rename(columns={right_word.columns[0]: 'right_word'})

        # recode values for response
        response = rawData[self.responseField]
        responseRecodeVals = {2: "right", 7: "left"}
        response = response.rename(columns={response.columns[0]: 'response'}).replace({'response': responseRecodeVals})

        # extract trial number
        trial = rawData[self.trialField]
        trial = trial.rename(columns={trial.columns[0]: 'trial'})

        # extract block number
        block = rawData[self.blockField]
        block = block.rename(columns={block.columns[0]: 'block'})

        data = pandas.concat([onset, duration, stim_onset, stim_duration, reaction_time, reaction_scantime,
                              anticipation_onset, feedback_onset, feedback_duration, feedback_type,
                              stim_category, left_word, right_word, response, trial, block], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data


# path to data
basefolder = "/mnt/magaj/SNAP/Data/Task Behavioral Data for BIDS/"
snap2datadir = basefolder + "SNAP 2/Social Feedback Task (Opinion)/"
snap3datadir = basefolder + "SNAP 3/Social Feedback Task (Opinion)/"

# getting list of files
snap2files = [f for f in listdir(snap2datadir) if isfile(join(snap2datadir, f))]
snap3files = [f for f in listdir(snap3datadir) if isfile(join(snap3datadir, f))]

# output folder
snap2outdir = basefolder + "Converted Files/SNAP 2/Feedback/"
snap3outdir = basefolder + "Converted Files/SNAP 3/Feedback/"

# read, clean, and write data
seenIDs = []
for datafile in snap2files:
    thisData = Data(join(snap2datadir, datafile))
    subjID = str(''.join(filter(str.isdigit, datafile)))

    try:
        thisData.load()
        thisData.clean()

        if subjID in seenIDs:
            # making sure there is no duplicate file as this would silently overwrite output from the first file
            raise Exception('Two file names found with the numbers {}. Rename to prevent overwriting.'.format(subjID))
        else:
            seenIDs.append(subjID)
            outputfile = "sub-" + subjID.zfill(5) + "_task-feedback_run01_events.tsv"

        thisData.write(join(snap2outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))


for datafile in snap3files:
    thisData = Data(join(snap3datadir, datafile))
    subjID = str(''.join(filter(str.isdigit, datafile)))

    try:
        thisData.load()
        thisData.clean()

        if subjID in seenIDs:
            # making sure there is no duplicate file as this would silently overwrite output from the first file
            raise Exception('Two file names found with the numbers {}. Rename to prevent overwriting.'.format(subjID))
        else:
            seenIDs.append(subjID)
            outputfile = "sub-" + subjID.zfill(5) + "_task-feedback_run01_events.tsv"

        thisData.write(join(snap3outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))