import os
import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import base64
from PIL import Image
import io
import time
import pandas as pd
import numpy as np
import re
import datetime
import subprocess
from tqdm import tqdm
import gpxpy
from dateutil.parser import *
import pytz
from GPSPhoto import gpsphoto
import dateparser
import subprocess
import sys
import tkinter


def trackExtract(gps_filename, gp_timezone = 'US/Eastern'):
    """Returns a dataframe containing the telemetry collected from the gpx file"""
    ext = gps_filename.split('.')
    global track_name
    track_name = ext[0]
    if ext[1] == 'csv':
        print('Parsing '+ gps_filename + '...')
        begin_time = datetime.datetime.now()
        gps_telem = pd.read_csv(gps_filename)
        gps_telem = gps_telem.rename(columns={'lat': 'latitude', 'lon': 'longitude','ele':'elevation','time':'timestamp'})
        i = 0
        for timestamp in gps_telem['timestamp']:
            gps_telem.loc[i,'timestamp'] = dateparser.parse(gps_telem.loc[i,'timestamp']).replace(tzinfo=pytz.UTC)
            i+=1
        print('Done in '+ str(datetime.datetime.now() - begin_time))
    if ext[1] == 'gpx':
        points = list()
        with open(gps_filename,'r') as gpxfile:
            gpx = gpxpy.parse(gpxfile)
            for track in gpx.tracks:
                for segment in track.segments:
                    sys.stdout.flush()
                    for point in tqdm(segment.points,desc='Parsing '+ gps_filename,unit='points'):
                        dict = {'timestamp': point.time,
                                'latitude': point.latitude,
                                'longitude': point.longitude,
                                'elevation': point.elevation
                                    }
                        points.append(dict)
        gps_telem = pd.DataFrame.from_dict(points)
        i = 0
        sys.stdout.flush()
        for timestamp in tqdm(gps_telem['timestamp'],desc='Converting gps timestamps',unit='points'):
            gps_telem.loc[i,'timestamp'] = gps_telem.loc[i,'timestamp'].to_pydatetime().replace(tzinfo=pytz.UTC) #.astimezone(pytz.timezone(gp_timezone))
            i+=1
    return gps_telem
#track_extract(gps_filename = 'track-71520-23237pm.gpx')

def concatenate(gopro_filename=['null'], gps_filename=['null'], gp_timezone = 'US/Eastern',autoscan = True):
    """
    

    Parameters
    ----------
    gopro_filename : List
        Filename list of gopro videos desired to be processed.
    gpx_filename : List
        Filename list of gps tracks desired to be processed.
    gp_timezone : TYPE, optional
        DESCRIPTION. The timezone associated with gopro video. The default is 'US/Eastern'.
    autoscan : TYPE, Boolean
        DESCRIPTION. The default is True. If True, all gopro and gps files in the working directory are processed

    Returns
    -------
    concatenate_df : TYPE
        DESCRIPTION.

    """
    global track_ex
    global gp_ex
    gp_ex = pd.DataFrame(columns=['frame','timestamp'])
    track_ex = pd.DataFrame()
    if autoscan == True:
        gopro_filenames = []
        gps_filenames = []
        for filename in os.listdir():
            if 'MP4' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    gopro_filenames.append(filename)
                    df = gp_extract(filename)
                    gp_ex = gp_ex.append(df,ignore_index=True)
            if 'gpx' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    gps_filenames.append(filename)
                    df = track_extract(filename, gp_timezone)
                    track_ex = track_ex.append(df,ignore_index=True)
            if 'csv' in filename.split('.'):
                if len(filename.split('.')) <= 2:
                    gps_filenames.append(filename)
                    df = track_extract(filename, gp_timezone)
                    track_ex = track_ex.append(df,ignore_index=True)
    
    if autoscan == False:
        for filename in gopro_filename:
            df = gp_extract(gopro_filename)
            gp_ex = gp_ex.append(df,ignore_index=True)
        for filename in gps_filename:
            df = track_extract(gps_filename)
            track_ex = track_ex.append(df,ignore_index=True)
    concatenate_df = track_ex
    i = 0
    sys.stdout.flush()
    for gpstime in tqdm(track_ex['timestamp'],desc='Matching frames from: '+str(gopro_filenames)+ ' to points on: '+ str(gps_filenames),unit='frames'):
        timedeltas = []
        for gptime in gp_ex['timestamp']:
            delta = gpstime-gptime
            timedeltas.append(abs(delta.total_seconds()))
        ix = gp_ex.loc[timedeltas.index(min(timedeltas)), 'frame']
        concatenate_df.loc[i, 'frame'] = ix
        i += 1
    #i = 0
    #for frame in concatenate_df['frame']:
        #if i+2<len(concatenate_df['frame']):
            #if concatenate_df.loc[i,'frame'] == concatenate_df.loc[i+2,'frame']:
                #concatenate_df.drop(labels=i,axis=0)
                #i+=1
        #else:
            #break
    return concatenate_df

def geotag(df):
    os.mkdir('geotagged_'+track_name+'/')
    i = 0
    sys.stdout.flush()
    for frame in tqdm(df['frame'],desc='Geotagging '+ str(len(df['frame'])) + ' frames to path: '+'geotagged_'+track_name+'/',unit='frames'):
        photo = gpsphoto.GPSPhoto('frames/'+frame)
        info = gpsphoto.GPSInfo((df.loc[i, 'latitude'], 
                                 df.loc[i, 'longitude']), 
                                alt=int(df.loc[i, 'elevation']), 
                                timeStamp=df.loc[i, 'timestamp'])
        photo.modGPSData(info, 'geotagged_'+track_name+'/'+ frame)
        i+=1

def classify(df):
    class_key = 'Undefined = 0, Loam = 1, Sand = 2, Gravel = 3, Cobble = 4'
    i = 0
    for frame in df['frame']:
        print(class_key)
        print('Displaying '+frame+' ...')
        image = Image.open('frames/'+frame)
        image.show()
        sed_type = int(input('Sediment type: '))
        df.loc[i,'sed_type'] = sed_type
        i+=1
def pyplot_classify(df):
    class_key = 'Undefined = 0, Loam = 1, Sand = 2, Gravel = 3, Cobble = 4'
    i = 0
    for frame in df['frame']:
        print(class_key)
        print('Displaying '+frame+' ...')
        img = mpimg.imread('frames/'+frame)
        plt.imshow(img)
        sed_type = int(input('Sediment type: '))
        df.loc[i,'sed_type'] = sed_type
        i+=1
        
