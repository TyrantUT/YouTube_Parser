#!/usr/bin/python
"""
YouTube_Parse_v3
Python script to search through YouTube videos based on search criteria, download each given video
and convert to MP3, search through the video Description for a tracklist and split the initial 
download into the proper track lists.
"""

import collections
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import time
import urllib
import urllib2
import urlparse
import youtube_dl

from apiclient.discovery import build
from apiclient.errors import HttpError
from mutagen.easyid3 import EasyID3
from oauth2client.tools import argparser
from termcolor import colored

_youtube_key_ = './youtube.key' # YouTube Developer API Key file

# TODO: If file does not exist, prompt to create it and enter key at console
if not os.path.exists(_youtube_key_): # Check if file exists
  print '[!] Unable to find YouTube API Key File. Please re-create and try again.'
  quit()

with open('./youtube.key', 'r') as k:
  DEVELOPER_KEY = k.readline()

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def color_print(p_string, color): # Function to print color to console

  print colored(p_string, color)

class ManageTracks(object): # ManageTracks objects handle all track parsing, splitting, and renaming operations

  def __init__(self, mt_id, mt_fn):
    # Class variables from call
    self.mt_id = mt_id # Video ID of initial download
    self.mt_fn = mt_fn # File Name of initial download

    # Variables to be used throughout the class 
    self.mt_tn = mt_fn.replace('./Music/', '').replace('.mp3', '') # Track Name of initial download

  def get_tracklist(self): # Extract description from YouTube video

    video_url = 'https://www.googleapis.com/youtube/v3/videos?id=' + self.mt_id + '&key=' + DEVELOPER_KEY.strip('\n') + '&part=snippet'
    response = urllib2.urlopen(video_url)
    video_response = json.load(response)
    video_meta = []
    
    try:
      for v in video_response['items']:
        video_meta.append(v['snippet']['description'])
      for meta in video_meta:
        description = self.parse_tracklist(meta)
      return description
    except:
      return False

  def parse_tracklist(self, meta): # Helper function to find matching lines with valid timestamps

    track_time_name = []
    for line in meta.splitlines():
      if re.match('.*?\d{1,2}:\d{2}', line):
        track_time_name.append(line)
    return track_time_name

  def get_file_duration(self): # Get  song duration of intitla download / converted file

    cmd1 = "ffprobe -i "
    cmd2 = " -show_entries format=duration -v quiet -of csv='p=0'"
    full_command = cmd1 + '"' + self.mt_fn + '"' + cmd2
    output = os.popen(full_command).read().strip("\n")
    if output:
      return output
    else:
      color_print('    [!] Could not extract duration of song', 'red')
      color_print('    [!] QUITTING. Find a new song!', 'yellow')
      quit()

  def write_tracklist_to_txt(self, track_title, track_seconds):

    output_txt = './Tracklist/' + self.mt_tn + '.txt' # Create a new file with the name of the inital download
    title_txt_file = open(output_txt, 'a') # Create new file for appending
    title_txt_file.write(self.mt_tn + '\n\n') # Write main title to first line
    for index, value in enumerate(track_seconds): # Enumerate through each item in track_title and track_seconds
      title_time = time.strftime("%H:%M:%S", time.gmtime(value)) # Format seonds to valid timestamp
      title_txt_file.write('[' + str(title_time) + '] ' + track_title[index] + '\n') # Finally write timestamp and title to file

    title_txt_file.close() # Close txt file

  def split_song_to_tracks(self, val, track_start, track_stop):

    # Set up command for splitting tracks
    audio_converter = 'ffmpeg'
    command_start = ' -ss ' # Start
    command_end = ' -t ' # End
    command_input = ' -i ' # Input file
    command_codec = ' -acodec copy ' # Codec and method
    input_file = '"' + self.mt_fn + '"' # Need to handle spaces in file name
    output_file = '"./Converted/' + val + '.mp3"' # Need to handle spaces in file name

    track_end = float(track_stop) - track_start # Handle final track float for track duration float

    running_command = audio_converter + command_input + input_file + command_start + str(track_start) + \
     command_end + str(track_end) + command_codec + " " + output_file
    cmd = shlex.split(running_command)

    color_print('    [+] Attempting to split track ' + val, 'blue')
    color_print('    [+] Splitting from ' + str(track_start) + ' to ' + str(track_stop), 'green')

    try:
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True) # So we can grab only what we want from the command
      for line in process.stdout:
        if line[:5] == "size=": # Check for the line we're going to use to write to console
          regex = re.compile(r'(\d+)([kgtb]?b).*?bitrate=\s*(\d+\.\d+)kbits\/s', re.IGNORECASE) # REGEX to grab only what we need
          track_details = regex.findall(line) # Run REGEX on the line string
          color_print('    [+] File Size: ' + track_details[0][0] + ' ' + track_details[0][1] + '\t\tBitrate= ' + track_details[0][2], 'yellow')
      
      color_print('    [+] Track split', 'white')
      color_print('    [+] Track written to ./Convertd folder', 'green')

    except Exception, e:   
      color_print('    [!] Unable to split track ' + val + ' "' + str(e) + '"', 'red')
   
  def split_tracks(self, track_time_name):
  
    track_title = [] # List for the titles of each individual track
    track_seconds = [] # List of each track duration in seconds

    total_duration = self.get_file_duration() # Grab file duration of initial downloaded file

    for ln in track_time_name:
    
      try:
        track_time = re.search('\d{1,3}:\d{2}(:\d{2})?', ln).group(0)
        track_name = re.search('[a-zA-Z]+.*[^0-9]*', ln).group(0)
        track_name = track_name.strip(track_time).strip() # Strip track_time just in case it is written after the track title
      except Exception, e:
        #print '    [!] Unable to parse strings. ' + str(e)
        color_print('    [!] Unable to parse strings. ' + str(e), 'red')

      track_title.append(track_name)

      parts = track_time.split(':')
      seconds = None
      if len(parts) == 3: # Account for H:M:S
        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
      elif len(parts) == 2: # Accont for M:S
        seconds = int(parts[0]) * 60 + int(parts[1])
      track_seconds.append(seconds)

    index = 0
    for i, val in enumerate(track_title):

      if index == len(track_title) - 1: # Determine if the last track is up to be split
        self.split_song_to_tracks(val, track_seconds[index], total_duration) # Account for last track to split to end of initial song

      else:
        self.split_song_to_tracks(val, track_seconds[index], track_seconds[index + 1]) # Split track up to the start of the next track
        index += 1

    self.write_tracklist_to_txt(track_title, track_seconds) # Write tracklist to txt file for future reference

    color_print('    [+] Tracklist written to file.', 'green')
    color_print('    [+] Attempting to write ID3 tags', 'blue')

    try: # Try to generate ID3 tags for track title
      id3 = GenerateID3(track_title)
      id3.writeID3()
    except:
      #print '    [!] Unable to write ID3 tags'
      color_print('    [!] Unable to write ID3 tags', 'red')

# GenerateID3 objects handle all ID3 operations on converted MP3 files
class GenerateID3(object):

  def __init__(self, gi_videos):
    self.gi_videos = gi_videos

  def writeID3(self):
    artist_title = []
    _musicFolder_ = './Converted/'
    for track in self.gi_videos:
      try:
        mp3_file = track + '.mp3'
        artist_title = track.split(' - ')
        
        if len(artist_title) == 2:
          file_path = _musicFolder_ + mp3_file
          artist = artist_title[0]
          title = artist_title[1].replace('.mp3', '')
          #print '    [+] Starting id3 tag edit for ' + artist + ' - ' + title
          color_print('    [+] Starting id3 tag edit for ' + artist + ' - ' + title, 'blue')

          try:
            meta = EasyID3(file_path)
          except mutagen.id3.ID3NoHeaderErrors:
            meta = mutagen.File(file_path, easy=True)
            meta.add_tags()

          meta['artist'] = artist
          meta['title'] = title
          meta['genre'] = "Dubstep"
          meta['album'] = "Dubstep"
          meta.save()
        else:
          pass
      except Exception, e:
        print str(e)

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def restart_line():
  sys.stdout.write('\r')
  sys.stdout.flush()

def my_hook(d):
    if d['status'] == 'downloading':
        print '    [+] Download speed: ' + d['_speed_str'] + ' \t\t Percent Complete: ' + d['_percent_str'],
        restart_line()
        
    if d['status'] == 'finished':
        #print '\n    [+] Download Complete. Conversion in progress...'
        color_print('\n    [+] Download Complete. Conversion in progress...', 'yellow')

def download_mp3(title, video_id):

  global track_time_name
  url = 'https://youtube.com/watch?v=' + video_id
  ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
    'outtmpl': '%(title)s.%(ext)s',
 }

  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    #info_dict = ydl.extract_info(url, download=False)
    #pre_title = info_dict.get('title', None)
    #print '    [+] Now downloading: ' + title + '.mp3'
    color_print('    [+] Now downloading: ' + title + '.mp3', 'blue')
    try:
      ydl.download([url])
      #print '    [+] Download and Conversion complete'
      #print '    [+] Renaming file'
      color_print('    [+] Download and Conversion complete', 'green')
      color_print('    [+] Renaming file', 'blue')
    except:
      webm = max(glob.iglob('./*.[Ww][Ee][Bb][Mm]'), key=os.path.getctime)
      if os.path.isfile(webm):
        try:
          #print '    [+] Attempting to convert directly.'
          color_print('    [+] Attempting to convert directly.', 'blue')
          os.system('ffmpeg -i ' + '"' + webm + '"' + ' -vn -c:a libmp3lame -b:a 128k ' + '"' + title + '"' + '.mp3')
        except:
          #print '    [+] Failed to download / convert MP3'
          color_print('    [+] Failed to download / convert MP3', 'red')
        #print '    [+] Failed to download / convert MP3'
        color_print('    [+] Failed to download / convert MP3', 'red')

  try:
    newest = max(glob.iglob('./*.[Mm][Pp]3'), key=os.path.getctime)
    os.rename(newest, './Music/' + title + '.mp3')
    color_print('    [+] Renaming complete', 'green')

  except Exception, e:
    color_print('[!] Unable to rename file', str(e), 'red')
  
  # Initiate track clalss
  new_filename = './Music/{0}.mp3'.format(title)
  track_class = ManageTracks(video_id, new_filename)
  
  try:
    init_tracklist = track_class.get_tracklist()
    color_print('    [+] Tracklist Detected. Attempting to split tracks', 'yellow')
    track_class.split_tracks(init_tracklist)

  except:
    color_print('    [!] Tracklist process failed!', 'red')

def check_duplicates(title):

  song = './Music/{0}.mp3'.format(title)

  if os.path.exists(song):
    return True
  else:
    return False

def youtube_search(options):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  # Call the search.list method to retrieve results matching the specified
  # query term.
  search_response = youtube.search().list(
    q=options.q,
    part="id,snippet",
    maxResults=options.max_results
  ).execute()

  videos = {}
  # Add each result to the appropriate dictionary
  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      yt_video_title = search_result["snippet"]["title"]
      yt_video_id = search_result["id"]["videoId"]
      videos.update({yt_video_title: yt_video_id})

  # Create ordred dictionary for videos
  videos = collections.OrderedDict(videos)
 
  # Print titles found and prompt to continue
  os.system('clear')

  color_print('\nThis is what I found\n', 'yellow')
  counter = 1
  for title, video_id in videos.items():
    print '[' + str(counter) + '] ' +  title
    counter += 1

  print '\n'
  print '[1] Enter 1 to download a specific item'
  print '[2] Enter 2 to to continue with the full list'
  print '[3] Enter 3 to exit'

  yes_no = raw_input("[?] How do you want to continue? ")

  if yes_no == '1':

    print '\n'
    download_number = int(raw_input("Please enter the number of the video you want to download: "))
    print '\n'

    download_number -= 1

    color_print('You selected: ' + videos.keys()[int(download_number)], 'yellow')
    new_yes = raw_input("Do you want to continue or select a new song? (yes to continue) ")
    
    # Format title to ascii characters only for easier management, and grab video ID for download function
    if new_yes == 'yes':
      title = videos.keys()[int(download_number)]
      title = title.encode('ascii', errors='ignore').replace('/', '').replace('"', '')
      single_video_id = videos.values()[int(download_number)]

      color_print('[!] Checking music folder for duplicates', 'blue')
      
      # Check for duplicated, if found re-run function
      if check_duplicates(title):

        color_print('[!] File found in database.', 'red')
        time.sleep(1)
        youtube_search(options) 

      else:

        color_print('\n[+] Starting Download and Conversion Process', 'green')
        download_mp3(title, single_video_id)
        quit()

    else:
      youtube_search(options)

  elif yes_no == '3':

    color_print('[!] Exiting', 'red')
    quit()
     
  elif yes_no == '2':

    print '\n'

    # Format the title and remove / and " characters
    for title, video_id in videos.items():
      
      title = title.encode('ascii', errors='ignore').replace('/', '').replace('"', '')

      # Check for duplicated, if found pass the file
      if check_duplicates(title):

        color_print('\n[!] Duplicate file found.', 'red')
        pass
      else:
        color_print('\n[+] Starting Download and Conversion Process', 'green')
        download_mp3(title, video_id)

  else:
    os.system('clear')
    color_print('[!] Please select 1, 2, or 3.', 'red')
    time.sleep(2)
    os.system('clear')
    youtube_search(options)
      


if __name__ == "__main__":

  # Check for directories prior to moving on
  _music_ = './Music'
  _converted_ = './Converted'
  _tracklist_ = './Tracklist'

  if not os.path.isdir(_music_):
    os.makedirs(_music_)
  if not os.path.isdir(_converted_):
    os.makedirs(_converted_)
  if not os.path.isdir(_tracklist_):
    os.makedirs(_tracklist_)

  # Create arguments for YouTube search
  search_string = raw_input("Please enter a keyword to search: ")
  argparser.add_argument("--q", help="Search term", default=search_string)
  argparser.add_argument("--max-results", help="Max results", default=25)
  args = argparser.parse_args()

  try:
    # Start search function. This will branch off into the remainder of the script
    youtube_search(args)
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
    