#!/usr/bin/python
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

# manage_tracks objects handle all track parsing, splitting, and renaming operations
class manage_tracks(object):

  def __init__(self, yt_id = None, yt_title_mp3 = None):
    self.yt_id = yt_id
    self.yt_title_mp3 = yt_title_mp3

  def get_tracklist(self):

    video_url = 'https://www.googleapis.com/youtube/v3/videos?id=' + self.yt_id + '&key=' + DEVELOPER_KEY.strip('\n') + '&part=snippet'
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
    return track_time_name
  
  def print_track(self, des):
    print des

if __name__ == "__main__":

  m = manage_tracks("dLyH94jNau0", "Title")
  try:
    d = m.get_tracklist()
    for i in d:
      m.print_track(i)
  except:
    print 'None'