import videoToolkit as vTk
import trackToolkit as tTk
import os
import pandas as pd
from tqdm import *
import time
import sys
from GPSPhoto import gpsphoto
import dateparser
from datetime import datetime

def match(videos=['null'],tracks=['null'],inputPath=False,projectPath=False,autoscan=True,maxTimeDifference=1.0):
    now = datetime.now()
    
    #MANAGE PATH
    if inputPath == False:
        inputPath = os.getcwd()+'\\'
    if projectPath == False:
        projectPath = os.getcwd()+'\\'
    if inputPath[-1] != '/':
        if inputPath[-1] != '\\':
            inputPath = inputPath+'\\'
    if projectPath[-1] != '/':
        if projectPath[-1] != '\\':
            projectPath = projectPath+'\\'
    
    #MANAGE CREATE PROJECT
    createProject = True
    projectName = 'project'+ time.strftime("%d-%b-%Y_%H.%M.%S")
    if 'projects' not in os.listdir(projectPath):
        os.mkdir(projectPath+'projects/')
    if projectName not in os.listdir(projectPath+'projects/'):
        os.mkdir(projectPath+'projects/'+projectName)
    projectPath += '/projects/'+projectName+'/'
    
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
    for pointTime in tqdm(pointsDF['timestamp'],desc='Matching: '+str(videos)+ ' and: '+ str(tracks),unit='frames'):
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
    
    #CREATE FRAMES FROM MP4
    for video in videos:
        vTk.createFrames(inputPath,video,projectPath,taggedDF)
    
    #ADD TELEMETRY TO PHOTOS
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
    print(r'Done (Processing time: '+str(((datetime.now()-now).total_seconds())/len(pointsDF['timestamp'])) + ' seconds per point')


        