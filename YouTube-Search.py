#!/usr/bin/python
"""
Python script to search through YouTube videos based on search criteria, download each given video
and convert to MP3, search through the video Description for a tracklist and split the initial 
download into the proper track lists.
"""

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import youtube_dl
import sys
import urlparse
import json
import re
import urllib
import urllib2
import time
import os
import glob
import shutil
import collections
import subprocess
import shlex
import time

_youtube_key_ = './youtube.key'

if not os.path.exists(_youtube_key_):
  print '[!] Unable to find YouTube API Key File. Please re-create and try again.'
  quit()

track_time_name = []

with open('./youtube.key', 'r') as k:
  DEVELOPER_KEY = k.readline()

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

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
        print('\n    [+] Download Complete. Conversion in progress...')

def parse_tracklist(meta):
  found = False
  global track_time_name
  for line in meta.splitlines():
    if re.match('.*?\d{1,2}:\d{2}', line):
      found = True
      track_time_name.append(line)
      #print line
  if found == False:
    return False
  else:
    return True

def get_tracklist(video_id):

  video_url = 'https://www.googleapis.com/youtube/v3/videos?id=' + video_id + '&key=' + DEVELOPER_KEY.strip('\n') + '&part=snippet'

  response = urllib2.urlopen(video_url)
  video_response = json.load(response)
  videoMetadata = []

  for v in video_response['items']:
    videoMetadata.append(v['snippet']['description'])
  for meta in videoMetadata:
    if parse_tracklist(meta):
      return True

def split_song_to_tracks(val, track_start, track_stop, new_filename):

  audio_converter = 'ffmpeg'
  command_start = ' -ss '
  command_end = ' -t '
  command_input = ' -i '
  command_codec = ' -acodec copy '
  input_file = '"' + new_filename + '"'
  output_file = '"' + val + '.mp3"'

  # Handle final track float for track duration float
  track_end = float(track_stop) - track_start

  running_command = audio_converter + command_input + input_file + command_start + str(track_start) + command_end + str(track_end) + command_codec + " " + output_file
  cmd = shlex.split(running_command)

  
  print '    [+] Attempting to split track ' + val
  print '    [+] Splitting from ' + str(track_start) + ' to ' + str(track_stop)
  try:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    for line in process.stdout:
      if line[5:] == "size=":
        print(line)
    #os.system(running_command)
    print '    [+] Track split'
  except Exception, e:
    print '    [!] Unable to split track ' + val + ' "' + str(e) + '"'
  
  print '    [+] Attempting to move to ./Converted folder'

  try:
    shutil.move('./' + val + '.mp3', './Converted/' + val + '.mp3')
  except Exception, e:
    print '    [!] Unable to move file. ' + str(e)

def get_file_duration(new_filename):
  cmd1 = "ffprobe -i "
  cmd2 = " -show_entries format=duration -v quiet -of csv='p=0'"
  full_command = cmd1 + '"' + new_filename + '"' + cmd2
  output = os.popen(full_command).read().strip("\n")
  if output:
    return output
  else:
    print '    [!] Could not extract duration of song'
    print '[!] QUITTING. Find a new song!'
    quit()

def write_track_to_file(new_filename, track_title, track_seconds):

  # Output file will be the title of the main downloaded YouTube file
  txt_file_name = new_filename.replace('./Music/', '').replace('.mp3', '')
  
  # Create a new empty file for appending
  output_txt = './Tracklist/' + txt_file_name + '.txt'
  title_txt_file = open(output_txt, 'a')
  title_txt_file.write(txt_file_name + '\n\n')
  for index, value in enumerate(track_seconds):
    title_time = time.strftime("%H:%M:%S", time.gmtime(value))
    title_txt_file.write('[' + str(title_time) + '] ' + track_title[index] + '\n')

  title_txt_file.close()


def split_tracks(track_time_name, new_filename):
  
  track_title = []
  track_seconds = []

  total_duration = get_file_duration(new_filename)

  for ln in track_time_name:
    
    try:
      track_time = re.search('\d{1,3}:\d{2}(:\d{2})?', ln).group(0)
      track_name = re.search('[a-zA-Z]+.*[^0-9]*', ln).group(0)
    except Exception, e:
      print '    [!] Unable to parse strings. ' + str(e)

    track_title.append(track_name)

    parts = track_time.split(':')
    seconds = None
    if len(parts) == 3: # h:m:s
      seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2: # m:s
      seconds = int(parts[0]) * 60 + int(parts[1])
    track_seconds.append(seconds)

  index = 0
  for i, val in enumerate(track_title):

    if index == len(track_title) - 1:
      split_song_to_tracks(val, track_seconds[index], total_duration, new_filename)

    else:
      split_song_to_tracks(val, track_seconds[index], track_seconds[index + 1], new_filename)
      index += 1

  write_track_to_file(new_filename, track_title, track_seconds)
  print '    [+] Tracklist written to file.'

  track_title = []
  track_seconds = []


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
    print('    [+] Now downloading: ' + title + '.mp3')
    try:
      ydl.download([url])
      print('    [+] Conversion complete')
      print('    [+] Renaming file')
    except:
      webm = max(glob.iglob('./*.[Ww][Ee][Bb][Mm]'), key=os.path.getctime)
      if os.path.isfile(webm):
        try:
          print '    [+] Attempting to convert directly.'
          os.system('ffmpeg -i ' + '"' + webm + '"' + ' -vn -c:a libmp3lame -b:a 128k ' + '"' + title + '"' + '.mp3')
        except:
          print('    [+] Failed to download / convert MP3')
        print('    [+] Failed to download / convert MP3')

  try:
    newest = max(glob.iglob('./*.[Mm][Pp]3'), key=os.path.getctime)
    os.rename(newest, './Music/' + title + '.mp3')
    print '    [+] Renaming complete'
  except:
    print('[!] Unable to rename file', sys.exc_info()[0])
  if get_tracklist(video_id):
    print '    [+] Detected track list in video Description.'
    print '    [+] Splitting song into separate tracks'
    new_filename = './Music/' + title + '.mp3'
    split_tracks(track_time_name, new_filename)

  track_time_name = [] # Reset global variable for next song

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

# TODO: Modify the dictionary to a list for proper individual file download handling
  videos = {}
  # Add each result to the appropriate dictionary
  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      video_id_dict = search_result["id"]["videoId"]
      videos.update({search_result["snippet"]["title"]: video_id_dict})

  # Create ordred dictionary for videos
  videos = collections.OrderedDict(videos)
 
  # Print titles found and prompt to continue
  os.system('clear')

  print "\nThis is what I found\n"
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

    print 'You selected: ' + videos.keys()[int(download_number)]
    new_yes = raw_input("Do you want to continue or select a new song? (yes to continue) ")
   
    if new_yes == 'yes':
      title = videos.keys()[int(download_number)]
      title = title.encode('ascii', errors='ignore').replace('/', '').replace('"', '')
      single_video_id = videos.values()[int(download_number)]
      print '[!] Checking music folder for duplicates'

      if check_duplicates(title):
        print "[!] File found in database."
        time.speed(1)
        youtube_search(options) 

      else:
        print "\n[+] Starting Download and Conversion Process"
        download_mp3(title, single_video_id)
        exit()

    else:
      youtube_search(options)

  elif yes_no == '3':
    print "[!] Exiting"
    exit()
     
  elif yes_no == '2':

    print '\n'
    # Call the check database file
    for title, video_id in videos.items():
      
      title = title.encode('ascii', errors='ignore').replace('/', '').replace('"', '')
      

      if check_duplicates(title):
        print "\n[!] Duplicate file found."
        pass
      else:
        print "\n[+] Starting Download and Conversion Process"
        download_mp3(title, video_id)

  else:
    os.system('clear')
    print "[!] Please select 1, 2, or 3."
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

  search_string = raw_input("Please enter a keyword to search: ")
  argparser.add_argument("--q", help="Search term", default=search_string)
  argparser.add_argument("--max-results", help="Max results", default=25)
  args = argparser.parse_args()

  try:
    youtube_search(args)
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)