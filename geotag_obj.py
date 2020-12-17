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
    
    def create(self,videos=[],tracks=[],inputPath=False, projectPath=False, autoscan=True):
        #MANAGE PATH
        if inputPath != False:
            if inputPath[-1] != '/':
                if inputPath[-1] != '\\':
                    inputPath = inputPath+'\\'
                    
        #MANAGE CREATE PROJECT
        time = datetime.datetime.now()
        projectName = 'project'+ time.strftime('%Y-%m-%d_%H%M%S')
        self.projectName = projectName
        if projectName not in os.listdir(projectPath):
            os.mkdir(projectPath+'/'+projectName+'/')
        projectPath += '\\'+projectName+'\\'
        self.projectPath = projectPath
        self.inputPath = inputPath
        del(projectName, projectPath, inputPath)
        
        #MANAGE AUTOSCAN
        if autoscan == True:
            for filename in os.listdir(self.inputPath):
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
        del(videos, tracks)
        
        #READ DATA INTO DATAFRAMES    
        framesDFs = []
        fps_list = []
        pointsDFs = []
        for video in self.videos: 
            framesDFs.append(getTimestamps(self.inputPath,video))
            fps_list.append(getFps(self.inputPath, video))
        for track in self.tracks:
            pointsDFs.append(trackExtract(self.inputPath,track))
        self.framesDFs = framesDFs
        self.pointsDFs = pointsDFs
        self.fps_list = fps_list
        del(framesDFs, fps_list, pointsDFs)
        
    def match(self, maxtimediff = 1.0, timeoffset=False):
        if timeoffset == False:
            timeoffset = 0
        self.taggedDFs = []
        for pointsDF in self.pointsDFs:
            for framesDF in self.framesDFs:          
                framesDF['adjTimestamp'] = [i+datetime.timedelta(hours=timeoffset) for i in framesDF['Timestamp']]
                video_ind = self.framesDFs.index(framesDF)
                curr_frame = None
                point_ind = 0
                
                for pointTime in pointsDF['timestamp']:
                    timedelta = abs((framesDF['adjTimestamp'][0]-pointTime).total_seconds())
                    if timedelta <= maxtimediff:
                        frame_ind = 0
                        curr_frame = framesDF.loc[frame_ind, 'Frame']
                        break
                    point_ind+=1
                    
                if curr_frame is None:
                    for pointTime in tqdm(pointsDF['timestamp']):
                        timedeltas = [abs((pointTime-frameTime).total_seconds()) for frameTime in framesDF['adjTimestamp']]
                        min_delta = min(timedeltas)
                        if min_delta <= maxtimediff:
                            frame_ind = timedeltas.index(min_delta)
                            curr_frame = framesDF.loc[frame_ind, 'Frame']
                            break
                        point_ind+=1

                if curr_frame is not None:
                        fps = self.fps_list[video_ind]
                        taggedDF = pointsDF
                        while frame_ind < len(framesDF['Timestamp']):
                            curr_frame = framesDF['Frame'][frame_ind]
                            taggedDF.loc[point_ind,'Frame'] = curr_frame
                            delta = (pointsDF['timestamp'][point_ind] - pointsDF['timestamp'][point_ind-1]).total_seconds()
                            frame_ind+=int(delta*fps)
                            point_ind+=1
                        taggedDF = taggedDF.dropna()
                        taggedDF = taggedDF.reset_index(drop=True)
                        self.taggedDFs.append(taggedDF)
                        self.framesDFs.pop(video_ind)
                        del(taggedDF,pointsDF,framesDF)
                        break  
                    
    def export(self):
        time = datetime.datetime.now()
        export_path = 'export '+time.strftime('%H_%M_%S')+'/'
        for ind in range(len(self.videos)):
            createFrames(self.inputPath,self.videos[ind],self.projectPath,export_path,self.taggedDFs[ind])
        self.taggedDFs = pd.concat(self.taggedDFs, ignore_index=True)
        i = 0
        for frame in tqdm(self.taggedDFs['Frame']):
            photo = gpsphoto.GPSPhoto(self.projectPath+export_path+frame)
            info = gpsphoto.GPSInfo((self.taggedDFs.loc[i, 'latitude'], 
                                     self.taggedDFs.loc[i, 'longitude']), 
                                    alt=int(self.taggedDFs.loc[i, 'elevation']), 
                                    timeStamp=self.taggedDFs.loc[i, 'timestamp'])
            photo.modGPSData(info, self.projectPath+export_path+frame)
            i+=1

    def load(self, projectPath):
        for file in os.listdir(projectPath):
            if len(file.split('.')) == 2 and file.split('.')[1] == 'pkl':
                projectPath+='\\'+file
                break
        with open(projectPath, 'rb') as f:
            data = dill.load(f)
        self.inputPath = data.inputPath
        self.projectPath = data.projectPath
        self.projectName = data.projectName
        self.videos = data.videos
        self.tracks = data.tracks
        self.framesDFs = data.framesDFs
        self.pointsDFs = data.pointsDFs
        self.fps_list = data.fps_list
        try:
            self.taggedDFs = data.taggedDFs
        except AttributeError: self.taggedDFs = None
        
    def save(self,project):
        with open(self.projectPath+self.projectName+'.pkl', 'wb') as f:
            dill.dump(project, f)
