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
    filename = mp3_file.split(' - ')
    if len(filename) == 2:

      regex = re.compile(r'(\(\w+.*?\))')
      #regex = re.compile(r'(\d{1,3}:\d{2}(:\d{2})?)')
      regex2 = re.compile(r'(\[\w+.*?\])')
      string = regex.findall(mp3_file)
      string2 = regex2.findall(mp3_file)
      # Remove anythign betwen []
      if string2:
        fn =  mp3_file.replace(string2[0], '').replace('  ', ' ').replace('.mp3', '').strip()
        color_print('Renaming ' + _musicFolder_ + mp3_file + ' to ' + _musicFolder_ + fn + '.mp3', 'blue')
        shutil.move(_musicFolder_ + mp3_file, _musicFolder_ + fn + '.mp3')

      # Remove anything between ()
      if len(string) == 1:
        fn =  mp3_file.replace(string[0], '').replace('  ', ' ').replace('.mp3', '').strip()
      elif len(string) == 2:
        fn = mp3_file.replace(string[0], '').replace(string[1], '').replace('  ', ' ').replace('.mp3', '').strip()
      elif len(string) < 1:
        pass
      try:
        color_print('Renaming ' + _musicFolder_ + mp3_file + ' to ' + _musicFolder_ + fn + '.mp3', 'blue')
        shutil.move(_musicFolder_ + mp3_file, _musicFolder_ + fn + '.mp3')
      except Exception, e:
        color_print('No need to alter any filenames!', 'red')
    else:
      pass


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
    counter += 1
  print counter
if __name__ == "__main__":
  splitID3()

