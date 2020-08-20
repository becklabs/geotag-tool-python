import videoToolkit as vTk
import trackToolkit as tTk
import os
import pandas as pd
from tqdm import *

def match(videos=['null'],tracks=['null'],path=False,autoscan=True,framesPath=False):
    
    #MANAGE PATH
    if path == False:
        path = os.getcwd()
    
    #MANAGE AUTOSCAN
    if autoscan == True:
        videos = []
        tracks = []
        for filename in os.listdir(path):
            if 'MP4' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    videos.append(filename)
            if 'gpx' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    tracks.append(filename)
            if 'csv' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    tracks.append(filename)
    framesDF = pd.DataFrame()
    pointsDF = pd.DataFrame()
    
    #READ DATA INTO DATAFRAMES
    for video in videos:
        framesDF = framesDF.append(vTk.getTimestamps(path+video,export=False),ignore_index=True)
        if framesPath == False:
            vTk.createFrames(path+video)
    for track in tracks:
        pointsDF = pointsDF.append(tTk.trackExtract(path+track),ignore_index=True)
    
    #MATCH POINTS TO CLOSEST FRAME
    taggedDF = pointsDF
    i = 0
    for pointTime in tqdm(pointsDF['timestamp'],desc='Matching frames from: '+str(videos)+ ' to points on: '+ str(tracks),unit='frames'):
        timedeltas = []
        for frameTime in framesDF['Timestamp']:
            delta = pointTime-frameTime
            timedeltas.append(abs(delta.total_seconds()))
        closestFrame = framesDF.loc[timedeltas.index(min(timedeltas)), 'Frame']
        taggedDF.loc[i, 'Frame'] = closestFrame
        i += 1
    
    #i = 0
    #for frame in concatenate_df['frame']:
        #if i+2<len(concatenate_df['frame']):
            #if concatenate_df.loc[i,'frame'] == concatenate_df.loc[i+2,'frame']:
                #concatenate_df.drop(labels=i,axis=0)
                #i+=1
        #else:
            #break
    return taggedDF

        
