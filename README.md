# video-timestamp-gen
Generates a CSV containing each frame of a video and its respective timestamp

# Description
Uses exiftool to search video metadata for tag: "TrackCreateDate"
Uses opencv to calculate timedelta(offset) for each frame
Adds creationdate to each offset to get timestamp for each frame
Builds and exports dataframe as CSV in name format: <filename>_timestamps.csv

# Usage
from command line you : python tsgen.py <video filename>
