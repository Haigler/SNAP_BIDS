# Cyberball TASK
# This script converts the original Cyberball files that were exported from ePrime to the BIDS compliant tsv format.
# Only data deemed relevant for analysis have been retained, however this has been construed broadly.

from os import listdir
from os.path import isfile, join
import re
import numpy as np
import pandas

# turning off a warning that occurs with some chained commands.
pandas.options.mode.chained_assignment = None

class Data:
    def __init__(self, dataFileName):
        self.contents = None
        self.dataFile = dataFileName
        self.stimuli = [HereWeGo(), Rest(), Image(), Throw()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'trial_type', 'response', 'reaction_time',
                       'reaction_scantime', 'thrower', 'catcher', 'clusivity', 'block',
                       'throw_pattern', 'image_number', 'filenames', 'image_durations']
        return writeFields

    def load(self):
        # Note that some headers must be specified as a regex.
        p = '|'.join(self.readFields)
        pattern = re.compile(p)
        try:
            headers = pandas.read_csv(self.dataFile, sep='\t', index_col=0, nrows=0).columns.tolist()
            self.readFields = [s for s in headers if pattern.match(s)]
            self.contents = pandas.read_csv(self.dataFile, sep='\t', usecols=self.readFields)
        except:
            try:  # if defaults didn't work, try reading with an alternate encoding
                headers = pandas.read_csv(self.dataFile, sep='\t', index_col=0, nrows=0, encoding='utf_16_le').columns.tolist()
                self.readFields = [s for s in headers if pattern.match(s)]
                self.contents = pandas.read_csv(self.dataFile, sep='\t', usecols=self.readFields, encoding='utf_16_le')
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
class HereWeGo:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = None
        self.trial_type = "HereWeGo"
        self.response = "NA"
        self.reaction_time = np.nan
        self.reaction_scantime = np.nan
        self.thrower = "NA"
        self.catcher = "NA"
        self.clusivity = "NA"
        self.block = "NA"
        self.throw_pattern = "NA"
        self.image_number = "NA"
        self.filenames = "NA"
        self.image_durations = "NA"

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['getready1.OnsetTime', 'getready2.OnsetTime']
        self.durationField = ['getready1.OnsetTime', 'getready1.OffsetTime',
                              'getready2.OnsetTime', 'getready2.OffsetTime']
        self.inputFields = list(set(self.onsetField + self.durationField))

    def clean(self, rawData, outputFields):
        # extract onset time
        onset = rawData[self.onsetField].iloc[0]
        onset = [onset['getready1.OnsetTime'], onset['getready2.OnsetTime']]
        onset = pandas.DataFrame(onset, columns=['onset'], dtype=int)

        # extract duration
        duration = rawData[self.durationField].iloc[0]
        herewego1_duration = duration['getready1.OffsetTime'] - duration['getready1.OnsetTime']
        herewego2_duration = duration['getready2.OffsetTime'] - duration['getready2.OnsetTime']
        duration = [herewego1_duration, herewego2_duration]
        duration = pandas.DataFrame(duration, columns=['duration'], dtype=int)

        data = pandas.concat([onset, duration], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

class Rest:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = None
        self.trial_type = "Rest"
        self.response = "NA"
        self.reaction_time = np.nan
        self.reaction_scantime = np.nan
        self.thrower = "NA"
        self.catcher = "NA"
        self.clusivity = "NA"
        self.block = "NA"
        self.throw_pattern = "NA"
        self.image_number = "NA"
        self.filenames = "NA"
        self.image_durations = "NA"

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['rest1.OnsetTime', 'rest2.OnsetTime', 'rest4.OnsetTime']
        self.durationField = ['rest1.OnsetTime', 'rest1.OffsetTime',
                              'rest2.OnsetTime', 'rest2.OffsetTime',
                              'rest4.OnsetTime', 'rest4.OffsetTime']
        self.inputFields = list(set(self.onsetField + self.durationField))

    def clean(self, rawData, outputFields):
        # extract onset time
        onset = rawData[self.onsetField].iloc[0]
        onset = [onset['rest1.OnsetTime'], onset['rest2.OnsetTime'], onset['rest4.OnsetTime']]
        onset = pandas.DataFrame(onset, columns=['onset'], dtype=int)

        # extract duration
        duration = rawData[self.durationField].iloc[0]
        rest1_duration = duration['rest1.OffsetTime'] - duration['rest1.OnsetTime']
        rest2_duration = duration['rest2.OffsetTime'] - duration['rest2.OnsetTime']
        rest4_duration = duration['rest4.OffsetTime'] - duration['rest4.OnsetTime']
        duration = [rest1_duration, rest2_duration, rest4_duration]
        duration = pandas.DataFrame(duration, columns=['duration'], dtype=int)

        data = pandas.concat([onset, duration], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

class Image:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = None
        self.trial_type = "Image"
        self.response = None
        self.reaction_time = None
        self.reaction_scantime = None
        self.thrower = "NA"
        self.catcher = "NA"
        self.clusivity = "NA" # note that this will be assigned after all data sorted by onset
        self.block = "NA"
        self.throw_pattern = "NA"
        self.image_number = None
        self.filenames = "NA"
        self.image_durations = "NA"

        # column headers of the specific data to import for this stimuli
        # some fields may have variable number of headers, so use regex to match multiple headers
        self.onsetField = ['ImageDisplay\d+.OnsetTime']
        self.durationField = ['ImageDisplay\d+.OnsetTime', 'ImageDisplay\d+.OffsetTime']
        self.responseField = ['ImageDisplay\d+.RESP']
        self.reaction_timeField = ['ImageDisplay\d+.RT']
        self.reaction_scantimeField = ['ImageDisplay\d+.RTTime']
        self.image_numberField = ['ImageDisplay\d+.OnsetTime']
        self.inputFields = list(set(self.onsetField + self.durationField + self.responseField
                                    + self.reaction_timeField + self.reaction_scantimeField
                                    + self.image_numberField))

    def clean(self, rawData, outputFields):
        # raw data must be extracted across matching column headers for each row of converted data
        pattern = '|'.join(self.onsetField)
        onsetHeaders = rawData.filter(regex=pattern).iloc[0].index.tolist()

        onset = []
        duration = []
        response = []
        reaction_time = []
        reaction_scantime = []
        image_number = []
        for header in onsetHeaders:
            headerID = str(''.join(filter(str.isdigit, header)))

            # extract onset time
            h = 'ImageDisplay' + headerID + '.OnsetTime'
            onset.append(rawData[h].iloc[0])

            # calculate duration
            h1 = 'ImageDisplay' + headerID + '.OffsetTime'
            h2 = 'ImageDisplay' + headerID + '.OnsetTime'
            d = rawData[h1].iloc[0] - rawData[h2].iloc[0]
            duration.append(d)

            # extract response, reaction_time, and reaction_scantime.
            # not all images have an associated response.
            h1 = 'ImageDisplay' + headerID + '.RESP'
            h2 = 'ImageDisplay' + headerID + '.RT'
            h3 = 'ImageDisplay' + headerID + '.RTTime'
            try:
                response.append(rawData[h1].iloc[0])
                reaction_time.append(rawData[h2].iloc[0])
                reaction_scantime.append(rawData[h3].iloc[0])
            except:
                response.append("NA")
                reaction_time.append(np.nan)
                reaction_scantime.append(np.nan)

            image_number.append(int(headerID))

        onset = pandas.DataFrame(onset, columns=['onset'], dtype=int)
        duration = pandas.DataFrame(duration, columns=['duration'], dtype=int)

        # recode response
        response = pandas.DataFrame(response, columns=['response'], dtype=str)
        responseRecodeVals = {'2': "CHANGETHIS!!", '7': "CHANGETHIS!!"}
        response = response.replace({'response': responseRecodeVals})

        reaction_time = pandas.DataFrame(reaction_time, columns=['reaction_time'], dtype=pandas.Int64Dtype())
        reaction_scantime = pandas.DataFrame(reaction_scantime, columns=['reaction_scantime'], dtype=pandas.Int64Dtype())

        image_number = pandas.DataFrame(image_number, columns=['image_number'],
                                             dtype=int)

        data = pandas.concat([onset, duration, response, reaction_time, reaction_scantime,
                              image_number], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

class Throw:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = None
        self.trial_type = "Throw"
        self.response = "NA"
        self.reaction_time = np.nan
        self.reaction_scantime = np.nan
        self.thrower = None
        self.catcher = None
        self.clusivity = "NA" # note that this will be assigned after all data sorted by onset
        self.block = None
        self.throw_pattern = None
        self.image_number = "NA"
        self.filenames = None
        self.image_durations = None

        # column headers of the specific data to import for this stimuli
        # some fields may have variable number of headers, so use regex to match multiple headers
        self.onsetField = ['MyImageDisplay.OnsetTime']
        self.durationField = ['MyImageDisplay.OnsetTime', 'MyImageDisplay.OffsetTime']
        self.throwerField = ['filename']
        self.catcherField = ['filename']
        self.blockField = ['Block']
        self.throw_patternField = ['Running\[Block\]']
        self.filenamesField = ['filename']
        self.image_durationsField = ['MyImageDisplay.OnsetTime', 'MyImageDisplay.OffsetTime']
        self.inputFields = list(set(self.onsetField + self.durationField + self.throwerField
                                    + self.catcherField + self.blockField + self.throw_patternField
                                    + self.filenamesField + self.image_durationsField))

    def clean(self, rawData, outputFields):
        # data for all throw events are within the same columns
        # must parse filenames column to identify individual events
        names = rawData['filename'].str.replace(r'.\d.bmp', '')
        eventStart = (names != names.shift(periods=1))
        eventEnd = (names != names.shift(periods=-1))

        # extract onsets
        onset = rawData[self.onsetField].loc[eventStart]
        onset = onset.rename(columns={onset.columns[0]: 'onset'}).reset_index(drop=True)

        # calculate duration
        offset = rawData['MyImageDisplay.OffsetTime'].loc[eventEnd].reset_index(drop=True)
        duration = offset - onset['onset']
        duration = duration.to_frame('duration').astype('Int64')

        # extract thrower and recode
        thrower = rawData['filename'].loc[eventStart]
        thrower = thrower.str.replace(r'to\d.\d.bmp', '')
        # double cast as work around for pandas bug. See github.com/pandas-dev/pandas/pull/43949
        thrower = thrower.reset_index(drop=True).to_frame('thrower').astype(float).astype('Int64')
        throwerRecodeVals = {1: "bar", 2: "subject", 3: "foo"}
        thrower = thrower.replace({"thrower": throwerRecodeVals})

        # extract catcher and recode
        catcher = rawData['filename'].loc[eventStart]
        catcher = catcher.str.replace(r'\dto', '').str.replace(r'.\d.bmp', '')
        catcher = catcher.reset_index(drop=True).to_frame('catcher').astype(float).astype('Int64')
        catcherRecodeVals = {1: "bar", 2: "subject", 3: "foo"}
        catcher = catcher.replace({"catcher": catcherRecodeVals})

        # extract block
        block = rawData[self.blockField].loc[eventStart]
        block = block.reset_index(drop=True).rename(columns={block.columns[0]: 'block'}).astype(int)

        # extract throw pattern
        throw_pattern = rawData['Running[Block]'].loc[eventStart]
        throw_pattern = throw_pattern.str.replace(r'throw', '')
        throw_pattern = throw_pattern.reset_index(drop=True).to_frame('throw_pattern').astype(str)

        # extract filenames and image durations
        eventFiles = []
        eventDurations = []
        for i, fname in rawData['filenames']:
            if eventStart[i]:
                pass

        data = pandas.concat([onset, duration, thrower, catcher,
                              block, throw_pattern], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

# path to data
basefolder = "/mnt/magaj/SNAP/Data/Task Behavioral Data for BIDS/"
snap1datadir = basefolder + "SNAP 1/Cyberball (Catch)/"
snap2datadir = basefolder + "SNAP 2/Cyberball (Catch)/"
snap3datadir = basefolder + "SNAP 3/Cyberball (Catch)/"
snapdatadir = [snap1datadir, snap2datadir, snap3datadir]

# getting list of files
snap1files = [f for f in listdir(snap1datadir) if isfile(join(snap1datadir, f))]
snap2files = [f for f in listdir(snap2datadir) if isfile(join(snap2datadir, f))]
snap3files = [f for f in listdir(snap3datadir) if isfile(join(snap3datadir, f))]
snapfiles = [snap1files, snap2files, snap3files]

# output folder
snap1outdir = basefolder + "Converted Files/SNAP 1/Cyberball/"
snap2outdir = basefolder + "Converted Files/SNAP 2/Cyberball/"
snap3outdir = basefolder + "Converted Files/SNAP 3/Cyberball/"
snapoutdir = [snap1outdir, snap2outdir, snap3outdir]

# read, clean, and write data
seenIDs = []
for datadir, files, outdir in zip(snapdatadir, snapfiles, snapoutdir):
    for datafile in files:
        thisData = Data(join(datadir, datafile))
        subjID = str(''.join(filter(str.isdigit, datafile)))

        try:
            thisData.load()
            thisData.clean()

            if subjID in seenIDs:
                # making sure there is no duplicate file as this would silently overwrite output from the first file
                raise Exception('Two file names found with the numbers {}. Rename to prevent overwriting.'.format(subjID))
            else:
                seenIDs.append(subjID)
                outputfile = "sub-" + subjID.zfill(5) + "_task-cyberball_run-01_events.tsv"

            thisData.write(join(outdir, outputfile))
        except:
            raise Exception('Unable to process subject {}'.format(subjID))
