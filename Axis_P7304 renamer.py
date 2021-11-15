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

#Read in the root directory

top_lvl_dir = Path("D:/axis-0e35ff78e")

#Empty lists to append directory Path objects into.

sub_dirs = []
lvl_two = []
lvl_three = []
lvl_four = []
recording_names = []
file_names = []

#Drop into second level dir
for dirs in top_lvl_dir.iterdir():
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

for i in range(len(lvl_three)):      
    tree = ET.parse(str(lvl_three[i]) + "/recording.xml")
    root = tree.getroot() #Contains all root elements, in the case of the Axis P7304, this goes up to root[6].

    #Get the camera name, the child[1] of root[6].
    recording = root[6][1].text #The text attribute is the value of this entry.
    recording_names.append(recording)

#The recording_names list and the lvl_three list will have the same number of elements, rename directories by element number
for k in range(len(lvl_three)):
    os.rename(str(lvl_three[k]), str(lvl_three[k].parent) + "\\" + recording_names[k])
    
#Clear the entries from the list of third level directories, as these have just beeen renamed. Get the new lvl three directories list
lvl_three.clear()
for each in lvl_two:
    for third in each.iterdir():
        lvl_three.append(third)
        
#Go into the next level of directories
for each in lvl_three:
    for fourth in each.iterdir():
        if fourth.parts[5] != "recording.xml": #By default, this will make a new path object for both files and directories, drop the paths that end in recording.xml
            lvl_four.append(fourth)       
            
#Get the files names 
for contents in lvl_four:
    for files in contents.iterdir():
        file_names.append(files)
        
#Rename the .mkv and .xml files of the actual recordings themselves.
for i in range(len(file_names)):          
    file_stem = re.match("^\\d{8}_\\d{6}", str(file_names[i].stem)) #Match the date and time portions of the file name, but not the foru characted hex suffix.
    matched_name = file_stem.group()  #Extract the match object as a string. Only one grouping, so don't need to specify it's ID.
    file_suffix = file_names[i].suffix  #Get the file extension.
    file_prefix = file_names[i].parts[4] #Get the recording name
    assembled = file_names[i].parts[4] + "_" + matched_name + file_names[i].suffix #Put all pieces together.
    source_path = str(file_names[i]) 
    dest_path = file_names[i].parts[0] + file_names[i].parts[1] + "\\" + assembled
    os.rename(source_path, dest_path)