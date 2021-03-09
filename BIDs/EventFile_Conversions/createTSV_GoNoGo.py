# GoNoGo TASK
# This script converts the original GoNoGo files that were exported from ePrime to the BIDS compliant tsv format.
# Only data deemed relevant for analysis have been retained, however this has been construed broadly.

from os import listdir
from os.path import isfile, join
import numpy as np
import pandas


class Data:
    def __init__(self, dataFileName):
        self.contents = None
        self.dataFile = dataFileName
        self.stimuli = [HereWeGo(), Interblock(), Image()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'stimulus_type', 'valence', 'gonogo', 'response', 'reaction_time',
                       'reaction_scan_time', 'image_onset', 'image_duration', 'letter_onset', 'letter_duration',
                       'image_file', 'letter', 'set', 'trial', 'block']
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
        cleanedData = self.__shiftTime(cleanedData)

        # replace all nan with 'NA'
        cleanedData.replace(np.nan, 'NA', inplace=True)

        # sort by onset time
        cleanedData.sort_values(by='onset', inplace=True)

        self.contents = cleanedData

    def __shiftTime(self, data):
        firstOnset = data['onset'].min()

        data['onset'] = data['onset'].astype(int) - firstOnset
        data['reaction_scan_time'] = data['reaction_scan_time'].astype('Int64') - firstOnset
        data['image_onset'] = data['image_onset'].astype('Int64') - firstOnset
        data['letter_onset'] = data['letter_onset'].astype('Int64') - firstOnset

        return data

    def write(self, outputfile):
        if self.contents is not None:
            self.contents.to_csv(outputfile, sep='\t', index=False)


# specific types of stimuli in the task
class HereWeGo:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = 3000
        self.stimulus_type = "HereWeGo"
        self.valence = "NA"
        self.gonogo = np.nan
        self.response = np.nan
        self.reaction_time = np.nan
        self.reaction_scan_time = np.nan
        self.image_onset = np.nan
        self.image_duration = np.nan
        self.letter_onset = np.nan
        self.letter_duration = np.nan
        self.image_file = "NA"
        self.letter = "NA"
        self.set = np.nan
        self.trial = np.nan
        self.block = np.nan
        # column headers of the specific data to import for this stimuli
        self.onsetField = ['HereWeGo.OnsetTime', 'HereWeGo1.OnsetTime', 'HereWeGo2.OnsetTime',
                           'HereWeGo3.OnsetTime', 'HereWeGo4.OnsetTime']
        self.inputFields = self.onsetField

    def error_check(self, dataName, data):
        if dataName == 'onset':
            # Check that there is only one entry per row
            numEntries = data.count(axis=1)
            if (numEntries > 1).any():
                raise Exception('Multiple line entries found for HereWeGo onsets')

    def clean(self, rawData, outputFields):
        # combine onset data into one column
        onset = rawData[self.onsetField]
        onset = onset.drop_duplicates()
        self.error_check('onset', onset)

        data = onset.sum(axis=1, min_count=1).to_frame('onset').astype(int)

        # create columns for each field with the static values set at initialization
        # this crucially depends on a few assumptions:
        #   1. The outputFields have the same names as attributes set at initialization.
        #   2. Each attribute to skip (i.e. it was processed and should already be in the dataframe)
        #       has been initialized to the value None.
        #   3. Each attribute to add has been assigned a constant value.
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data


class Interblock:
    def __init__(self):
        self.onset = None
        self.duration = 7000
        self.stimulus_type = "Interblock"
        self.valence = "NA"
        self.gonogo = np.nan
        self.response = np.nan
        self.reaction_time = np.nan
        self.reaction_scan_time = np.nan
        self.image_onset = np.nan
        self.image_duration = np.nan
        self.letter_onset = np.nan
        self.letter_duration = np.nan
        self.image_file = "NA"
        self.letter = "NA"
        self.set = np.nan
        self.trial = np.nan
        self.block = np.nan
        # column headers of the specific data to import for this stimuli
        self.onsetField = ['Interblock.OnsetTime', 'Interblock1.OnsetTime', 'Interblock2.OnsetTime',
                           'Interblock3.OnsetTime', 'Interblock4.OnsetTime']
        self.inputFields = self.onsetField

    def error_check(self, dataName, data):
        if dataName == 'onset':
            # Check that there is only one entry per row
            numEntries = data.count(axis=1)
            if (numEntries > 1).any():
                raise Exception('Multiple line entries found for Interblock onsets')

    def clean(self, rawData, outputFields):
        # combine onset data into one column
        onset = rawData[self.onsetField]
        onset = onset.drop_duplicates()
        self.error_check('onset', onset)

        data = onset.sum(axis=1, min_count=1).to_frame('onset').astype(int)

        # create columns for each field with the values set at initialization
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data


class Image:
    def __init__(self):
        self.onset = None
        self.duration = 800
        self.stimulus_type = "Image/Letter"
        self.valence = None
        self.gonogo = None
        self.response = None
        self.reaction_time = None
        self.reaction_scan_time = None
        self.image_onset = None
        self.image_duration = 300
        self.letter_onset = None
        self.letter_duration = 500
        self.image_file = None
        self.letter = None
        self.set = None
        self.trial = None
        self.block = None
        # column headers of the specific data to import for this stimuli
        self.onsetField = ['Image.OnsetTime', 'Image1.OnsetTime', 'Image2.OnsetTime',
                           'Image3.OnsetTime', 'Image4.OnsetTime']
        self.valenceField = ['Valence']
        self.gonogoField = ['Go_NoGo']
        self.responseField = ['Letter.RESP', 'Letter1.RESP', 'Letter2.RESP', 'Letter3.RESP', 'Letter4.RESP']
        self.reaction_timeField = ['Letter.RT', 'Letter1.RT', 'Letter2.RT', 'Letter3.RT', 'Letter4.RT']
        self.reaction_scan_timeField = ['Letter.RTTime', 'Letter1.RTTime', 'Letter2.RTTime',
                                        'Letter3.RTTime', 'Letter4.RTTime']
        self.image_onsetField = ['Image.OnsetTime', 'Image1.OnsetTime', 'Image2.OnsetTime', 'Image3.OnsetTime',
                                 'Image4.OnsetTime']
        self.letter_onsetField = ['Letter.OnsetTime', 'Letter1.OnsetTime', 'Letter2.OnsetTime',
                                  'Letter3.OnsetTime', 'Letter4.OnsetTime']
        self.image_fileField = ['Image']
        self.letterField = ['Letter']
        self.setField = ['Procedure[Trial]']
        self.trialField = ['SubTrial']
        self.blockField = ['Trial']
        self.inputFields = list(set(self.onsetField + self.valenceField + self.gonogoField + self.responseField \
                                    + self.reaction_timeField + self.reaction_scan_timeField + self.image_onsetField \
                                    + self.letter_onsetField + self.image_fileField + self.letterField + self.setField \
                                    + self.trialField + self.blockField))

    def error_check(self, dataName, data):
        if dataName == 'onset' or 'response' or 'reaction_time' or 'reaction_scan_time' or 'image_onset' \
                or 'letter_onset':
            # Check that there is only one entry per row
            numEntries = data.count(axis=1)
            if (numEntries > 1).any():
                raise Exception('Multiple line entries found for Image {}'.format(dataName))

    def clean(self, rawData, outputFields):
        # combine onset data into one column
        onset = rawData[self.onsetField]
        self.error_check('onset', onset)
        onset = onset.sum(axis=1, min_count=1).to_frame('onset').astype(int)

        # recode values for valence
        valence = rawData[self.valenceField]
        valenceRecodeVals = {"NS": "NegScrambled", "PS": "PosScrambled",
                             "P": "Positive", "N": "Negative"}
        valence = valence.rename(columns={valence.columns[0]: 'valence'})
        valence = valence.replace({"valence": valenceRecodeVals})

        gonogo = rawData[self.gonogoField]
        gonogo = gonogo.rename(columns={gonogo.columns[0]: 'gonogo'})

        # combine response data into one column
        response = rawData[self.responseField]
        self.error_check('response', response)
        response = response.sum(axis=1, min_count=1).to_frame('response').astype('Int64')

        # combine reaction time
        reaction_time = rawData[self.reaction_timeField].replace(0, np.nan)
        self.error_check('reaction_time', reaction_time)
        reaction_time = reaction_time.sum(axis=1, min_count=1).to_frame('reaction_time').astype('Int64')

        # combine reaction scan time
        reaction_scan_time = rawData[self.reaction_scan_timeField].replace(0, np.nan)
        self.error_check('reaction_scan_time', reaction_scan_time)
        reaction_scan_time = reaction_scan_time.sum(axis=1, min_count=1).to_frame('reaction_scan_time').astype('Int64')

        # combine image onset
        image_onset = rawData[self.image_onsetField]
        self.error_check('image_onset', image_onset)
        image_onset = image_onset.sum(axis=1, min_count=1).to_frame('image_onset').astype(int)

        # combine letter onset
        letter_onset = rawData[self.letter_onsetField]
        self.error_check('letter_onset', letter_onset)
        letter_onset = letter_onset.sum(axis=1, min_count=1).to_frame('letter_onset').astype(int)

        image_file = rawData[self.image_fileField]
        image_file = image_file.apply(lambda s: s.str.replace('\\', '/')) # replacing escaped backslash in file names
        image_file = image_file.rename(columns={image_file.columns[0]: 'image_file'})

        letter = rawData[self.letterField]
        letter = letter.rename(columns={letter.columns[0]: 'letter'})

        # recode values for set
        set = rawData[self.setField]
        setRecodeVals = {"Neg1S": "ScramNeg1", "Neg2S": "ScramNeg2",
                         "Pos1S": "ScramPos1", "Pos2S": "ScramPos2"}
        set = set.rename(columns={set.columns[0]: 'set'})
        set = set.replace({"set": setRecodeVals})

        trial = rawData[self.trialField]
        trial = trial.rename(columns={trial.columns[0]: 'trial'})

        block = rawData[self.blockField]
        block = block.rename(columns={block.columns[0]: 'block'})

        data = pandas.concat([onset, valence, gonogo, response, reaction_time, reaction_scan_time,
                              image_onset, letter_onset, image_file, letter, set, trial, block], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data


# path to data
basefolder = "/mnt/magaj/SNAP/Data/Task Behavioral Data for BIDS/"
snap2datadir = basefolder + "SNAP 2/Emotional Go_No-go (Reaction)/"
snap3datadir = basefolder + "SNAP 3/Emotional Go_No-go (Reaction)/"

# getting list of files
snap2files = [f for f in listdir(snap2datadir) if isfile(join(snap2datadir, f))]
snap3files = [f for f in listdir(snap3datadir) if isfile(join(snap3datadir, f))]

# output folder
snap2outdir = basefolder + "Converted Files/SNAP 2/GoNoGo/"
snap3outdir = basefolder + "Converted Files/SNAP 3/GoNoGo/"

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
            outputfile = "sub-" + subjID.zfill(5) + "_task-gonogo_run01.tsv"

        thisData.write(join(snap2outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))

seenIDs = []
for datafile in snap3files:
    thisData = Data(join(snap3datadir, datafile))
    subjID = str(''.join(filter(str.isdigit, datafile)))

    try:
        thisData.load()
        thisData.clean()

        if subjID in seenIDs:
            raise Exception('Two file names found with the numbers {}. Rename to prevent overwriting.'.format(subjID))
        else:
            seenIDs.append(subjID)
            outputfile = "sub-" + subjID.zfill(5) + "_task-gonogo_run01.tsv"

        thisData.write(join(snap3outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))
