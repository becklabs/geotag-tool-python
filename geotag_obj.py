import os
from ttk import *
from vtk import *
import datetime
import pandas as pd
import dill
from tqdm import tqdm
from GPSPhoto import gpsphoto

class Project:
    def __init__(self):
        pass
    def create_project(self,videos=[],tracks=[],inputPath=False, projectPath=False, autoscan=True):
        #MANAGE PATH
        if inputPath != False:
            if inputPath[-1] != '/':
                if inputPath[-1] != '\\':
                    inputPath = inputPath+'\\'
                    
        #MANAGE CREATE PROJECT
        time = datetime.datetime.now()
        projectName = 'project'+ time.strftime('%Y-%m-%d_%H%M%S')
        self.projectName = projectName
        if 'projects' not in os.listdir(projectPath):
            os.mkdir(projectPath+'/projects/')
        if projectName not in os.listdir(projectPath+'/projects/'):
            os.mkdir(projectPath+'/projects/'+projectName+'/')
        projectPath += '/projects/'+projectName+'/'
        self.projectPath = projectPath
        self.inputPath = inputPath
        
        #MANAGE AUTOSCAN
        if autoscan == True:
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
        self.videos = videos
        self.tracks = tracks
        
        #READ DATA INTO DATAFRAMES    
        framesDF = pd.DataFrame()
        pointsDF = pd.DataFrame()
        for video in videos: 
            framesDF = framesDF.append(getTimestamps(inputPath,video),ignore_index=True)
        for track in tracks:
            pointsDF = pointsDF.append(trackExtract(inputPath,track),ignore_index=True)
        self.framesDF = framesDF
        self.pointsDF = pointsDF
        
    def match(self, maxtimediff = 1.0, timeoffset=False):
        if timeoffset == False:
            timeoffset = 0
        self.framesDF['adjTimestamp'] = [i+datetime.timedelta(hours=timeoffset) for i in self.framesDF['Timestamp']]
        #MATCH POINTS TO CLOSEST FRAME OR SET UNDEFINED IF INSUFFICIENT TIME DIFFERENCE
        taggedDF = self.pointsDF
        i = 0
        for pointTime in tqdm(self.pointsDF['timestamp'],desc='Matching: '+str(self.videos)+ ' and: '+ str(self.tracks),unit='points'):
            timedeltas = [abs((pointTime-frameTime).total_seconds()) for frameTime in self.framesDF['adjTimestamp']]
            if min(timedeltas) <= maxtimediff:
                closestFrame = self.framesDF.loc[timedeltas.index(min(timedeltas)), 'Frame']
                taggedDF.loc[i, 'Frame'] = closestFrame
            else:
                taggedDF.loc[i, 'Frame'] = float('nan')
            i += 1
        
        #DROP UNDEFINED POINTS FROM DF
        taggedDF = taggedDF.dropna()
        taggedDF = taggedDF.reset_index(drop=True)
        self.taggedDF = taggedDF
    
    def export(self):
        for video in self.videos:
            createFrames(self.inputPath,video,self.projectPath,self.taggedDF)
    
        #ADD TELEMETRY TO PHOTOS
        if 'geotagged_frames' not in os.listdir(self.projectPath):
            os.mkdir(self.projectPath+'geotagged_frames/')
        i = 0
        for frame in self.taggedDF['Frame']:
            photo = gpsphoto.GPSPhoto(self.projectPath+'frames/'+frame)
            info = gpsphoto.GPSInfo((self.taggedDF.loc[i, 'latitude'], 
                                     self.taggedDF.loc[i, 'longitude']), 
                                    alt=int(self.taggedDF.loc[i, 'elevation']), 
                                    timeStamp=self.taggedDF.loc[i, 'timestamp'])
            photo.modGPSData(info, self.projectPath+'geotagged_frames/'+ frame)
            i+=1
    
    def load_project(self, projectPath):
        with open(projectPath, 'rb') as f:
            data = dill.load(f)
        self.inputPath = data.inputPath
        self.projectPath = data.projectPath
        self.videos = data.videos
        self.tracks = data.tracks
        self.framesDF = data.framesDF
        self.pointsDF = data.pointsDF
    
    def save_project(self,project):
        with open(self.projectPath+self.projectName+'.pkl', 'wb') as f:
            dill.dump(project, f)
