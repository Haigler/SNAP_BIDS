# Team TASK
# This script converts the original Team files that were exported from ePrime to the BIDS compliant tsv format.
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
        self.stimuli = [HereWeGo(), Team()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'image_onset', 'image_duration', 'reaction_time',
                       'reaction_scantime', 'trial_type', 'response', 'group_affiliation',
                       'team', 'gender', 'race', 'filename', 'trial', 'block']
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
        self.onset = 0
        self.duration = None
        self.image_onset = np.nan
        self.image_duration = np.nan
        self.reaction_time = np.nan
        self.reaction_scantime = np.nan
        self.trial_type = "HereWeGo"
        self.response = "NA"
        self.group_affiliation = "NA"
        self.team = "NA"
        self.gender = "NA"
        self.race = "NA"
        self.filename = "NA"
        self.trial = "NA"
        self.block = "NA"

        # column headers of the specific data to import for this stimuli
        self.durationField = ['HereWeGo.Duration']
        self.inputFields = self.durationField

    def clean(self, rawData, outputFields):
        # combine duration data into one column
        duration = rawData[self.durationField]
        duration = duration.drop_duplicates().rename(columns={duration.columns[0]: 'duration'}).astype(int)

        data = duration

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data


class Team:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.image_onset = None
        self.image_duration = 3000
        self.reaction_time = None
        self.reaction_scantime = None
        self.trial_type = "Image"
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
        if dataName == 'single_response':
            # Verify that there is at most one response recorded across both the stimuli and jitter period.
            no_response = pandas.isna(data['Stim.RESP']) & pandas.isna(data['Jitter.RESP'])
            exactly1_response = pandas.isna(data['Stim.RESP']) ^ pandas.isna(data['Jitter.RESP'])
            atmost1_response = no_response | exactly1_response
            if not atmost1_response.all():
                raise Exception('Response recorded during both stimuli and jitter. Expecting at most one recorded response.')
        if dataName == 'no_response':
            # Verify that no response also has no reaction time and no reaction scan time recorded
            timeNAmatches = (pandas.isna(data['response']) == pandas.isna(data['reaction_time']))
            scanTimeNAmatches = (pandas.isna(data['response']) == pandas.isna(data['reaction_scantime']))
            if not timeNAmatches.all() or not scanTimeNAmatches.all():
                raise Exception('Mismatch in blank entries for response and response timings (RT and/or scan time).')

    def clean(self, rawData, outputFields):
        # calculate onset time
        onset = rawData['Stim.OnsetTime'] - rawData['HereWeGo.OnsetTime'].iloc[0]
        onset = onset.to_frame('onset')

        # calculate duration
        duration = rawData[self.durationField]
        duration = duration.diff()
        duration = duration.reindex(index=np.roll(duration.index, -1)).reset_index(drop=True)
        duration = duration.rename(columns={duration.columns[0]: 'duration'}).astype('Int64')

        # calculate image onset time
        image_onset = rawData['Stim.OnsetTime'] - rawData['HereWeGo.OnsetTime'].iloc[0]
        image_onset = image_onset.to_frame('image_onset')

        # calculate reaction time
        # replace missing values in the probe reaction time with any responses made during the jitter
        reaction_time = rawData[self.reaction_timeField]
        reaction_time[['Stim.RTTime', 'Jitter.RTTime']] = reaction_time[['Stim.RTTime', 'Jitter.RTTime']].replace(0, np.NaN)  # no response made during probe or jitter
        reaction_time['Stim.RTTime'] = reaction_time['Stim.RTTime'].fillna(reaction_time['Jitter.RTTime'])  # replace missing stim time with jitter
        reaction_time = reaction_time['Stim.RTTime'] - reaction_time['Stim.OnsetTime']
        reaction_time = reaction_time.to_frame('reaction_time').astype('Int64')

        # calculate reaction scan time
        reaction_scantime = rawData['Stim.RTTime'] + rawData['Jitter.RT']
        reaction_scantime = reaction_scantime.replace(0, np.NaN).to_frame('reaction_scantime').astype('Int64')

        # recode values for response
        response = rawData[self.responseField]
        #self.error_check('single_response', response) # disabling so will take first response if two
        response = response['Stim.RESP'].mask(pandas.isna(response['Stim.RESP']), other=response['Jitter.RESP'])
        responseRecodeVals = {1: "Dislike a lot", 2: "Dislike a little", 3: "Like a little", 4: "Like a lot", 5: "CHANGETHIS!!"}
        response = response.to_frame('response').replace({'response': responseRecodeVals})

        self.error_check('no_response', pandas.concat([response, reaction_time, reaction_scantime], axis=1))

        # recode values for group affiliation
        group_affiliation = rawData[self.group_affiliationField]
        group_affiliationRecodeVals = {1: "ingroup", 2: "outgroup", 3: "unaffiliated"}
        group_affiliation = group_affiliation.rename(columns={group_affiliation.columns[0]: 'group_affiliation'}).replace({'group_affiliation': group_affiliationRecodeVals})

        # extract team membership
        team = rawData[self.teamField]
        team = team.rename(columns={team.columns[0]: 'team'})

        # extract gender
        gender = rawData[self.genderField]
        gender = gender.rename(columns={gender.columns[0]: 'gender'})

        # extract race
        race = rawData[self.raceField]
        race = race.rename(columns={race.columns[0]: 'race'})

        # extract filename
        filename = rawData[self.filenameField]
        filename = filename.rename(columns={filename.columns[0]: 'filename'})

        # extract trial
        trial = rawData[self.trialField]
        trial = trial.rename(columns={trial.columns[0]: 'trial'})

        # extract block
        block = rawData[self.blockField]
        block = block.rename(columns={block.columns[0]: 'block'})

        data = pandas.concat([onset, duration, image_onset, reaction_time, reaction_scantime, response, group_affiliation, team, gender, race, filename, trial, block], axis=1)

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
snap1datadir1 = basefolder + "SNAP 1/Team Game/Scan Task/Edat/"
snap1datadir2 = basefolder + "SNAP 1/Team Game/Scan Task/New Edat/"

# output folder
snap1outdir = basefolder + "Converted Files/SNAP 1/Team/Scan Task/"

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
            outputfile = "sub-" + subjID.zfill(5) + "_task-team_run01_events.tsv"

        thisData.write(join(snap1outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))
