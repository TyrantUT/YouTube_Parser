#!/usr/bin/python
"""
Python script to parse converted folder and start adding ID3 tags
"""
from mutagen.easyid3 import EasyID3
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import urlparse
import json
import re
import urllib
import urllib2
from os import walk
import os
from termcolor import colored
import re
import shutil
import collections
import argparse
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

_youtube_key_ = './youtube.key'
_thumb_dir_ = './Thumbnails/'


if not os.path.exists(_youtube_key_):
  print '[!] Unable to find YouTube API Key File. Please re-create and try again.'
  quit()

with open('./youtube.key', 'r') as k:
  DEVELOPER_KEY = k.readline()

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def color_print(p_string, color):
  print colored(p_string, color)

def youtube_start(title):
  search_string = title
  parser = argparse.ArgumentParser(conflict_handler='resolve')
  parser.add_argument("--q", help="Search term", default=search_string)
  parser.add_argument("--max-results", help="Max results", default=1)
  args = parser.parse_args()

  try:
    # Start search function. This will branch off into the remainder of the script
    youtube_search(args, title)
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)

def getMutagenTags(mp3_file):

  fileName = mp3_file.strip('.mp3')
  fileName = mp3_file.strip('./Converted/')
  artist_title = fileName.split(' - ')
  if len(artist_title) == 2:
    songArtist = artist_title[0]
    songTitle = artist_title[1]
  else:
    pass

  try:
    meta = EasyID3(mp3_file)
  except mutagen.id3.ID3NoHeaderErrors:
    meta = mutagen.File(mp3_file, easy=True)
    meta.add_tags()

  meta['artist'] = songArtist
  meta['title'] = songTitle
  meta['genre'] = "Dubstep"
  meta.save()

def youtube_search(options, title):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

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

    try:
      if yt_video_title == 'What are .DS_Store Files?':
        pass
      else:

        url =  'http://img.youtube.com/vi/%s/0.jpg' % (yt_video_id,)
        thumb_file = _thumb_dir_ + title + '.jpg'

        if os.path.exists(thumb_file):
          pass

        urllib.urlretrieve(url, thumb_file)

        mp3_file = _converted_ + title + '.mp3'

        mut_file = MP3(mp3_file, ID3=ID3)
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
        color_print('Writing album art for ' + title, 'blue')
        mut_file.save()
        getMutagenTags(mp3_file)

    except Exception, e:
      print str(e)


  
if __name__ == "__main__":
  _converted_ = './Converted/'
  file_list = []
  for (dirpath, dirnames, filenames) in os.walk(_converted_):
    file_list.extend(filenames)
  for mp3_title in file_list:
    title = mp3_title.replace('.mp3', '')

  # Create arguments for YouTube search
    youtube_start(title)