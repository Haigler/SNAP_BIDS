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
        self.stimuli = [HereWeGo(), Sample(), PreStimulus(), Image(), IRI()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'reaction_time', 'reaction_exptime', 'trial_type',
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
        self.trial_type = "HereWeGo"
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
        self.trial_type = "Sample"
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
        self.trial_type = "PreStimulus"
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

class Image:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.reaction_time = None
        self.reaction_exptime = None
        self.trial_type = "Image"
        self.response = None
        self.accuracy = None
        self.group_affiliation = None
        self.team = None
        self.gender = None
        self.race = None
        self.filename = None
        self.photo_group = None
        self.trial = None

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['Stim1.OnsetTime']
        self.durationField = ['Stim1.OffsetTime', 'Stim1.OnsetTime']
        self.reaction_timeField = ['Stim1.RT']
        self.reaction_exptimeField = ['Stim1.RTTime']
        self.responseField = ['Stim1.RESP']
        self.accuracyField = ['Stim1.RESP', 'CorrectAnswer']
        self.group_affiliationField = ['In1_Out2']
        self.teamField = ['Team']
        self.genderField = ['Gender']
        self.raceField = ['Race']
        self.filenameField = ['Image']
        self.photo_groupField = ['PhotoGroup']
        self.trialField = ['Trial']

        self.inputFields = list(set(self.onsetField + self.durationField + self.reaction_timeField \
                                    + self.reaction_exptimeField + self.responseField \
                                    + self.accuracyField + self.group_affiliationField + self.teamField \
                                    + self.genderField + self.raceField + self.filenameField \
                                    + self.photo_groupField + self.trialField))

    def clean(self, rawData, outputFields):
        # extract onset time
        onset = rawData[self.onsetField]
        onset = onset.rename(columns={onset.columns[0]: 'onset'})

        # extract duration
        duration = rawData['Stim1.OffsetTime'] - rawData['Stim1.OnsetTime']
        duration = duration.to_frame('duration')

        # extract reaction time
        reaction_time = rawData[self.reaction_timeField]
        reaction_time = reaction_time.rename(columns={reaction_time.columns[0]: 'reaction_time'})

        # extract reaction experiment time
        reaction_exptime = rawData[self.reaction_exptimeField]
        reaction_exptime = reaction_exptime.rename(columns={reaction_exptime.columns[0]: 'reaction_exptime'})

        # recode values for response
        response = rawData[self.responseField]
        responseRecodeVals = {'p': "CHANGETHIS!!", 'q': "CHANGETHIS!!"}
        response = response.rename(columns={response.columns[0]: 'response'}).replace({'response': responseRecodeVals})

        # calculate accuracy
        correct = response['response'] == rawData['CorrectAnswer']
        accuracy = correct.to_frame('accuracy')
        accuracy = accuracy.where(correct, other="incorrect")
        accuracy = accuracy.where(~correct, other="correct")
        accuracy = accuracy.mask(response['response'].isnull(), other=np.nan)

        # recode values for group affiliation
        group_affiliation = rawData[self.group_affiliationField]
        group_affiliationRecodeVals = {1: "ingroup", 2: "outgroup", 3: "unaffiliated"}
        group_affiliation = group_affiliation.rename(
            columns={group_affiliation.columns[0]: 'group_affiliation'}).replace(
            {'group_affiliation': group_affiliationRecodeVals})

        # extract team membership
        team = rawData[self.teamField]
        team = team.rename(columns={team.columns[0]: 'team'})

        # extract gender
        gender = rawData[self.genderField]
        gender = gender.rename(columns={gender.columns[0]: 'gender'})

        # extract race
        race = rawData[self.raceField]
        race = race.rename(columns={race.columns[0]: 'race'}).replace('', "NA")

        # extract filename
        filename = rawData[self.filenameField]
        filename = filename.rename(columns={filename.columns[0]: 'filename'})

        # recode values for photo group
        photo_group = rawData[self.photo_groupField]
        photo_groupRecodeVals = {'1': "bar", '2': "baz", 'D': "foo"}
        photo_group = photo_group.rename(
            columns={photo_group.columns[0]: 'photo_group'}).replace(
            {'photo_group': photo_groupRecodeVals})

        # extract trial number
        trial = rawData[self.trialField]
        trial = trial.rename(columns={trial.columns[0]: 'trial'})

        data = pandas.concat(
            [onset, duration, reaction_time, reaction_exptime, response, accuracy, group_affiliation,
             team, gender, race, filename, photo_group, trial], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

class IRI:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.reaction_time = np.nan
        self.reaction_exptime = np.nan
        self.trial_type = "IRI"
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
        self.onsetField = ['IRI.OnsetTime']
        self.durationField = ['IRI.Duration']
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