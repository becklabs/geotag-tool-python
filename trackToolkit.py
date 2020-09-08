import os
import pandas as pd
import gpxpy
import pytz
import dateparser
import sys


def trackExtract(inputPath,gps_filename,projectPath,gp_timezone = 'US/Eastern'):
    """Returns a dataframe containing the telemetry collected from the gpx file"""
    ext = gps_filename.split('.')
    track_name = ext[0]
    if ext[1] == 'csv':
        gps_telem = pd.read_csv(inputPath+gps_filename)
        if 'esrignss_latitude' in list(gps_telem.columns):
            gps_telem = gps_telem.rename(columns={'esrignss_latitude': 'latitude', 'esrignss_longitude': 'longitude','esrignss_altitude':'elevation','esrignss_fixdatetime':'timestamp'})
            gps_telem1 = pd.DataFrame()
            gps_telem1['latitude'] = gps_telem['latitude']
            gps_telem1['longitude'] = gps_telem['longitude']
            gps_telem1['elevation'] = gps_telem['elevation']
            gps_telem1['timestamp'] = gps_telem['timestamp']
            gps_telem = gps_telem1
        if 'lat' in list(gps_telem.columns):
            gps_telem = gps_telem.rename(columns={'lat': 'latitude', 'lon': 'longitude','ele':'elevation','time':'timestamp'})
        i = 0
        for timestamp in gps_telem['timestamp']:
            gps_telem.loc[i,'timestamp'] = dateparser.parse(gps_telem.loc[i,'timestamp']).replace(tzinfo=pytz.UTC)
            i+=1
    if ext[1] == 'gpx':
        points = []
        with open(inputPath+gps_filename,'r') as gpxfile:
            gpx = gpxpy.parse(gpxfile)
            for track in gpx.tracks:
                for segment in track.segments:
                    sys.stdout.flush()
                    for point in segment.points:
                        dict = {'timestamp': point.time,
                                'latitude': point.latitude,
                                'longitude': point.longitude,
                                'elevation': point.elevation
                                    }
                        points.append(dict)
        gps_telem = pd.DataFrame.from_dict(points)
        i = 0
        for timestamp in gps_telem['timestamp']:
            gps_telem.loc[i,'timestamp'] = gps_telem.loc[i,'timestamp'].to_pydatetime().replace(tzinfo=pytz.UTC) #.astimezone(pytz.timezone(gp_timezone))
            i+=1
    if 'tracks' not in os.listdir(projectPath):
        os.mkdir(projectPath+'tracks/')
    gps_telem.to_csv(projectPath+'tracks/'+track_name+'.csv')
    return gps_telem
