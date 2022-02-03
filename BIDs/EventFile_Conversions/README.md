# Event File Conversion Scripts
This is a collection of scripts that were used to convert the event files generated during runs from their original stored format to the BIDS compliant tsv/json format.

## Progress
Below is the current state of the event file conversions.

+ **GoNoGo** -- Ready for tsv review.
+ **DotProbe** -- Ready for code review.
+ **Driving** -- Need to add conversion for practice files.
+ **Emotion** -- Ready for code review.
+ **Feedback** -- Ready for code review.
+ **Team** -- Need to add conversion for pre and post files.
+ **Cyberball** -- Needs pre-code documentation (see the [before code development process](#before-code-development))

## Process
This process includes the following stages.

1. code development
2. code review
3. tsv output review
4. json review
5. organization of tsv/json into the BIDS data hierarchy

### Before Code Development
Note that prior to code development, work began with **1.** a thorough review of the source event files to identify what data to keep, **2.** creation of a flow chart outlining in step-by-step fashion how to convert a file by hand, **3.** creation of an example tsv file from a single subject, **4.** creation of a template json file for each task. These preliminaries represent a substantial amount of upfront work, but is highly recommended to streamline the conversion proccess.

### Before Code Review
To aide code review, the example tsv file was compared to the code-generated tsv file for that same subject and differences highlighted.


