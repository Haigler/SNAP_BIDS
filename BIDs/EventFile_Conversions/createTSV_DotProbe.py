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
        self.stimuli = [Probe()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()

    def __declareReadFields(self):
        readFields = []
        for s in self.stimuli:
            readFields.extend(s.inputFields)
        return readFields

    def __declareWriteFields(self):
        writeFields = ['onset', 'duration', 'reaction_time', 'reaction_scantime', 'response', 'probe_rl', 'word_rl',
                       'congruency', 'word_onset', 'word_duration', 'probe_onset', 'probe_duration',
                       'wordL', 'wordR', 'trial_type', 'trial']
        return writeFields

    def load(self):
        # These try-except blocks have been tailored to the particular data files being parsed in order to accommodate
        # the different encodings that were encountered
        try:
            self.contents = pandas.read_csv(self.dataFile, sep='\t', usecols=self.readFields)
        except:
            try: # if defaults didn't work, try reading with an alternate encoding
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
class Probe:
    def __init__(self):
        self.onset = None
        self.duration = None
        self.reaction_time = None
        self.reaction_scantime = None
        self.response = None
        self.probe_rl = None
        self.word_rl = None
        self.congruency = None
        self.word_onset = None
        self.word_duration = None
        self.probe_onset = None
        self.probe_duration = None
        self.wordL = None
        self.wordR = None
        self.trial_type = None
        self.trial = None

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['Words.OnsetTime', 'GetReady.OnsetTime']
        self.durationField = ['Prb.Duration', 'Words.Duration']
        self.reaction_timeField = ['jitter.RT', 'Prb.RT']
        self.responseField = ['jitter.RESP', 'Prb.RESP']
        self.probe_rlField = ['Probe_RL']
        self.word_rlField = ['Cue_RL']
        self.congruencyField = ['congruent']
        self.word_onsetField = ['Words.OnsetTime', 'GetReady.OnsetTime']
        self.word_durationField = ['Words.Duration']
        self.probe_onsetField = ['Prb.OnsetTime', 'GetReady.OnsetTime']
        self.probe_durationField = ['Prb.Duration']
        self.wordLField = ['word1']
        self.wordRField = ['word2']
        self.trial_typeField = ['trialtype']
        self.trialField = ['Trial']
        self.inputFields = list(set(self.onsetField + self.durationField + self.reaction_timeField \
                                    + self.responseField + self.probe_rlField + self.word_rlField \
                                    + self.congruencyField + self.word_onsetField + self.word_durationField \
                                    + self.probe_onsetField + self.probe_durationField + self.wordLField \
                                    + self.wordRField + self.trial_typeField + self.trialField))

    def error_check(self, dataName, data):
        if dataName == 'response':
            # Verify that no response also has no reaction time and no reaction scan time recorded
            timeNAmatches = (pandas.isna(data['response']) == pandas.isna(data['reaction_time']))
            scanTimeNAmatches = (pandas.isna(data['response']) == pandas.isna(data['reaction_scantime']))
            if not timeNAmatches.all() or not scanTimeNAmatches.all():
                raise Exception('Mismatch in blank entries for response and response timings (RT and/or scan time).')

    def clean(self, rawData, outputFields):
        # combine onset data into one column
        onset = rawData['Words.OnsetTime'] - rawData['GetReady.OnsetTime']
        onset = onset.to_frame('onset')

        # combine duration data into one column
        duration = rawData[self.durationField]
        duration = duration.sum(axis=1, min_count=2).to_frame('duration')

        # calculate reaction time
        # replace missing values in the probe reaction time with any responses made during the jitter
        # if response was made during the jitter, add 500 to account for time elapsed during probe
        reaction_time = rawData[self.reaction_timeField]
        reaction_time['Prb.RT'] = reaction_time['Prb.RT'].replace(0, np.NaN) # no response made during probe
        reaction_time['jitter.RT'] = reaction_time['jitter.RT'] + 500 # 0 during jitter sometimes has a response with it
        reaction_time = reaction_time['Prb.RT'].fillna(reaction_time['jitter.RT']) # replace missing probe with jitter
        response = rawData[self.responseField]
        noRespTrials = response.index[response.isnull().all(1)]  # trials with no response in probe or jitter
        reaction_time.loc[noRespTrials] = np.NaN # filtering out 0 reaction time in jitter when there was no response
        reaction_time = reaction_time.to_frame('reaction_time').astype('Int64')



        # calculate reaction scanner time.
        reaction_scantime = reaction_time.iloc[:, 0] + onset.iloc[:, 0]
        reaction_scantime = reaction_scantime.to_frame('reaction_scantime')

        # replace missing values in the probe response with any responses made during the jitter
        # recode values for response
        response = rawData[self.responseField]
        response = response['Prb.RESP'].fillna(response['jitter.RESP'])
        responseRecodeVals = {2: "right", 7: "left"}
        response = response.to_frame('response').replace({'response': responseRecodeVals})

        self.error_check('response', pandas.concat([response, reaction_time, reaction_scantime], axis=1))

        # recode values for probe location
        probe_rl = rawData[self.probe_rlField]
        probe_rlDecodVals = {"r": "right", "l": "left"}
        probe_rl = probe_rl.rename(columns={probe_rl.columns[0]: 'probe_rl'})
        probe_rl = probe_rl.replace({'probe_rl': probe_rlDecodVals})

        # recode values for cue word location
        word_rl = rawData[self.word_rlField]
        word_rlDecodeVals = {"r": "right", "l": "left"}
        word_rl = word_rl.rename(columns={word_rl.columns[0]: 'word_rl'})
        word_rl = word_rl.replace({'word_rl': word_rlDecodeVals})

        # recode congruency
        congruency = rawData[self.congruencyField]
        congruencyDecodeVals = {"i": "incongruent", "c": "congruent"}
        congruency = congruency.rename(columns={congruency.columns[0]: 'congruency'})
        congruency = congruency.replace({'congruency': congruencyDecodeVals})

        # combine word onset data into one column
        word_onset = rawData['Words.OnsetTime'] - rawData['GetReady.OnsetTime']
        word_onset = word_onset.to_frame('word_onset')

        # extract word duration data
        word_duration = rawData[self.word_durationField]
        word_duration = word_duration.rename(columns={word_duration.columns[0]: 'word_duration'})

        # combine probe onset data into one column
        probe_onset = rawData['Prb.OnsetTime'] - rawData['GetReady.OnsetTime']
        probe_onset = probe_onset.to_frame('probe_onset')

        # extract probe duration data
        probe_duration = rawData[self.probe_durationField]
        probe_duration = probe_duration.rename(columns={probe_duration.columns[0]: 'probe_duration'})

        # extract left word data
        wordL = rawData[self.wordLField]
        wordL = wordL.rename(columns={wordL.columns[0]: 'wordL'})

        # extract right word data
        wordR = rawData[self.wordRField]
        wordR = wordR.rename(columns={wordR.columns[0]: 'wordR'})

        # extract trial type
        trial_type = rawData[self.trial_typeField]
        trial_type = trial_type.rename(columns={trial_type.columns[0]: 'trial_type'})

        # extract trial number
        trial = rawData[self.trialField]
        trial = trial.rename(columns={trial.columns[0]: 'trial'})

        data = pandas.concat([onset, duration, reaction_time, reaction_scantime, response, probe_rl, word_rl,
                              congruency, word_onset, word_duration, probe_onset, probe_duration, wordL, wordR,
                              trial_type, trial], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data


# path to data
basefolder = "/mnt/magaj/SNAP/Data/Task Behavioral Data for BIDS/"
snap1datadir = basefolder + "SNAP 1/Dot Probe (Dot or Star)/"
snap2datadir = basefolder + "SNAP 2/DotProbe (Star or Dot)/"
snap3datadir = basefolder + "SNAP 3/DotProbe (Star or Dot)/"

# getting list of files
snap1files = [f for f in listdir(snap1datadir) if isfile(join(snap1datadir, f))]
snap2files = [f for f in listdir(snap2datadir) if isfile(join(snap2datadir, f))]
snap3files = [f for f in listdir(snap3datadir) if isfile(join(snap3datadir, f))]

# output folder
snap1outdir = basefolder + "Converted Files/SNAP 1/DotProbe/"
snap2outdir = basefolder + "Converted Files/SNAP 2/DotProbe/"
snap3outdir = basefolder + "Converted Files/SNAP 3/DotProbe/"

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
            outputfile = "sub-" + subjID.zfill(5) + "_task-dotprobe_run01.tsv"

        thisData.write(join(snap1outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))

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
            outputfile = "sub-" + subjID.zfill(5) + "_task-dotprobe_run01.tsv"

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
            outputfile = "sub-" + subjID.zfill(5) + "_task-dotprobe_run01.tsv"

        thisData.write(join(snap3outdir, outputfile))
    except:
        raise Exception('Unable to process subject {}'.format(subjID))