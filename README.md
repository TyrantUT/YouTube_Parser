
Python script to search through YouTube videos based on search criteria, download each given video
and convert to MP3, search through the video Description for a tracklist and split the initial 
download into the proper track lists.

##BUGS##
- Identify live streams and ignore the download - These usually don't have accurate tracklists anyway

##TODO##
- Fix videos dictionary and move to an ordered list for manual selection
- Implement duplicate song searches in ./Converted folder - Some file names differ by a period
- Move files with no tracklist into a separete folder other than ./Music
- Move track_time_name[] list away from global variable. Not really a problem, just isn't clean
- Create txt file for each downloaded mix with the tracklist and times for future reference

#FUTURE TASKS#
- Move to a class based script to clean it up a bit. There are a lot of defs calling other defs
- Potentially compile?
- Standardize file name strings. Using way too many different methods to capture the file name
- Move printing items to a single def and reference with an index number (case)
- Move away from Youtube-dl and implement a faster method of extracting the audio from videos
  - ffmpeg for conversion is really slow, but is good for splitting tracks (is immediate)