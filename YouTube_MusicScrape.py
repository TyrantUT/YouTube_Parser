#!/usr/bin/python
"""
YouTube Music Scraper v6

- Search for YouTube videos containing tracklists
- Download YouTube video
- Strip audio from video
- Split file into tracks from tracklist
- Write ID3 tags
- Write YouTube song thumbnail for each song

"""

import urllib
import urllib2
from apiclient.discovery import build
from apiclient.errors import HttpError
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

import re
import sys
import time
import os
import collections
import itertools
import shlex
import subprocess
import json
from termcolor import colored

from oauth2client.tools import argparser
from pytube import YouTube


# Small function to print items in color
def color_print(p_string, color):
  print colored(p_string, color)

def cycle_text(iterable, n):
  for item in itertools.cycle(iterable):
    for i in range(n):
      yield item

def detect_livestream(video_title):
  regex = re.compile(r'(live\s?stream)', re.IGNORECASE)
  if regex.findall(video_title):
    return True
  else:
    return False

def check_duplicates(video_title):
  song = './Music/{0}.mp3'.format(video_title)
  if os.path.exists(song):
    return True
  else:
    return False

class progressBar:
    def __init__(self, barlength=25):
        self.barlength = barlength
        self.position = 0
        self.longest = 0

    def print_progress(self, cur, total, start):
        currentper = cur / total
        elapsed = int(time.clock() - start) + 1
        curbar = int(currentper * self.barlength)
        bar = '\r[' + '='.join(['' for _ in range(curbar)])  # Draws Progress
        bar += '>'
        bar += ' '.join(['' for _ in range(int(self.barlength - curbar))]) + '] '  # Pads remaining space
        bar += bytestostr(cur / elapsed) + '/s '  # Calculates Rate
        bar += getHumanTime((total - cur) * (elapsed / cur)) + ' left'  # Calculates Remaining time
        if len(bar) > self.longest:  # Keeps track of space to over write
            self.longest = len(bar)
            bar += ' '.join(['' for _ in range(self.longest - len(bar))])
        sys.stdout.write(bar)

    def print_end(self, *args):  # Clears Progress Bar
        sys.stdout.write('\r{0}\r'.format((' ' for _ in range(self.longest))))

def getHumanTime(sec):
    if sec >= 3600:  # Converts to Hours
        return '{0:d} hour(s)'.format(int(sec / 3600))
    elif sec >= 60:  # Converts to Minutes
        return '{0:d} minute(s)'.format(int(sec / 60))
    else:            # No Conversion
        return '{0:d} second(s)'.format(int(sec))

def bytestostr(bts):
    bts = float(bts)
    if bts >= 1024 ** 4:    # Converts to Terabytes
        terabytes = bts / 1024 ** 4
        size = '%.2fTb' % terabytes
    elif bts >= 1024 ** 3:  # Converts to Gigabytes
        gigabytes = bts / 1024 ** 3
        size = '%.2fGb' % gigabytes
    elif bts >= 1024 ** 2:  # Converts to Megabytes
        megabytes = bts / 1024 ** 2
        size = '%.2fMb' % megabytes
    elif bts >= 1024:       # Converts to Kilobytes
        kilobytes = bts / 1024
        size = '%.2fKb' % kilobytes
    else:                   # No Conversion
        size = '%.2fb' % bts
    return size

def convertTo_mp3(video_title):

  audio_converter = 'ffmpeg'
  command_input = ' -i '
  input_file = '"' + _processing_ + '/' + video_title + '.mp4"'
  command_args = ' -vn -c:a libmp3lame -b:a 192k '  
  output_file = '"' + _processing_ + '/' + video_title + '.mp3"'

  running_command = audio_converter + command_input + input_file + command_args + " " + output_file
  cmd = shlex.split(running_command)

  color_print('    [+] Attempting to convert ' + input_file, 'blue')

  try:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    for line in process.stdout:
      if line[5:] == "size=":
        print line
    color_print('    [+] File converted', 'white')
  except Exception, e:
    
    color_print('    [!] Unable to convert file ' + input_file + ' "' + str(e) + '"', 'red')

  try:
    color_print('    [+] Removing old mp4 file', 'yellow')
    os.remove(input_file.strip('"'))
    color_print('    [+] Removed old mp4 file', 'blue')
  except Exception as e:
    color_print('    [!] Unable to delete file ' + input_file + ' "' + str(e) + '"', 'red')

def download_mp4(video_title, video_id):
  vid_url = 'http://www.youtube.com/watch?v={0}'.format(video_id)
  try:
    yt = YouTube(vid_url)
    yt.set_filename(video_title)
  except Exception as e:
    print "Error:", str(e), "- Skipping Video with url '" + vid_url + "'."
    return

  try:
    video = yt.get('mp4', '1080p')
  except Exception:
    video = sorted(yt.filter("mp4"), key=lambda video: int(video.resolution[:-1]), reverse=True)[0]

  print "Downloading " + yt.filename + " Video and Audio..."

  try:
      bar = progressBar()
      video.download(_processing_, on_progress=bar.print_progress, on_finish=bar.print_end)
      print "Successfully downloaded " + yt.filename + "!"
  except OSError:
      print yt.filename, "Error in the download process..."

def write_id3():

  artist_title = []
  for mp3_file in os.listdir(_processing_):
    if mp3_file.endswith('.mp3'):
      try:
        id3_mp3 = os.path.join(_processing_, mp3_file)
        track_presplit = mp3_file.strip('.mp3').strip()
        artist_title = track_presplit.split(' - ')

        if len(artist_title) == 2:
          artist = artist_title[0]
          title = artist_title[1]
          color_print('    [+] Starting id3 tag edit for ' + artist + ' - ' + title, 'blue')
          
          try:
            meta = EasyID3(id3_mp3)
          except mutagen.id3.ID3NoHeaderErrors:
            meta = mutagen.File(id3_mp3, easy=True)
            meta.add_tags()

          meta['artist'] = artist
          meta['title'] = title
          meta['genre'] = "Dubstep"
          meta.save()
        else:
          pass
      except Exception as e:
        print str(e)

def write_thumbnails():

  for mp3_file in os.listdir(_processing_):
    if mp3_file.endswith('.mp3'):
      try:
        
        search_string = mp3_file.strip('.mp3').strip()
        song_id = youtube_search(args, 1, search_string)
        url =  'http://img.youtube.com/vi/%s/0.jpg' % (song_id,)
        thumb_file = _thumb_dir_ + '/' + search_string + '.jpg'
        urllib.urlretrieve(url, thumb_file)

        thumb_mp3 = os.path.join(_processing_, mp3_file)

        mut_file = MP3(thumb_mp3, ID3=ID3)
        try:
          mut_file.add_tags()
        except error:
          pass
        mut_file.tags.add(
          APIC(
            encoding=3,
            mime='image/jpg',
            type=3,
            desc=u'Cover',
            data=open(thumb_file).read()
            )
          )
        color_print('    [+] Writing album art for ' + search_string, 'blue')
        mut_file.save()
        ''''getMutagenTags(thumb_mp3)'''
      except Exception as e:
        print str(e)

def finish_processing():
  for mp3_file in os.listdir(_processing_):
    if mp3_file.endswith('.mp3'):
      try:
        os.rename(os.path.join(_processing, mp3_file), os.path.join(_converted_, mp3_file))
        color_print('    [!] Finished moving ' + mp3_file, 'yellow')
      except Exception as e:
        print str(e)

class trackList(object):

  def __init__(self, video_title, video_id):

    self.video_title = video_title
    self.video_id = video_id
    self.file_Name = _processing_ + '/' + video_title + '.mp3' # YouTube Video Filename

  def get_tracklist(self):

    video_url = 'https://www.googleapis.com/youtube/v3/videos?id=' + self.video_id + '&key=' + DEVELOPER_KEY.strip('\n') + '&part=snippet'
    response = urllib2.urlopen(video_url)
    video_response = json.load(response)
    video_meta = []
    
    try:
      for v in video_response['items']:
        video_meta.append(v['snippet']['description'])

      for meta in video_meta: # Need to check this line, I don't think a for loop is required here since there is only one description
        description = self.parse_tracklist(meta)
      return description
    except:
      return False

  def parse_tracklist(self, meta):
    # If the line includes a valid timestamp, then capture the oline into a list
    track_list = []

    for line in meta.splitlines():
      # Might be better 
      # .*?\d{1,2}:\d{2}(:\d{2})?
      if re.match('.*?\d{1,2}:\d{2}(:\d{1,2})?', line): # Need to modify to capture more valid timestamps
        track_list.append(line)

    if track_list:
      return track_list
    else:
      return False

  def get_file_duration(self):
    cmd1 = "ffprobe -i "
    cmd2 = " -show_entries format=duration -v quiet -of csv='p=0'"
    full_command = cmd1 + '"' + self.file_Name + '"' + cmd2
    output = os.popen(full_command).read().strip("\n")
    if output:
      return output
    else:
      color_print('    [!] Could not extract duration of song', 'red')
      color_print('[!] QUITTING. Find a new song!', 'yellow')
      quit()

  def sanitize_title(self, track_name, track_time):

    # ASCII encode
    track_name = track_name.encode('ascii', errors='ignore')

    # Replace /, ", spaces
    track_name = track_name.replace('/', '').replace('"', '').replace(track_time, '')

    # Remove all entries between () and []
    regex = re.compile(r'([\(|\[]\w+.*[\]|\)])')
    string = regex.findall(track_name)
    
    # Strip off what was found (TODO: Fix regex so it doens't capture songs like 'Artist - Title (Something) More Title (Something else)')
    if string:
      file_name = track_name.replace(string[0], '')
      file_name = file_name.replace('.mp3', '').strip()
      color_print('    [+] Sanatized song title ' + track_name + ' to ' + file_name, 'green')
      return file_name
    else:
      return track_name

  def split_song_to_tracks(self, val, track_start, track_stop):

    audio_converter = 'ffmpeg'
    command_start = ' -ss '
    command_end = ' -t '
    command_input = ' -i '
    command_codec = ' -acodec copy '
    input_file = '"' + self.file_Name + '"'
    output_file = '"' + _processing_ + '/' + val + '.mp3"'

    # Handle final track float for track duration float
    track_end = float(track_stop) - track_start

    running_command = audio_converter + command_input + input_file + command_start + str(track_start) + command_end + str(track_end) + command_codec + " " + output_file
    cmd = shlex.split(running_command)

    color_print('    [+] Attempting to split track ' + val, 'blue')
    color_print('    [+] Splitting from ' + str(track_start) + ' to ' + str(track_stop), 'green')

    try:
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
      for line in process.stdout:
        if line[5:] == "size=":
          print(line)
      
      color_print('    [+] Track split', 'white')
    except Exception, e:
      
      color_print('    [!] Unable to split track ' + val + ' "' + str(e) + '"', 'red')

  def split_tracks(self, track_list):

    track_title = []
    track_seconds = []

    total_duration = self.get_file_duration()

    for ln in track_list:
    
      try:
        track_time = re.search('\d{1,3}:\d{2}(:\d{2})?', ln).group(0)
        track_name = re.search('[a-zA-Z]+.*[^0-9]*', ln).group(0)
        track_name = self.sanitize_title(track_name, track_time)
      except Exception, e:
        
        color_print('    [!] Unable to detect tracklist. ' + str(e), 'red')
      
      track_title.append(track_name)
     
      parts = track_time.split(':')
      seconds = None
      if len(parts) == 3: # h:m:s
        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
      elif len(parts) == 2: # m:s
        seconds = int(parts[0]) * 60 + int(parts[1])
      track_seconds.append(seconds)
    
    color_print('    [+] Track Detected. Attempting to split tracks', 'yellow')
    index = 0
    
    for i, val in enumerate(track_title):

      if index == len(track_title) - 1:
        self.split_song_to_tracks(val, track_seconds[index], total_duration)

      else:
        self.split_song_to_tracks(val, track_seconds[index], track_seconds[index + 1])
        index += 1

    os.rename(self.file_Name, os.path.join(_music_, self.video_title + '.mp3'))

    return track_title


def start_processing(video_title, video_id):
  
  download_mp4(video_title, video_id)
  convertTo_mp3(video_title)

  manageTracks = trackList(video_title, video_id)
  track_list = manageTracks.get_tracklist()

  if track_list:
    id3_tracks = manageTracks.split_tracks(track_list)
  else:
    color_print('    [!] Unable to detect tracklist. Skipping file.', 'red')
    color_print('    [!] Video ID is ' + video_id, 'blue')
    os.rename(os.path.join(_processing_, video_title + '.mp3'), os.path.join(_music_, video_title + '.mp3'))
    return False

  write_id3()
  write_thumbnails()
  finish_processing()

  color_print(' [!] All files processed!', 'white')

def youtube_search(options, thumbnail, tb_search):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  if thumbnail == 1:
    search_response = youtube.search().list(
      q=tb_search,
      part="id,snippet",
      maxResults=1
    ).execute()

    for search_result in search_response.get("items", []):
      if search_result["id"]["kind"] == "youtube#video":
        return search_result["id"]["videoId"]

  else:

    # Call the search.list method to retrieve results matching the query string
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
    print_colors = cycle_text(['white', 'blue', 'green', 'yellow'], 1)

    for video_title, video_id in videos.items():
      color_print('[' + str(counter) + '] ' +  video_title + ' | ' + video_id, print_colors.next())
      counter += 1

    print '\n'
    print '[1] Enter the number of the song you want to download'
    print '[2] Enter "list" to download the entire list'
    print '[3] Enter "exit" to exit'

    yes_no = raw_input("[?] How do you want to continue? ")

    if yes_no != 'list' and yes_no != 'exit':

      print '\n'
      download_number = int(yes_no)
      print '\n'

      download_number -= 1

      
      color_print('You selected: ' + videos.keys()[int(download_number)], 'yellow')
      new_yes = raw_input("Do you want to continue or select a new song? (yes to continue) ")
      
      # Format title to ascii characters only for easier management, and grab video ID for download function
      if new_yes == 'yes':
        video_title = videos.keys()[int(download_number)]
        video_title = video_title.encode('ascii', errors='ignore').replace('/', '').replace('"', '')
        if detect_livestream(video_title):
          color_print('[!] Live Stream found, please select another video to download.', 'red')
          youtube_search(options, 0, 0)

        single_video_id = videos.values()[int(download_number)]
        
        color_print('[!] Checking music folder for duplicates', 'blue')
        
        # Check for duplicated, if found re-run function
        if check_duplicates(video_title):
          
          color_print('[!] File found in database.', 'red')
          time.sleep(1)
          youtube_search(options, 0, 0) 

        else:
          
          color_print('\n[+] Starting Download and Conversion Process', 'green')
          start_processing(video_title, single_video_id)
          quit()

      else:
        youtube_search(options, 0, 0)

    elif yes_no == 'exit':
      
      color_print('[!] Exiting', 'red')
      quit()
       
    elif yes_no == 'list':

      print '\n'

      # Format the title and remove / and " characters
      for video_title, video_id in videos.items():
        
        video_title = video_title.encode('ascii', errors='ignore').replace('/', '').replace('"', '')
        if detect_livestream(video_title):
          color_print('[!] Live Stream found, Skipping.', 'red')
          pass
        else:

          # Check for duplicated, if found pass the file
          if check_duplicates(video_title):
            
            color_print('\n[!] Duplicate file found.', 'red')
            pass
          else:    
            color_print('\n[+] Starting Download and Conversion Process', 'green')
            start_processing(video_title, video_id)

    else:
      os.system('clear')
      
      color_print('[!] Please select 1, 2, or 3.', 'red')
      time.sleep(2)
      os.system('clear')
      youtube_search(options, 0, 0)

if __name__ == "__main__":

  # Check for directories prior to moving on
  _music_ = './Music'
  _processing_ = './Processing'
  _converted_ = './Converted'
  _tracklist_ = './Tracklist'
  _thumb_dir_ = './Thumbnails'

  if not os.path.isdir(_music_):
    os.makedirs(_music_)
  if not os.path.isdir(_processing_):
    os.makedirs(_processing_)
  if not os.path.isdir(_converted_):
    os.makedirs(_converted_)
  if not os.path.isdir(_tracklist_):
    os.makedirs(_tracklist_)
  if not os.path.isdir(_thumb_dir_):
    os.makedirs(_thumb_dir_)

  # Define youtube API key file name
  _youtube_key_ = './youtube.key'

  # Check if the youtube key file exists, if not then prompt for the API key and create the file
  if not os.path.exists(_youtube_key_):
    key_yesno = raw_input("Youtube Developer key not found, would you like to create one now? (Yes/No) ")
    if key_yesno == 'Yes':
      key_fromprompt = raw_input("Please enter your Youtube API Key ")
      with open('./youtube.key', 'w') as l:
        l.write(key_fromprompt)
    else:
      color_print('[!] Unable to find YouTube API Key File. Please re-create and try again.', 'red')
      quit()

  # Open the PAI key file and read the first line into variable
  with open('./youtube.key', 'r') as k:
    DEVELOPER_KEY = k.readline()

  # Define service and version name for Youtube API
  YOUTUBE_API_SERVICE_NAME = "youtube"
  YOUTUBE_API_VERSION = "v3"

  # Create arguments for YouTube search
  search_string = raw_input("Please enter a keyword to search: ")
  argparser.add_argument("--q", help="Search term", default=search_string)
  argparser.add_argument("--max-results", help="Max results", default=25)
  args = argparser.parse_args()

  try:
    # Start search function. This will branch off into the remainder of the script
    youtube_search(args, 0, 0)
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)