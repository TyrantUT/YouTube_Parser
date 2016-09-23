#!/usr/bin/python
"""
Python script to parse converted folder and start adding ID3 tags
"""
from mutagen.easyid3 import EasyID3
from os import walk
import os
from termcolor import colored
import re
import shutil

def color_print(p_string, color):
  print colored(p_string, color)

def splitID3():
  _musicFolder_ = './Converted/'
  file_list = []
  artist_title = []

# Bring all the track names into file_list
  for (dirpath, dirnames, filenames) in walk(_musicFolder_):
    file_list.extend(filenames)
    break
  counter = 0
  for mp3_file in file_list:
    #regex = re.compile(r'(\d{1,3}:\d{2}(:\d{2})?)')
     
    try:
      artist_title = mp3_file.split(' - ')
      if len(artist_title) == 2:
        filePath = _musicFolder_ + mp3_file
        artist = artist_title[0]
        title = artist_title[1].replace('.mp3', '')
        color_print('[+] Starting ID3 tag edit for ' + artist + ' - ' + title, 'blue')
        try:
          meta = EasyID3(filePath)
        except mutagen.id3.ID3NoHeaderError:
          meta = mutagen.File(filePath, easy=True)
          meta.add_tags()
        meta['artist'] = artist
        meta['albumartist'] = artist
        meta['title'] = title
        meta['genre'] = "Dubstep"
        meta['album'] = "Dubstep"
        meta.save()
      else:
        pass
    except Exception, e:
      print str(e)

if __name__ == "__main__":
  splitID3()

