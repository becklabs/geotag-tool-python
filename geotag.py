# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 22:51:39 2020

@author: beck
"""

import videoToolkit as vTk
import trackToolkit as tTk
import os
import pandas as pd
from tqdm import *
import time
import sys
from GPSPhoto import gpsphoto
import dateparser
import argparse

def match(videos=['null'],tracks=['null'],inputPath=False,projectPath=False,autoscan=True,maxTimeDifference=1.0):
    
    #MANAGE PATH
    if inputPath == False:
        inputPath = os.getcwd()+'\\'
    if inputPath[-1] != '/':
        if inputPath[-1] != '\\':
            inputPath = inputPath+'\\'
    #MANAGE CREATE PROJECT
    createProject=False
    if projectPath == False:
        createProject = True
        projectName = 'project'+ time.strftime("%Y%m%d-%H%M%S")
        projectPath = os.getcwd()+'/projects/'+projectName+'/'
        if 'projects' not in os.listdir():
            os.mkdir('projects/')
        if projectName not in os.listdir('projects/'):
            os.mkdir('projects/'+projectName)
        
    #MANAGE AUTOSCAN
    if autoscan == True:
        videos = []
        tracks = []
        for filename in os.listdir(inputPath):
            if 'MP4' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    videos.append(filename)
            if 'gpx' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    tracks.append(filename)
            if 'csv' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    tracks.append(filename)
        inputDF = pd.DataFrame()
        inputDF['Videos'] = videos
        inputDF['Tracks'] = tracks
        if 'input' not in os.listdir(projectPath):
            os.mkdir(projectPath+'input/')
        inputDF.to_csv(projectPath+'input/inputFiles.csv')
    
    #READ DATA INTO DATAFRAMES    
    framesDF = pd.DataFrame()
    pointsDF = pd.DataFrame()
    if createProject == True:
        for video in videos: 
                framesDF = framesDF.append(vTk.getTimestamps(inputPath,video,projectPath,export=True),ignore_index=True)
                vTk.createFrames(inputPath,video,projectPath)
        for track in tracks:
            pointsDF = pointsDF.append(tTk.trackExtract(inputPath,track,projectPath),ignore_index=True)
    else:
            timestampDFs = [x for x in os.listdir(projectPath+'timestamps/') if x.split('.')[-1] == 'csv']
            for x in timestampDFs:
                framesDF = framesDF.append(pd.read_csv(projectPath+'timestamps/'+x),ignore_index=True)
            pointDFs = [x for x in os.listdir(projectPath+'tracks/') if x.split('.')[-1] == 'csv']
            for x in pointDFs:
                pointsDF = pointsDF.append(pd.read_csv(projectPath+'tracks/'+x),ignore_index=True)
            framesDF['Timestamp'] = [dateparser.parse(i) for i in framesDF['Timestamp']]
            pointsDF['timestamp']= [dateparser.parse(i) for i in pointsDF['timestamp']]
    
    #MATCH POINTS TO CLOSEST FRAME OR SET UNDEFINED IF INSUFFICIENT TIME DIFFERENCE
    taggedDF = pointsDF
    i = 0
    for pointTime in tqdm(pointsDF['timestamp'],desc='Matching frames from: '+str(videos)+ ' to points on: '+ str(tracks),unit='frames'):
        timedeltas = [abs((pointTime-frameTime).total_seconds()) for frameTime in framesDF['Timestamp']]
        if min(timedeltas) <= maxTimeDifference:
            closestFrame = framesDF.loc[timedeltas.index(min(timedeltas)), 'Frame']
            taggedDF.loc[i, 'Frame'] = closestFrame
        else:
            taggedDF.loc[i, 'Frame'] = float('nan')
        i += 1
    
    #DROP UNDEFINED POINTS FROM DF
    taggedDF = taggedDF.dropna()
    taggedDF = taggedDF.reset_index(drop=True)
    if 'geotagged frames' not in os.listdir(projectPath):
        os.mkdir(projectPath+'geotagged frames/')
    i = 0
    sys.stdout.flush()
    for frame in tqdm(taggedDF['Frame'],desc='Geotagging '+ str(len(taggedDF['Frame'])) + ' frames to path: geotagged frames/',unit='frames'):
        photo = gpsphoto.GPSPhoto(projectPath+'frames/'+frame)
        info = gpsphoto.GPSInfo((taggedDF.loc[i, 'latitude'], 
                                 taggedDF.loc[i, 'longitude']), 
                                alt=int(taggedDF.loc[i, 'elevation']), 
                                timeStamp=taggedDF.loc[i, 'timestamp'])
        photo.modGPSData(info, projectPath+'geotagged frames/'+ frame)
        i+=1
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input',type=str,default=False,help='Path to look for videos/tracks in')
    parser.add_argument('-p','--project',type=str,default=False,help='Path to project folder')
    parser.add_argument('-m','--maxtimedifference',type=float,default=1.0,help='Max allowed time difference between frame and point')
    args = parser.parse_args()
    match(inputPath = args.input, projectPath = args.project, maxTimeDifference = args.maxtimedifference)

        
