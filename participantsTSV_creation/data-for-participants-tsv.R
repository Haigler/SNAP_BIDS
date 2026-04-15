library(haven)
library(dplyr)
##
## Creates the participants.tsv files for each data set from the original spss file.
##    You should only need to change the paths/file names at the top to make this work.
##    You will need to strip the "SNAP1", "SNAP2", "SNAP3" off the tsv file names to 
##    make them BIDS-compliant.
##
##    Run the ## DATA ## section to extract the data and write to file.
##      To add additional variables, add them to the select() and rename() parameters.
##
##    Run the ## DIAGNOSTICS ## section to print the SPSS variable names, labels, and 
##    label values to file for easier searching.
##      The labels and values were used to construct the participants.json
##

# input
workdir <- "/path/to/working/directory/"
spssfile <- "./rawdata/MergedSHARE+SNAP123.sav"     # should point to whichever source you are using
# output
varlabel.csvfile <- "./derivatives/spss_variable_labels.csv"
SNAP.1.tsvfile <- "./derivatives/participants_SNAP1.tsv"
SNAP.2.tsvfile <- "./derivatives/participants_SNAP2.tsv"
SNAP.3.tsvfile <- "./derivatives/participants_SNAP3.tsv"

setwd(workdir)

##----------------------------------------------------------------
## DATA - Load data and pull out SNAP participants
##----------------------------------------------------------------

fulldata = read_sav(spssfile)

# These are all the subject IDs from the nueroimaging portion of the study.
SNAP.1.ID = c(01003, 01012, 01024, 02020, 02022, 02060, 03003, 04007, 04020, 
              04021, 04032, 04037, 04038, 04043, 04056, 05007, 05027, 06009, 
              06017, 06022, 06029, 06032, 06041, 06049, 06066, 06073, 06081, 
              06086, 06095, 06116, 06120, 06129, 06143, 07011, 07012, 07015, 
              07021, 07027, 07033, 07038, 07054, 11027, 11030, 11036, 11041, 
              12018, 12052, 14013, 14045, 14071)

SNAP.2.ID = c(01008, 01026, 02014, 02025, 02046, 02050, 02053, 03011, 03012, 
              03029, 03030, 04024, 05022, 05025, 06008, 06046, 06070, 06078, 
              06088, 06111, 06123, 06126, 06128, 06163, 07007, 07013, 07039, 
              11023, 11050, 12007, 12022, 12026, 12062, 13002, 14028, 14038, 
              14041, 14047, 14069, 14078)  

SNAP.3.ID = c(01025, 01034, 01047, 01051, 01053, 01059, 01077, 01083, 01086, 
              01093, 01112, 01117, 01119, 01122, 01125, 01127, 01137, 01155, 
              01173, 01181, 01188, 01196, 01197, 01198, 01199, 01202, 01203, 
              01223, 01234, 02001, 02002, 02007, 02013, 02018, 02037, 02041, 
              02043, 02047, 02049, 02058, 02059, 02069, 02072, 02076, 02083, 
              02086, 02096, 02105, 02106, 02138, 02159)

SNAP.ID = c(SNAP.1.ID, SNAP.2.ID, SNAP.3.ID)

SNAP.data   = fulldata[fulldata$id %in% SNAP.ID, ]
SNAP.1.data = fulldata[fulldata$id %in% SNAP.1.ID, ]
SNAP.2.data = fulldata[fulldata$id %in% SNAP.2.ID, ]
SNAP.3.data = fulldata[fulldata$id %in% SNAP.3.ID, ]

participants <- SNAP.data %>%
  select(id, t1SNage, 
         mt1SNsmfq, mt2SNsmfq, mt3SNsmfq, mt4SNsmfq, mt5SNsmfq, 
         mt1SNvictim, mt1SNvictim, mt1SNphysicalvic, mt1SNverbalvic, mt1SNrelationvic, mt1SNcybervic) %>%
  rename(
    participant_id = id,           # participant ID
    age            = t1SNage,      # age at scan day
    depression_t0  = mt1SNsmfq,    # depression at scan day
    depression_t1  = mt2SNsmfq,    # depression 3-month follow-up
    depression_t2  = mt3SNsmfq,    # depression 6-month follow-up
    depression_t3  = mt4SNsmfq,    # depression 9-month follow-up
    depression_t4  = mt5SNsmfq,    # depression 12-month follow-up
    victimization_overall_T0    = mt1SNvictim,       # overall victimization at scan day
    victimization_overt_T0      = mt1SNvictim,       # physical and verbal victimization at scan day
    victimization_physical_T0   = mt1SNphysicalvic,  # physical victimization at scan day
    victimization_verbal_T0     = mt1SNverbalvic,    # verbal victimization at scan day
    victimization_relational_T0 = mt1SNrelationvic,  # relational victimization at scan day
    victimization_cyber_T0      = mt1SNcybervic     # cyber victimization at scan day
  ) %>%
  mutate(
    participant_id = sprintf("sub-%05d", participant_id),
    age            = round(age, 2)
  )

participants.SNAP1 <- participants %>% filter(participant_id %in% sprintf("sub-%05d", SNAP.1.ID))
participants.SNAP2 <- participants %>% filter(participant_id %in% sprintf("sub-%05d", SNAP.2.ID))
participants.SNAP3 <- participants %>% filter(participant_id %in% sprintf("sub-%05d", SNAP.3.ID))

write.table(participants.SNAP1, SNAP.1.tsvfile, sep = "\t", row.names = FALSE, quote = FALSE, na = "n/a")
write.table(participants.SNAP2, SNAP.2.tsvfile, sep = "\t", row.names = FALSE, quote = FALSE, na = "n/a")
write.table(participants.SNAP3, SNAP.3.tsvfile, sep = "\t", row.names = FALSE, quote = FALSE, na = "n/a")

##----------------------------------------------------------------
## DAIAGNOSTICS - Print variable labels to search more easily
##----------------------------------------------------------------

# Extract variable labels and value labels for every column
var_labels <- sapply(SNAP.data, function(x) {
  lab <- attr(x, "label")
  if (is.null(lab)) NA_character_
  else paste(lab, collapse = "; ")
}, USE.NAMES = FALSE)

val_labels <- sapply(SNAP.data, function(x) {
  labs <- attr(x, "labels")
  if (is.null(labs)) NA_character_
  else paste(names(labs), labs, sep = " = ", collapse = "; ")
}, USE.NAMES = FALSE)

# Combine into a data frame
label_df <- data.frame(
  variable     = names(var_labels),
  label        = unlist(var_labels),
  value_labels = unlist(val_labels),
  stringsAsFactors = FALSE
)

# Write to CSV
write.csv(label_df, varlabel.csvfile, row.names = FALSE)
