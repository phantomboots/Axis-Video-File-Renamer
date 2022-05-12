# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 19:06:43 2021

This script can be used to do a batch renaming process for recordings of standard definition video files recorded from the Phantom ROV's
subsea camera (pilot camere, umbilical camera, forward camera, or others SD camera feeds). These video files are recorded by an AXIS P7304
network video recorder. This device does not allow for a file naming in a manner that is easily interpreted during data review.

An example of the default directory and file format created by the AXIS P7304 is as follows:
    
D:\axis-ACCC8EE207AE\20211020\14\20211020_143325_B4F5_ACCC8EE207AE\20211020_14\20211026_145333_CB36.mvk

This file format does not indicate the camera name, and the nested directory structure makes accessing video files or batch processing
challenging. The script first builds a Path object to contain all directory levels as component parts. There is an .XML file for each 
camera that contains the recording information for a given camera. It is always located in the fourth nested directory level, and is always 
called 'recording.xml'. This script parses the infomration in that .XML file and extracts the recording name.

D:\axis-ACCC8EE207AE\20211020\14\20211020_143325_B4F5_ACCC8EE207AE\recording.xml

Finally, the .mkv files are renamed to the format of 'RecordingName_YYYYMMDD_HHMMSS.mkv', and moved to the root directory (i.e. 
D:\axis-ACCC8EE207AE)

"""

import os
from pathlib import Path
import xml.etree.cElementTree as ET #Library to parse .XML files
import re
import pandas as pd
import time

########################################## EDITS THESE VALUES ########################################################################

#String that stores the project or cruise number, could be of the from PACYYYY-XXX or another designation.

project_name = "AnchorScour"

#Location and name of Dive log file to import.
    
dive_log = pd.read_csv("D:/DiveLogFull.csv")

#Root directory where GoPro video files are stored

top_lvl_dir = Path("D:/SD_Videos")

################################################## INITIAL RENAME AND MOVE FOR SD VIDEO FILES ###############################################


#Empty lists to append directory Path objects into.

sub_dirs = []
lvl_two = []
lvl_three = []
lvl_four = []
recording_names = []
file_names = []

#Drop into second level dir
for dirs in top_lvl_dir.iterdir():
    if(str(dirs.suffix) != ".db"):
       sub_dirs.append(dirs)
    
#Drop into third level dir, get directory listings iteratively
for each in sub_dirs:
    for second in each.iterdir():
      lvl_two.append(second)
           
#Drop in fourth level dir, get directory listings iteratively
for each in lvl_two:
    for third in each.iterdir():
        lvl_three.append(third)
        
        
#Drop into last level sub directory, get listings iteratively
for each in lvl_three:
    for fourth in each.iterdir():
        if fourth.parts[5] != "recording.xml": #By default, this will make a new path object for both files and directories, drop the paths that end in recording.xml
            lvl_four.append(fourth)
                  
        
#Parse .XML files in the lvl_three list object. The 'root' object is the top-level node. root[6] contains the attributes describing the 
#user configured recording parameters in the Axis video recorder, among which is the camera name, listed under child[1] of root[6]

"""
Example .xml file generated by the Axis P7304 encoder, each level is a different level in the .XML tree hiearchy. We are only
interested in the TriggerName here:
    
<?xml version="1.0"?>

-<Recording RecordingToken="20211020_143325_B4F5_ACCC8EE207AE">
        <RecordingGroup> </RecordingGroup>
        <SourceToken>1</SourceToken>
        <StartTime>2021-10-20T14:33:25.145837Z</StartTime>
        <StopTime>2021-10-20T15:48:00.289791Z</StopTime>
        <Content/>
        -<Track TrackToken="Video">
            -<VideoAttributes>
                <Width>720</Width>
                <Height>480</Height>
                <Framerate>30.00000</Framerate>
                <Framerate_fraction>30:1</Framerate_fraction>
                <Encoding>video/x-h264</Encoding>
                <Bitrate>0</Bitrate>
        </VideoAttributes>
    </Track>
    <Application>AxisCamera</Application>
    -<CustomAttributes>
        <TriggerTrigger>Record video while the rule is active</TriggerTrigger>
        <TriggerName>Pilot_Cam_Record</TriggerName>
        <TriggerType>triggered</TriggerType>
    </CustomAttributes>
</Recording>

"""


for i in range(len(lvl_three)):
    try:      
        tree = ET.parse(str(lvl_three[i]) + "/recording.xml")                    
        root = tree.getroot() #Contains all root elements, in the case of the Axis P7304, this goes up to root[6].
    
        #Search for the CustomAtrributes node in the .XML file, then find the TriggerName subnode. Get the text value of this field
        #and append it to the recording_names list.
        attribs = root.findall("CustomAttributes")
        recording = attribs[0].findall("TriggerName")
        recording_names.append(recording[0].text)
    except: 
        recording_names.append("Unknown_Camera")

#The recording_names list and the lvl_three list will have the same number of elements, rename directories by element number
        
    
        
for k in range(0, len(lvl_three)):
    try:
        os.rename(str(lvl_three[k]), str(lvl_three[k].parent) + "\\" + recording_names[k])
    except:
        os.rename(str(lvl_three[k]), str(lvl_three[k].parent) + "\\" + recording_names[k] + "_" + str(k))
    
#Clear the entries from the list of third level directories, as these have just beeen renamed. Get the new lvl three directories list
lvl_three.clear()
for each in lvl_two:
    for third in each.iterdir():
        lvl_three.append(third)
        
#Go into the next level of directories
lvl_four.clear()
for each in lvl_three:
    for fourth in each.iterdir():
        if fourth.suffix != ".xml": #By default, this will make a new path object for both files and directories, drop the paths that end in recording.xml
            lvl_four.append(fourth)       
            
#Get the files names 
for contents in lvl_four:
    for files in contents.iterdir():
        if files.suffix != ".xml":
            file_names.append(files)
        
#Rename the .mkv and .xml files of the actual recordings themselves.
for i in range(len(file_names)):          
    file_stem = re.match("^\\d{8}_\\d{6}", str(file_names[i].stem)) #Match the date and time portions of the file name, but not the four character hex suffix.
    matched_name = file_stem.group()  #Extract the match object as a string. Only one grouping, so don't need to specify it's ID.
    file_suffix = file_names[i].suffix  #Get the file extension.
    file_prefix = file_names[i].parts[4] #Get the recording name
    assembled = file_names[i].parts[4] + "_" + matched_name + file_names[i].suffix #Put all pieces together.
    source_path = str(file_names[i]) 
    dest_path = file_names[i].parts[0] + file_names[i].parts[1] + "\\" + assembled
    os.rename(source_path, dest_path)
    

###################################### EXTRACT SD VIDEO RECORDINGS TIMESTAMPS ############################################

#Empty list to hold GoPro files names, this will be filled using the .iterdir() method on the Path object for the root directory 
#where all the files are stored.

recording_names = []


#Iterate through the contents of the root directory, and append the filenames within this directory to the empty list.
for each in top_lvl_dir.iterdir():
    recording_names.append(each)
    
#Convert the Path objects in the recording_names list to strings, since exiftool cannot work with Path objects.
#in case there are other (non video) files in the directory, exclude them.

recordings = []    
for files in recording_names:
    if(files.suffix == ".mkv"):
        recordings.append(str(files))
        
#Extract the time component of the file timestamps, and convert them to series.

matched = []        
for each in recordings:
    pattern = re.compile("(\d{8}_\d{6})")  
    timestamp = pattern.search(str(each))
    foundtime = timestamp.group()
    convtime = time.strptime(foundtime, "%Y%m%d_%H%M%S")
    string_time = time.strftime("%Y-%m-%d %H:%M:%S", convtime)
    matched.append(string_time) #Extract matched timestamps as a string.

#Generate data frame of file names, and timestamps.
recording_times = pd.DataFrame({"FileName": recordings, "date_time": matched})

#Convert the date_time column to a datetime64 data type.
recording_times["date_time"] = recording_times["date_time"].astype("datetime64[ns]")

#

############################################### CONVERT DATA TYPES IN DIVE LOG DATAFRAME ##################################################
    
#Convert the start and end transect times to datetime64 data types
    
dive_log["Launch"] = dive_log["Launch"].astype("datetime64[ns]")
dive_log["Recovery"] = dive_log["Recovery"].astype("datetime64[ns]")

#Axis P7304 recording are clipped into 5 min files, in this case, need to backtrack the Launch timestamp up to 5 mins
#in the metadata to account for this. 

dive_log["Launch"] = dive_log["Launch"] - pd.Timedelta(minutes=5) #This makes the launch time value 5 mins earlier
    
    
#Convert the time datetime64 time values to integers, for both the dive_log and metadata entries, to facilitate comparisons

dive_log["Launch"] = pd.to_numeric(dive_log["Launch"], errors = "coerce")
dive_log["Recovery"] = pd.to_numeric(dive_log["Recovery"], errors = "coerce")
recording_times["date_time"] = pd.to_numeric(recording_times["date_time"], errors = "coerce")


#################################### MATCH SD VIDEO CREATION TIMES TO DIVE INTERVALS #################################################


#This nested loops looks through all the video files in the metadata_df, for each of these video files it then loops through the dive log 
#Launch and Recovery times, to search for the interval between the Launch and Recovery times that contains the start time of that video
#the corresponding video file recording name (e.g. P10079) is then retrieved from the same row in the dive_log data frame and appended
#into a new column "DiveNumber" in the metadata_df. If no value is found, the entry in the "DiveNumber" column, is left blank.


recording_times["DiveNumber"] = "" #New empty column to fill.

for gp_row, gptimes in recording_times["date_time"].items():
    for index in range(dive_log["Launch"].size):
        if(dive_log["Launch"].at[index] < gptimes < dive_log["Recovery"].at[index]):
            recording_times["DiveNumber"].at[gp_row] = dive_log["Transect_Name"].at[index]
            break

#Rename files outside of these time stamps as "off transect", with a row to number to allow for unique file naming (avoid duplications)
                  
for row, content in recording_times["DiveNumber"].items():
    if(content == ""):
        recording_times["DiveNumber"].at[row] = str("Off_transect_" + str(row))


##################################### RENAME THE SD VIDEO FILES ##################################################################

#Make a new destination path in the recording times dataframe.
    
recording_times["DestPath"] = ""

for timerow, timecontent in recording_times["FileName"].items():
    groups = re.split("\\\\", recording_times["FileName"].at[timerow]) #Have to double escape the two slashed "\\" in the file path.
    dest = str(groups[0] + "/" + groups[1] + "/" + project_name + "_" + recording_times["DiveNumber"].at[timerow] + "_"  + groups[2])
    recording_times["DestPath"].at[timerow] = dest

#Rename the Axis .mkv recordings. The file name generate as the dest_path value will take the form of:
#ProjectName_DiveNumber_YYYYMMDD_HHMMSS.MP4
    
for rows, name in recording_times["FileName"].items():
    source_path = name
    dest_path = recording_times["DestPath"].at[rows]
    os.rename(source_path, dest_path)