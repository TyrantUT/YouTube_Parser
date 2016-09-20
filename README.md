
YouTube_Parse_v3

Python script to search through YouTube videos based on search criteria, download each given video
and convert to MP3, search through the video Description for a tracklist and split the initial 
download into the proper track lists.

##BUGS##
- Identify live streams and ignore the download

##TODO##
- [X] Fix videos dictionary and move to an ordered list for manual selection
- Implement duplicate song searches in ./Converted folder - Some file names differ by a period
- If song has a tracklist, delete the original and only keep the converted files
- [X] Move track_time_name[] list away from global variable. Not really a problem, just isn't clean
- [X] Create txt file for each downloaded mix with the tracklist and times for future reference
- [X] Generate ID3 tags for split files

#FUTURE TASKS#
- [X] Implement classes
- Standardize file name strings. Using way too many different methods to capture the file name
- Move printing items to a single def and reference with an index number (case)
  - [X] Add colored printing to console
- Move away from Youtube-dl and implement a faster method of extracting the audio from videos
  - ffmpeg for conversion is really slow, but is good for splitting tracks (is immediate)