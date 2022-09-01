# Team Post TASK
# This script converts the original Team Post-Task (i.e. Memory Task) files that were exported from ePrime to the BIDS compliant tsv format.
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
        self.stimuli = [HereWeGo(), Sample(), PreStimulus()] #, Image(), IRI()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'reaction_time', 'reaction_exptime', 'stimulus_type',
                       'response', 'accuracy', 'group_affiliation', 'team', 'gender', 'race',
                       'filename', 'photo_group', 'trial']
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

        # drop rows with all NA/nan values
        cleanedData.dropna(how='all', inplace=True)

        # shift all time stamps so the experiment starts at time 0
        cleanedData = self.__shiftTime(cleanedData)

        # replace all nan with 'NA'
        cleanedData.replace(np.nan, 'NA', inplace=True)

        # sort by onset time
        cleanedData.sort_values(by='onset', inplace=True)

        self.contents = cleanedData

    def __shiftTime(self, data):
        firstOnset = data['onset'].min()

        data['onset'] = data['onset'].astype('Int64') - firstOnset
        data['reaction_exptime'] = data['reaction_exptime'].astype('Int64') - firstOnset

        return data

    def write(self, outputfile):
        if self.contents is not None:
            self.contents.to_csv(outputfile, sep='\t', index=False)

# specific types of stimuli in the task
class HereWeGo:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.reaction_time = np.nan
        self.reaction_exptime = np.nan
        self.stimulus_type = "HereWeGo"
        self.response = "NA"
        self.accuracy = "NA"
        self.group_affiliation = "NA"
        self.team = "NA"
        self.gender = "NA"
        self.race = "NA"
        self.filename = "NA"
        self.photo_group = "NA"
        self.trial = np.nan

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['PreSample1.OnsetTime', 'PreSample2.OnsetTime']
        self.durationField = ['PreSample1.Duration', 'PreSample2.Duration']

        self.inputFields = list(set(self.onsetField + self.durationField))

    def clean(self, rawData, outputFields):
        # extract onset time
        onset = rawData[self.onsetField].iloc[0]
        onset = [onset['PreSample1.OnsetTime'], onset['PreSample2.OnsetTime']]
        onset = pandas.DataFrame(onset, columns=['onset'], dtype=int)

        # extract duration
        duration = rawData[self.durationField].iloc[0]
        duration = [duration['PreSample1.Duration'], duration['PreSample2.Duration']]
        duration = pandas.DataFrame(duration, columns=['duration'], dtype=int)

        data = pandas.concat(
            [onset, duration], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

class Sample:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.reaction_time = None
        self.reaction_exptime = None
        self.stimulus_type = "Sample"
        self.response = None
        self.accuracy = "NA"
        self.group_affiliation = "NA"
        self.team = "NA"
        self.gender = "NA"
        self.race = "NA"
        self.filename = "NA"
        self.photo_group = "NA"
        self.trial = np.nan

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['Sample1.OnsetTime', 'Sample2.OnsetTime']
        self.durationField = ['Sample1.OffsetTime', 'Sample1.OnsetTime', 'Sample2.OffsetTime', 'Sample2.OnsetTime']
        self.reaction_timeField = ['Sample1.RT', 'Sample2.RT']
        self.reaction_exptimeField = ['Sample1.RTTime', 'Sample2.RTTime']
        self.responseField = ['Sample1.RESP', 'Sample2.RESP']

        self.inputFields = list(set(self.onsetField + self.durationField \
                                    + self.reaction_timeField + self.reaction_exptimeField \
                                    + self.responseField))

    def clean(self, rawData, outputFields):
        # extract onset time
        onset = rawData[self.onsetField].iloc[0]
        onset = [onset['Sample1.OnsetTime'], onset['Sample2.OnsetTime']]
        onset = pandas.DataFrame(onset, columns=['onset'], dtype=int)

        # extract duration
        duration = rawData[self.durationField].iloc[0]
        sample1_duration = duration['Sample1.OffsetTime'] - duration['Sample1.OnsetTime']
        sample2_duration = duration['Sample2.OffsetTime'] - duration['Sample2.OnsetTime']
        duration = [sample1_duration, sample2_duration]
        duration = pandas.DataFrame(duration, columns=['duration'], dtype=int)

        # extract reaction time
        reaction_time = rawData[self.reaction_timeField].iloc[0]
        reaction_time = [reaction_time['Sample1.RT'], reaction_time['Sample2.RT']]
        reaction_time = pandas.DataFrame(reaction_time, columns=['reaction_time'], dtype=int)

        # extract reaction experiment time
        reaction_exptime = rawData[self.reaction_exptimeField].iloc[0]
        reaction_exptime = [reaction_exptime['Sample1.RTTime'], reaction_exptime['Sample2.RTTime']]
        reaction_exptime = pandas.DataFrame(reaction_exptime, columns=['reaction_exptime'], dtype=int)

        # extract response time
        response = rawData[self.responseField].iloc[0]
        response = [response['Sample1.RESP'], response['Sample2.RESP']]
        response = pandas.DataFrame(response, columns=['response'], dtype=str)
        responseRecodeVals = {'p': "CHANGETHIS!!", 'q': "CHANGETHIS!!"}
        response = response.replace({'response': responseRecodeVals})

        data = pandas.concat(
            [onset, duration, reaction_time, reaction_exptime, response], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

class PreStimulus:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.reaction_time = np.nan
        self.reaction_exptime = np.nan
        self.stimulus_type = "PreStimulus"
        self.response = "NA"
        self.accuracy = "NA"
        self.group_affiliation = "NA"
        self.team = "NA"
        self.gender = "NA"
        self.race = "NA"
        self.filename = "NA"
        self.photo_group = "NA"
        self.trial = None

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['PreStim.OnsetTime']
        self.durationField = ['PreStim.Duration']
        self.trialField = ['Trial']

        self.inputFields = list(set(self.onsetField + self.durationField \
                                    + self.trialField))

    def clean(self, rawData, outputFields):
        # extract onset time
        onset = rawData[self.onsetField]
        onset = onset.rename(columns={onset.columns[0]: 'onset'})

        # extract duration
        duration = rawData[self.durationField]
        duration = duration.rename(columns={duration.columns[0]: 'duration'})

        # extract trial number
        trial = rawData[self.trialField]
        trial = trial.rename(columns={trial.columns[0]: 'trial'})

        data = pandas.concat(
            [onset, duration, trial], axis=1)

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
snap1datadir1 = basefolder + "SNAP 1/Team Game/Post Scan Memory/Edat/"
snap1datadir2 = basefolder + "SNAP 1/Team Game/Post Scan Memory/New Edat/"

# output folder
snap1outdir = basefolder + "Converted Files/SNAP 1/Team/Post Scan Memory/"

# getting list of files and their paths
snap1files1 = [f for f in listdir(snap1datadir1) if isfile(join(snap1datadir1, f))]
snap1files1path = [snap1datadir1 for d in snap1files1]
snap1files2 = [f for f in listdir(snap1datadir2) if isfile(join(snap1datadir2, f))]
snap1files2path = [snap1datadir2 for d in snap1files2]
snap1files = snap1files1 + snap1files2
snap1datadir = snap1files1path + snap1files2path

# read, clean, and write data
seenIDs = []
for i, datafile in enumerate(snap1files):
    thisData = Data(join(snap1datadir[i], datafile))
    subjID = str(''.join(filter(str.isdigit, datafile)))

    try:
        thisData.load()
        thisData.clean()

        if subjID in seenIDs:
            # making sure there is no duplicate file as this would silently overwrite output from the first file
            raise Exception('Two file names found with the numbers {}. Rename to prevent overwriting.'.format(subjID))
        else:
            seenIDs.append(subjID)
            outputfile = "sub-" + subjID.zfill(5) + "_task-team-post_run01_events.tsv"

        thisData.write(join(snap1outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))