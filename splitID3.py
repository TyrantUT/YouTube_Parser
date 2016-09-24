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
  regex = re.compile(r'\w+(\s\s)\w+')

  for mp3_file in file_list:
    string = regex.findall(mp3_file)
    if string:
      fn =  mp3_file.replace('  ', ' - ')
    #fn = mp3_file.replace('.mp3.mp3', '.mp3')
      shutil.move(_musicFolder_ + mp3_file, _musicFolder_ + fn)
      artist_title = fn.split(' - ')
        
      if len(artist_title) == 2:
        artist = artist_title[0]
        title = artist_title[1].replace('.mp3', '')

      try:
        meta = EasyID3(_musicFolder_ + fn)
      except mutagen.id3.ID3NoHeaderErrors:
        meta = mutagen.File(_musicFolder_ + fn, easy=True)
        meta.add_tags()
        
      color_print('    [+] Starting id3 tag edit for ' + artist + ' - ' + title, 'blue')
      meta['artist'] = artist
      meta['title'] = title
      meta['genre'] = "Dubstep"
      meta['album'] = "Dubstep"
      meta.save()

if __name__ == "__main__":
  splitID3()

