#!/usr/bin/python
"""
Python script to parse converted folder and start adding ID3 tags
"""


from mutagen.easyid3 import EasyID3
import os
from os import walk

_musicFolder_ = './Converted/'

def splitID3():

  file_list = []
  artist_title = []

  # Bring all the track names into file_list
  for (dirpath, dirnames, filenames) in walk(_musicFolder_):
  	file_list.extend(filenames)
  	break

  for mp3_file in file_list:
  	try:
  	  artist_title = mp3_file.split(' - ')

  	  if len(artist_title) == 2:
  	  	filePath = _musicFolder_ + mp3_file
  	  	artist = artist_title[0]
  	  	title = artist_title[1].replace('.mp3', '')
  	  	print '[+] Starting ID3 tag edit for ' + artist + ' - ' + title

  	  	try:
  	  		meta = EasyID3(filePath)
  	  	except mutagen.id3.ID3NoHeaderError:

  	  		mmeta = mutagen.File(filePath, easy=True)
  	  		meta.add_tags()

  	  	meta['artist'] = artist
  	  	meta['title'] = title
  	  	meta['genre'] = "Dubstep"
  	  	meta.save()
        print '[+] ID3 Tags generated.'
  	  else:
  	  	pass

  	except Exception, e:
  	 	print str(e)

if __name__ == "__main__":
  splitID3()

