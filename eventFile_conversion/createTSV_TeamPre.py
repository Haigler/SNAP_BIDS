# Team Pre TASK
# This script converts the original Team Pre-Task (i.e. Training Task) files that were exported from ePrime to the BIDS compliant tsv format.
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
        self.stimuli = [Image()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'reaction_time', 'reaction_exptime', 'response',
                       'accuracy', 'left_image', 'right_image', 'group_affiliation', 'team',
                       'gender', 'race', 'filename']
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
class Image:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.reaction_time = None
        self.reaction_exptime = None
        self.response = None
        self.accuracy = None
        self.left_image = None
        self.right_image = None
        self.group_affiliation = None
        self.team = None
        self.gender = None
        self.race = None
        self.filename = None

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['Stim.OnsetTime']
        self.durationField = ['Stim.OnsetTime']
        self.reaction_timeField = ['Stim.RT']
        self.reaction_exptimeField = ['Stim.RTTime']
        self.responseField = ['Stim.RESP']
        self.accuracyField = ['Stim.RESP', 'CorrectAnswer']
        self.left_imageField = ['LeftLabel']
        self.right_imageField = ['RightLabel']
        self.group_affiliationField = ['In1_Out2']
        self.teamField = ['Team']
        self.genderField = ['Gender']
        self.raceField = ['Race']
        self.filenameField = ['Image']

        self.inputFields = list(set(self.onsetField + self.durationField + self.reaction_timeField \
                                    + self.reaction_exptimeField + self.responseField \
                                    + self.accuracyField + self.left_imageField \
                                    + self.right_imageField + self.group_affiliationField \
                                    + self.teamField + self.genderField + self.raceField \
                                    + self.filenameField))

    def clean(self, rawData, outputFields):
        # extract onset time
        onset = rawData[self.onsetField]
        onset = onset.rename(columns={onset.columns[0]: 'onset'})

        # calculate duration
        duration = rawData[self.durationField]
        duration = duration.diff()
        duration = duration.reindex(index=np.roll(duration.index, -1)).reset_index(drop=True)
        duration = duration.rename(columns={duration.columns[0]: 'duration'}).astype('Int64')

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

        # recode values for left image
        left_image = rawData[self.left_imageField]
        left_imageRecodeVals = {"image/BlueTeam.png": "blue", "image/RedTeam.png": "red"}
        left_image = left_image.rename(columns={left_image.columns[0]: 'left_image'}).replace({'left_image': left_imageRecodeVals})

        # recode values for right image
        right_image = rawData[self.right_imageField]
        right_imageRecodeVals = {"image/BlueTeam.png": "blue", "image/RedTeam.png": "red"}
        right_image = right_image.rename(columns={right_image.columns[0]: 'right_image'}).replace(
            {'right_image': right_imageRecodeVals})

        # recode values for group affiliation
        group_affiliation = rawData[self.group_affiliationField]
        group_affiliationRecodeVals = {1: "ingroup", 2: "outgroup", 3: "unaffiliated"}
        group_affiliation = group_affiliation.rename(columns={group_affiliation.columns[0]: 'group_affiliation'}).replace(
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

        data = pandas.concat(
            [onset, duration, reaction_time, reaction_exptime, response, accuracy,
             left_image, right_image, group_affiliation, team, gender, race, filename], axis=1)

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
snap1datadir1 = basefolder + "SNAP 1/Team Game/Pre Scan Training/Edat/"
snap1datadir2 = basefolder + "SNAP 1/Team Game/Pre Scan Training/New Edat/"

# output folders
snap1outdir = basefolder + "Converted Files/SNAP 1/Team/Pre Scan Training/"

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
            outputfile = "sub-" + subjID.zfill(5) + "_task-team-pre_run01_events.tsv"

        thisData.write(join(snap1outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))
