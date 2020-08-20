# video-timestamp-gen
A couple of functions I made packed into one script
getCreationDate - Gets creation date of a video from exif tag "TrackCreateDate"
getTimestamps - Generates a CSV containing each frame of a video and its respective timestamp

# Description
Main function is getTimestamps:
Uses exiftool to search video metadata for tag: "TrackCreateDate"
Uses opencv to calculate timedelta(offset) for each frame
Adds creationdate to each offset to get timestamp for each frame
Builds and exports dataframe as CSV in name format: <filename>_timestamps.csv

# Usage
from command line you : python tsgen.py <video filename>

# Notes
Soon I will add ability to call each function from command line but for now you can only access getTimestamps

  
