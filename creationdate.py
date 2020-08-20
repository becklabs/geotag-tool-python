# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 19:50:43 2020

@author: beck
"""
import cv2
from tqdm import *
import datetime
import dateparser
import os
import sys
import pandas as pd

def getCreationDate(file):
    #GET CREATEDATE FROM EXIFTOOL
    stream = os.popen('exiftool '+file)
    output = stream.read().split('\n')
    for item in output:
        item = item.replace(' ','')
        if item.split(':')[0] == 'TrackCreateDate':
            break
    datelist=item.split(':')[1:]
    creationdate = ''
    for item in datelist:
        creationdate = creationdate+item
    creationdate = dateparser.parse(creationdate)
    
    #GET DELTA SECONDS FOR EVERY FRAME
    cap = cv2.VideoCapture(file)
    totalFps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    offsets = []
    pbar = tqdm(total=totalFps)
    while(cap.isOpened()):
        frame_exists, curr_frame = cap.read()
        if frame_exists:
            offsets.append(cap.get(cv2.CAP_PROP_POS_MSEC))
            pbar.update(1)
        else:
            break
    
    cap.release()
    pbar.close()
    
    #CONVERT OFFSETS TO TIMEDELTAS
    offsets = [datetime.timedelta(milliseconds=i) for i in offsets]
    
    #CALCULATE TIMESTAMPS
    timestamps = [creationdate+offset for offset in offsets]
    
    #GENERATE FRAME NAMES
    frames = [file+'_'+str(i) for i in range(len(timestamps))]
    
    #EXPORT DATA AS CSV
    df = pd.DataFrame()
    df['Frame'] = frames
    df['Timestamp'] = timestamps
    df.to_csv(file+'_timestamps')
    print(df)
if __name__ == '__main__':

    if len(sys.argv) != 2: 
        print("Need exactly one argument ...")
        print("usage: python creationdate.py <filename>")
        sys.exit()
    else:
        file = sys.argv[1]
        getCreationDate(file)