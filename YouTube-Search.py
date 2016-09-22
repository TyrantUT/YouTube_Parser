#!/usr/bin/python
"""
YouTube_Parse_v3
Python script to search through YouTube videos based on search criteria, download each given video
and convert to MP3, search through the video Description for a tracklist and split the initial 
download into the proper track lists.
"""

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
from mutagen.easyid3 import EasyID3
from termcolor import colored
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

with open('./youtube.key', 'r') as k:
  DEVELOPER_KEY = k.readline()

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def color_print(p_string, color):
  print colored(p_string, color)

# ManageTracks objects handle all track parsing, splitting, and renaming operations
class ManageTracks(object):

  def __init__(self, mt_id, mt_vt):

    self.mt_id = mt_id # YouTube Video ID
    self.mt_vt = mt_vt # YouTube Video Title

    # Variables to be used throughout class
    self.mt_fn = './Music/' + mt_vt + '.mp3' # YouTube Video Filename

  def get_tracklist(self):

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

  def parse_tracklist(self, meta):

    track_time_name = []
    for line in meta.splitlines():
      if re.match('.*?\d{1,2}:\d{2}', line):
        track_time_name.append(line)

    for u in track_time_name:
      print u
    return track_time_name

  def get_file_duration(self):
    cmd1 = "ffprobe -i "
    cmd2 = " -show_entries format=duration -v quiet -of csv='p=0'"
    full_command = cmd1 + '"' + self.mt_fn + '"' + cmd2
    output = os.popen(full_command).read().strip("\n")
    if output:
      return output
    else:
      color_print('    [!] Could not extract duration of song', 'red')
      color_print('[!] QUITTING. Find a new song!', 'yellow')
      quit()

  def write_track_to_file(self, track_title, track_seconds):

    # Output file will be the title of the main downloaded YouTube file
    # Create a new empty file for appending

    output_txt = './Tracklist/' + self.mt_vt + '.txt'
    title_txt_file = open(output_txt, 'a')
    title_txt_file.write(self.mt_vt + '\n\n')
    for index, value in enumerate(track_seconds):
      title_time = time.strftime("%H:%M:%S", time.gmtime(value))
      title_txt_file.write('[' + str(title_time) + '] ' + track_title[index] + '\n')

    title_txt_file.close()

  def split_song_to_tracks(self, val, track_start, track_stop):

    audio_converter = 'ffmpeg'
    command_start = ' -ss '
    command_end = ' -t '
    command_input = ' -i '
    command_codec = ' -acodec copy '
    input_file = '"' + self.mt_fn + '"'
    output_file = '"' + val + '.mp3"'

    # Handle final track float for track duration float
    track_end = float(track_stop) - track_start

    running_command = audio_converter + command_input + input_file + command_start + str(track_start) + command_end + str(track_end) + command_codec + " " + output_file
    cmd = shlex.split(running_command)

    #print '    [+] Attempting to split track ' + val
    #print '    [+] Splitting from ' + str(track_start) + ' to ' + str(track_stop)
    color_print('    [+] Attempting to split track ' + val, 'blue')
    color_print('    [+] Splitting from ' + str(track_start) + ' to ' + str(track_stop), 'green')
    try:
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
      for line in process.stdout:
        if line[5:] == "size=":
          print(line)
      #print '    [+] Track split'
      color_print('    [+] Track split', 'white')
    except Exception, e:
      #print '    [!] Unable to split track ' + val + ' "' + str(e) + '"'
      color_print('    [!] Unable to split track ' + val + ' "' + str(e) + '"', 'red')

    #print '    [+] Attempting to move to ./Converted folder'
    color_print('    [+] Attempting to move to ./Converted folder', 'green')


    try:
      shutil.move('./' + val + '.mp3', './Converted/' + val + '.mp3')
    except Exception, e:
      #print '    [!] Unable to move file. ' + str(e)
      color_print('    [!] Unable to move file. ' + str(e), 'red')

  def split_tracks(self, track_time_name):
  
    track_title = []
    track_seconds = []

    total_duration = self.get_file_duration()

    for ln in track_time_name:
    
      try:
        track_time = re.search('\d{1,3}:\d{2}(:\d{2})?', ln).group(0)
        track_name = re.search('[a-zA-Z]+.*[^0-9]*', ln).group(0).encode('ascii', errors='ignore').replace('/', '').replace('"', '')
      except Exception, e:
        #print '    [!] Unable to parse strings. ' + str(e)
        color_print('    [!] Unable to parse strings. ' + str(e), 'red')

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
        self.split_song_to_tracks(val, track_seconds[index], total_duration)

      else:
        self.split_song_to_tracks(val, track_seconds[index], track_seconds[index + 1])
        index += 1

    self.write_track_to_file(track_title, track_seconds)
    #print '    [+] Tracklist written to file.'
    #print '    [+] Attempting to write ID3 tags'
    color_print('    [+] Tracklist written to file.', 'green')
    color_print('    [+] Attempting to write ID3 tags', 'blue')
    try:
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
    #print '    [+] Renaming complete'
    color_print('    [+] Renaming complete', 'green')
  except Exception, e:
    #print '[!] Unable to rename file', str(e)
    color_print('[!] Unable to rename file', str(e), 'red')
  
  # Initiate track clalss
  track_class = ManageTracks(video_id, title)
  
  try:
    init_tracklist = track_class.get_tracklist()
    #print '    [+] Tracklist Detected. Attempting to split tracks'
    color_print('    [+] Tracklist Detected. Attempting to split tracks', 'yellow')
    track_class.split_tracks(init_tracklist)

  except Exception, e:
    #print '    [!] Unable to detect tracklist'
    color_print('    [!] Unable to detect tracklist' + str(e), 'red')


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

  #print "\nThis is what I found\n"
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

    #print 'You selected: ' + videos.keys()[int(download_number)]
    color_print('You selected: ' + videos.keys()[int(download_number)], 'yellow')
    new_yes = raw_input("Do you want to continue or select a new song? (yes to continue) ")
    
    # Format title to ascii characters only for easier management, and grab video ID for download function
    if new_yes == 'yes':
      title = videos.keys()[int(download_number)]
      title = title.encode('ascii', errors='ignore').replace('/', '').replace('"', '')
      single_video_id = videos.values()[int(download_number)]
      #print '[!] Checking music folder for duplicates'
      color_print('[!] Checking music folder for duplicates', 'blue')
      
      # Check for duplicated, if found re-run function
      if check_duplicates(title):
        #print "[!] File found in database."
        color_print('[!] File found in database.', 'red')
        time.sleep(1)
        youtube_search(options) 

      else:
        #print "\n[+] Starting Download and Conversion Process"
        color_print('\n[+] Starting Download and Conversion Process', 'green')
        download_mp3(title, single_video_id)
        quit()

    else:
      youtube_search(options)

  elif yes_no == '3':
    #print "[!] Exiting"
    color_print('[!] Exiting', 'red')
    quit()
     
  elif yes_no == '2':

    print '\n'

    # Format the title and remove / and " characters
    for title, video_id in videos.items():
      
      title = title.encode('ascii', errors='ignore').replace('/', '').replace('"', '')

      # Check for duplicated, if found pass the file
      if check_duplicates(title):
        #print "\n[!] Duplicate file found."
        color_print('\n[!] Duplicate file found.', 'red')
        pass
      else:
        #print "\n[+] Starting Download and Conversion Process"
        color_print('\n[+] Starting Download and Conversion Process', 'green')
        download_mp3(title, video_id)

  else:
    os.system('clear')
    #print "[!] Please select 1, 2, or 3."
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