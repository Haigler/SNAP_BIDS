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
        self.stimuli = [HereWeGo(), Rest(), Decision(), Throw()]
        self.readFields = self.__declareReadFields()
        self.writeFields = self.__declareWriteFields()
        self.qc_flags = {
            'ghost_decisions': False,
            'ghost_throws': False,
            'out_of_sequence_throws': False,
        } # These are meant to flag unexpected patterns noticed during visual inspection of data

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

        # convert units from millisecond to seconds
        cols = ['onset', 'duration', 'reaction_time', 'reaction_scantime']
        cleanedData[cols] = cleanedData[cols].apply(pandas.to_numeric, errors='coerce') # to make numeric manipulation easier
        cleanedData[cols] = (cleanedData[cols] / 1000).round(3)

        # sort by onset time
        # note that SNAP 2, sub-01008 is missing onset time for one throw. this will go to the bottom
        cleanedData.sort_values(by='onset', inplace=True)

        # adjust so start of data collection (onset = 0) is synced to the first HereWeGo.
        match = cleanedData.loc[cleanedData['trial_type'] == 'HereWeGo', 'onset']
        cleanedData[['onset', 'reaction_scantime']] -= match.iloc[0]

        # remove "ghost" events in the data that are likely artifacts and never shown to subject
        # resets row index for iteration
        cleanedData = self.__removeGhostEvents(cleanedData)

        # determine values for 'clusivity' column
        cleanedData = self.__addClusivity(cleanedData)

        # Assign Decision trials to the following block number.
        mask = (
                (cleanedData['trial_type'] == 'Decision') &
                (cleanedData['block'].shift(-1) != 'n/a')
        )

        cleanedData.loc[mask, 'block'] = cleanedData['block'].shift(-1)

        # Change a Decision trial to a WaitForThrow trial. this should exclusively be the first
        # stimuli after HereWeGo in the inclusion round, when the ball starts with another player.
        mask = (
                (cleanedData['trial_type'] == 'Decision') &
                (cleanedData['response'] == 'n/a') &
                (cleanedData['trial_type'].shift(-1) == 'Throw') &
                (cleanedData['thrower'].shift(-1) != 'subject')
        )

        cleanedData.loc[mask, 'trial_type'] = 'WaitForThrow'

        self.contents = cleanedData

    def __removeGhostEvents(self, data):
        data = data.reset_index(drop=True)

        decision_ghost = (
                (data["trial_type"] == "Decision")
                & data["response"].isna()
                & (data["reaction_time"] == 0)
                & (data["reaction_scantime"] < 0)
        )

        # A single-element list (e.g., "['1to3.1.bmp']") starts with
        # '[' and contains no commas.
        single_file =(data["filenames"].str.startswith("[")
                       & ~data["filenames"].str.contains(",", regex=False))
        single_dur = (data["image_durations"].str.startswith("[")
                      & ~data["image_durations"].str.contains(",", regex=False))

        throw_ghost = (
                (data["trial_type"] == "Throw")
                & single_file
                & single_dur
        )

        if decision_ghost.any():
            self.qc_flags['ghost_decisions'] = True
        if throw_ghost.any():
            self.qc_flags['ghost_throws'] = True

        ghosts = decision_ghost | throw_ghost

        data = data[~ghosts].reset_index(drop=True)

        # validate throw continuity within rounds (rounds demarcated by 'Rest' and 'HereWeGo'
        self.__validateThrowSequences(data)

        return data

    def __validateThrowSequences(self, data):
        is_boundary = data['trial_type'].isin(['Rest', 'HereWeGo'])
        round_id = is_boundary.cumsum()

        is_throw = data["trial_type"] == "Throw"
        assert is_throw.any(), "No throws detected."

        throws = data.loc[is_throw, ["onset", "thrower", "catcher", "block"]].copy()
        throws["_round"] = round_id[is_throw].values

        # split throws into their separate rounds (should be continuous sequence within rounds)
        rounds = [grp for _, grp in throws.groupby("_round")]

        for rnd in rounds:
            mismatches = (rnd["thrower"] != rnd["catcher"].shift()).iloc[1:]
            if len(rnd) < 2 or mismatches.any():
                self.qc_flags['out_of_sequence_throws'] = True

    def __addClusivity(self, data):
        data = data.reset_index(drop=True) # don't count on this being done before now.

        # mark throw events
        throws = pandas.Series(0, index=range(len(data.index)))
        throws[data['trial_type'] == 'Throw'] = 1

        # find and count all consecutive throws
        t = throws.diff().ne(0) # mark start of groupings of consecutive throw/non-throw events
        tgrp = t.cumsum() # assign a group number for each grouping
        cnt = throws.groupby(tgrp).cumcount() # use group number to count events within groups
        consecthrow = throws * (cnt + 1) # zero out non-throw counts

        # find consecutive throws meeting criteria for exclusion
        gt5 = consecthrow > 5 # exclusion is defined as >5 consecutive throw events
        gt5startIndx = list(consecthrow.index[consecthrow == 6]) # find where consecutive throws become >5

        # mark all throws belonging to an exclusion group of throws then use to find inclusion throws.
        startIndx = [x-5 for x in gt5startIndx] # start of exclusion throws
        indxlists = [list(range(start, end)) for (start, end) in zip(startIndx, gt5startIndx)]
        first_exclthrows = [item for sublist in indxlists for item in sublist]  # flattening list of lists
        exclusionthrow = gt5
        exclusionthrow[first_exclthrows] = True
        inclusionthrow = (data['trial_type'] == 'Throw') & ~exclusionthrow

        # updating clusivity
        data.loc[exclusionthrow, 'clusivity'] = 'exclusion'
        data.loc[inclusionthrow, 'clusivity'] = 'inclusion'

        return data

    def write(self, outputfile):
        if self.contents is not None:
            self.contents.to_csv(outputfile, sep='\t', float_format='%.3f', na_rep='n/a', index=False)

# specific types of stimuli in the task
class HereWeGo:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = None
        self.trial_type = 'HereWeGo'
        self.response = 'n/a'
        self.reaction_time = np.nan
        self.reaction_scantime = np.nan
        self.thrower = 'n/a'
        self.catcher = 'n/a'
        self.clusivity = 'n/a'
        self.block = 'n/a'
        self.throw_pattern = 'n/a'
        self.image_number = 'n/a'
        self.filenames = 'n/a'
        self.image_durations = 'n/a'

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['getready1.OnsetTime', 'getready2.OnsetTime']
        self.durationField = ['getready1.OnsetTime', 'getready1.OffsetTime',
                              'getready2.OnsetTime', 'getready2.OffsetTime']
        self.inputFields = list(set(self.onsetField + self.durationField))

    def clean(self, rawData, outputFields):
        # extract onset time
        try:
            onset = rawData[self.onsetField].iloc[0]
            onset = [onset['getready1.OnsetTime'], onset['getready2.OnsetTime']]
        except KeyError:
            # SNAP 2, sub-14047_run-2 is missing the second HereWeGo stimuli
            onset = [rawData['getready1.OnsetTime'].iloc[0]]

        onset = pandas.DataFrame(onset, columns=['onset'], dtype=int)

        # extract duration
        try:
            duration = rawData[self.durationField].iloc[0]
            herewego1_duration = duration['getready1.OffsetTime'] - duration['getready1.OnsetTime']
            herewego2_duration = duration['getready2.OffsetTime'] - duration['getready2.OnsetTime']
            duration = [herewego1_duration, herewego2_duration]
        except KeyError:
            # SNAP 2, sub-14047_run-2 missing second HereWeGo.
            herewego1_offset = rawData['getready1.OffsetTime'].iloc[0]
            herewego1_onset = rawData['getready1.OnsetTime'].iloc[0]
            duration = [herewego1_offset - herewego1_onset]

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
        self.trial_type = 'Rest'
        self.response = 'n/a'
        self.reaction_time = np.nan
        self.reaction_scantime = np.nan
        self.thrower = 'n/a'
        self.catcher = 'n/a'
        self.clusivity = 'n/a'
        self.block = 'n/a'
        self.throw_pattern = 'n/a'
        self.image_number = 'n/a'
        self.filenames = 'n/a'
        self.image_durations = 'n/a'

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['rest1.OnsetTime', 'rest2.OnsetTime', 'rest4.OnsetTime']
        self.durationField = ['rest1.OnsetTime', 'rest1.OffsetTime',
                              'rest2.OnsetTime', 'rest2.OffsetTime',
                              'rest4.OnsetTime', 'rest4.OffsetTime']
        self.inputFields = list(set(self.onsetField + self.durationField))

    def clean(self, rawData, outputFields):
        # extract onset time
        try:
            onset = rawData[self.onsetField].iloc[0]
            onset = [onset['rest1.OnsetTime'], onset['rest2.OnsetTime'], onset['rest4.OnsetTime']]
        except KeyError:
            # SNAP 2, sub-14047_run-2 is missing the second Rest stimuli
            try:
                remainingFields = [s for s in self.onsetField if s != 'rest2.OnsetTime']
                onset = rawData[remainingFields].iloc[0]
                onset = [onset['rest1.OnsetTime'], onset['rest4.OnsetTime']]
            except KeyError:
                # SNAP 2, sub-14047_run-1 and SNAP 3, sub-02007_run-1 are missing the last Rest stimuli
                remainingFields = [s for s in self.onsetField if s != 'rest4.OnsetTime']
                onset = rawData[remainingFields].iloc[0]
                onset = [onset['rest1.OnsetTime'], onset['rest2.OnsetTime']]

        onset = pandas.DataFrame(onset, columns=['onset'], dtype=int)

        # extract duration
        try:
            duration = rawData[self.durationField].iloc[0]
            rest1_duration = duration['rest1.OffsetTime'] - duration['rest1.OnsetTime']
            rest2_duration = duration['rest2.OffsetTime'] - duration['rest2.OnsetTime']
            rest4_duration = duration['rest4.OffsetTime'] - duration['rest4.OnsetTime']
            duration = [rest1_duration, rest2_duration, rest4_duration]
        except KeyError:
            # sub-14047_run-2 missing second Rest.
            try:
                to_remove = ['rest2.OffsetTime', 'rest2.OnsetTime']
                remainingFields = [f for f in self.durationField if f not in to_remove]
                duration = rawData[remainingFields].iloc[0]
                rest1_duration = duration['rest1.OffsetTime'] - duration['rest1.OnsetTime']
                rest4_duration = duration['rest4.OffsetTime'] - duration['rest4.OnsetTime']
                duration = [rest1_duration, rest4_duration]
            except KeyError:
                # sub-14047_run-1 and SNAP 3, sub-02007_run-1 are missing the last Rest.
                to_remove = ['rest4.OffsetTime', 'rest4.OnsetTime']
                remainingFields = [f for f in self.durationField if f not in to_remove]
                duration = rawData[remainingFields].iloc[0]
                rest1_duration = duration['rest1.OffsetTime'] - duration['rest1.OnsetTime']
                rest2_duration = duration['rest2.OffsetTime'] - duration['rest2.OnsetTime']
                duration = [rest1_duration, rest2_duration]

        duration = pandas.DataFrame(duration, columns=['duration'], dtype=int)

        data = pandas.concat([onset, duration], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

class Decision:
    def __init__(self):
        # hard coded values are the same across all subjects and trials
        # None values need to be calculated for each trial/subject from the subject file
        self.onset = None
        self.duration = None
        self.trial_type = 'Decision'
        self.response = None
        self.reaction_time = None
        self.reaction_scantime = None
        self.thrower = 'n/a'
        self.catcher = 'n/a'
        self.clusivity = 'inclusion'
        self.block = 'n/a'
        self.throw_pattern = 'n/a'
        self.image_number = None
        self.filenames = 'n/a'
        self.image_durations = 'n/a'

        # column headers of the specific data to import for this stimuli
        # some fields may have variable number of headers, so use regex to match multiple headers
        self.onsetField = [r'ImageDisplay\d+.OnsetTime']
        self.durationField = [r'ImageDisplay\d+.OnsetTime', r'ImageDisplay\d+.OffsetTime']
        self.responseField = [r'ImageDisplay\d+.RESP']
        self.reaction_timeField = [r'ImageDisplay\d+.RT']
        self.reaction_scantimeField = [r'ImageDisplay\d+.RTTime']
        self.image_numberField = [r'ImageDisplay\d+.OnsetTime']
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
            except KeyError:
                response.append('n/a')
                reaction_time.append(np.nan)
                reaction_scantime.append(np.nan)

            image_number.append(int(headerID))

        onset = pandas.DataFrame(onset, columns=['onset'], dtype=int)
        duration = pandas.DataFrame(duration, columns=['duration'], dtype=int)

        # recode response
        response = pandas.DataFrame(response, columns=['response'], dtype=str)
        responseRecodeVals = {'2': 'right', '7': 'left', 'nan': 'n/a'}
        response = response.replace({'response': responseRecodeVals})

        no_response = (response['response'] == 'n/a')
        reaction_time = pandas.DataFrame(reaction_time, columns=['reaction_time'], dtype=pandas.Int64Dtype())
        reaction_time[no_response] = np.nan
        reaction_scantime = pandas.DataFrame(reaction_scantime, columns=['reaction_scantime'], dtype=pandas.Int64Dtype())
        reaction_scantime[no_response] = np.nan

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
        self.trial_type = 'Throw'
        self.response = 'n/a'
        self.reaction_time = np.nan
        self.reaction_scantime = np.nan
        self.thrower = None
        self.catcher = None
        self.clusivity = 'n/a' # note that this will be assigned after all data sorted by onset
        self.block = None
        self.throw_pattern = None
        self.image_number = 'n/a'
        self.filenames = None
        self.image_durations = None

        # column headers of the specific data to import for this stimuli
        self.onsetField = ['MyImageDisplay.OnsetTime']
        self.offsetField = ['MyImageDisplay.OffsetTime']
        self.durationField = ['MyImageDisplay.OnsetTime', 'MyImageDisplay.OffsetTime']
        self.throwerField = ['filename']
        self.catcherField = ['filename']
        self.blockField = ['Block']
        self.throw_patternField = [r'Running\[Block\]|RunningBlock']
        self.filenamesField = ['filename']
        self.image_durationsField = ['MyImageDisplay.OnsetTime', 'MyImageDisplay.OffsetTime']
        self.inputFields = list(set(self.onsetField + self.offsetField + self.durationField
                                    + self.throwerField + self.catcherField + self.blockField
                                    + self.throw_patternField + self.filenamesField + self.image_durationsField))

    def clean(self, rawData, outputFields):
        # data for all throw events are within the same columns
        # must parse filenames column to identify individual events
        names = rawData['filename'].str.replace(r'\.\d\.bmp', '', regex=True)
        eventStart = (names != names.shift(periods=1))
        eventEnd = (names != names.shift(periods=-1))

        # extract onsets
        onset = rawData[self.onsetField].loc[eventStart]
        onset = onset.rename(columns={onset.columns[0]: 'onset'}).reset_index(drop=True)

        # calculate duration
        offset = rawData[self.offsetField].loc[eventEnd]
        offset = offset.rename(columns={offset.columns[0]: 'offset'}).reset_index(drop=True)
        duration = offset['offset'] - onset['onset']
        duration = duration.to_frame('duration').astype('Int64')

        # ensure we have an end for every start and we're not misgrouping
        assert (
            len(eventStart[eventStart]) == len(eventEnd[eventEnd])
            and onset['onset'].dropna().is_monotonic_increasing
            and offset['offset'].dropna().is_monotonic_increasing
            ), (
                f'[ClassName: {self.__class__.__name__}] Data Integrity Error: '
                'Mismatch between event starts/ends or unsorted onsets/offsets. '
                'Check if rawData is sorted or contains gaps.'
            )

        # extract thrower and recode
        thrower = rawData['filename'].loc[eventStart]
        thrower = thrower.str.replace(r'to\d\.\d\.bmp', '', regex=True)
        thrower = thrower.reset_index(drop=True).to_frame('thrower')
        throwerRecodeVals = {'1': 'player1', '2': 'subject', '3': 'player3'}
        thrower = thrower.replace({'thrower': throwerRecodeVals})

        # extract catcher and recode
        catcher = rawData['filename'].loc[eventStart]
        catcher = catcher.str.replace(r'\dto', '', regex=True).str.replace(r'\.\d\.bmp', '', regex=True)
        catcher = catcher.reset_index(drop=True).to_frame('catcher')
        catcherRecodeVals = {'1': 'player1', '2': 'subject', '3': 'player3'}
        catcher = catcher.replace({'catcher': catcherRecodeVals})

        # extract block
        block = rawData[self.blockField].loc[eventStart]
        block = block.reset_index(drop=True).rename(columns={block.columns[0]: 'block'}).astype(int)

        # extract throw pattern
        # note that across subjects raw data uses different naming conventions for this header
        throw_pattern = rawData.filter(regex=self.throw_patternField[0]).loc[eventStart]
        throw_pattern = throw_pattern.replace('throw', '', regex=True)
        throw_pattern = throw_pattern.reset_index(drop=True).rename(columns={throw_pattern.columns[0]: 'throw_pattern'}).astype(str)

        # Collect all filenames and image durations for each throw event into single entries.
        filenames = []
        image_durations = []
        imgdurs = rawData['MyImageDisplay.OffsetTime'] - rawData['MyImageDisplay.OnsetTime']
        imgdurs = imgdurs/1000 # convert from millisecond to seconds
        for i, (fname, imgdur) in enumerate(zip(rawData['filename'], imgdurs)):
            # some values missing in SNAP 2 data (last throw in sub-01008 specifically)
            if pandas.isnull(fname): fname = 'n/a'
            if pandas.isnull(imgdur): imgdur = 'n/a'

            if eventStart[i]:
                if eventEnd[i]:  # for single image throw events where the start is also the end
                    filenames.append('[\'' + fname + '\']')
                    image_durations.append('[' + str(imgdur) + ']')
                else:
                    filestr = '[\'' + fname + '\', '
                    durstr = '[' + str(imgdur) + ', '
            elif eventEnd[i]:
                filenames.append(filestr + '\'' + fname + '\']')
                image_durations.append(durstr + str(imgdur) + ']')
            else:
                filestr = filestr + '\'' + fname + '\', '
                durstr = durstr + str(imgdur) + ', '

        filenames = pandas.DataFrame(filenames, columns=['filenames'], dtype=str)
        image_durations = pandas.DataFrame(image_durations, columns=['image_durations'], dtype=str)

        data = pandas.concat([onset, duration, thrower, catcher, block,
                              throw_pattern, filenames, image_durations], axis=1)

        # create columns for each field with the values set at initialization
        # (this may not be used in certain versions of this script)
        for attrName in outputFields:
            attr = getattr(self, attrName)
            if attr is not None:
                data[attrName] = attr

        return data

# path to data
basefolder = '/g/Imaging/SNAP/Data/Task Behavioral Data for BIDS/'
snap1datadir = basefolder + 'SNAP 1/Cyberball (Catch)/'
snap2datadir = basefolder + 'SNAP 2/Cyberball (Catch)/'
snap3datadir = basefolder + 'SNAP 3/Cyberball (Catch)/'
snapdatadir = [snap1datadir, snap2datadir, snap3datadir]

# getting list of files
snap1files = [f for f in listdir(snap1datadir) if isfile(join(snap1datadir, f))]
snap2files = [f for f in listdir(snap2datadir) if isfile(join(snap2datadir, f))]
snap3files = [f for f in listdir(snap3datadir) if isfile(join(snap3datadir, f))]
snapfiles = [snap1files, snap2files, snap3files]

# output folder
snap1outdir = basefolder + 'Converted Files/SNAP 1/Cyberball/'
snap2outdir = basefolder + 'Converted Files/SNAP 2/Cyberball/'
snap3outdir = basefolder + 'Converted Files/SNAP 3/Cyberball/'
snapoutdir = [snap1outdir, snap2outdir, snap3outdir]

VERBOSE = False # Toggle printing some logging info about malformed data to stdout.

# read, clean, and write data
seenIDs = []
for datadir, files, outdir in zip(snapdatadir, snapfiles, snapoutdir):
    files_with_throw_ghosts = 0 # tracking a problem that seems pervasive (see QC document)
    for datafilename in files:
        thisData = Data(join(datadir, datafilename))

        # create the output file name
        # - A handful of subjects have scans that were rerun for various reasons.
        # - These have the string run-01, run-02, etc. added to the event files
        # - to distinguish which file belongs to which run.
        pattern = r'run-(\d+)'
        match = re.search(pattern, datafilename)
        runID = match.group(1) if match else '1'

        # extract ID from whatever numbers are left after removing run.
        strippedName = re.sub(pattern, "", datafilename)
        subjID = str(''.join(filter(str.isdigit, strippedName)))

        outputfile = ('sub-' + subjID.zfill(5) + '_task-cyberball_run-'
                                                + runID + '_events.tsv')

        try:
            thisData.load()
            thisData.clean()

            if VERBOSE:
                # tracking some quality control info about malformed data.
                if thisData.qc_flags['ghost_throws']:
                    files_with_throw_ghosts += 1
                if thisData.qc_flags['ghost_decisions']:
                    print(f'Malformed Data: sub-{subjID} run-{runID}: ghost decisions')
                if thisData.qc_flags['out_of_sequence_throws']:
                    print(f'Malformed Data: sub-{subjID} run-{runID}: out of sequence throws')

                # checking if previous onset+duration is falling far short of the recorded onset of the next event
                expected = thisData.contents['onset'].shift() + thisData.contents['duration'].shift()
                if ((thisData.contents['onset'] - expected).abs() > 1).iloc[1:].any():
                    print(f'  WARNING: sub-{subjID} run-{runID}: onset gap > 1s detected')

            if subjID + runID in seenIDs:
                # making sure there is no duplicate file as this would silently overwrite output from the first file
                raise Exception('Two file names found with the numbers {}. Rename to prevent overwriting.'.format(subjID))
            else:
                seenIDs.append(subjID + runID)

            thisData.write(join(outdir, outputfile))
        except:
            raise Exception(f'Unable to process subject {subjID}, run {runID}')

    if VERBOSE:
        # printing some QC info about malformed data
        if files_with_throw_ghosts == len(files):
            print(f'All files in {datadir} contained ghost throw events.')