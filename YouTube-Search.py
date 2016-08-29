#!/usr/bin/python
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import youtube_dl
import sys
import urlparse
import json
import urllib
import time
import os
import glob

DEVELOPER_KEY = "AIzaSyAOeOazXFgWKfMIcSZ2Crhgclr6VIy0MPI"
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
        print '    [+] Download speed: ' + d['_speed_str'] + '\t\t Percent Complete: ' + d['_percent_str'],
        sys.stdout.flush()
        restart_line()
        
    if d['status'] == 'finished':
        print('\n    [+] Download Complete. Conversion in progress...')

def download_mp3(title, url):
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
    info_dict = ydl.extract_info(url, download=False)
    pre_title = info_dict.get('title', None)
    print('    [+] Now downloading: ' + title + '.mp3')
    try:
      ydl.download([url])
    except:
      print('    [+] Failed to download / convert MP3')

  print('    [+] Conversion complete')
  print('    [+] Renaming file')

  try:
    newest = max(glob.iglob('./*.[Mm][Pp]3'), key=os.path.getctime)
    os.rename(newest, './Music/' + title + '.mp3')
  except:
    print('[!] Unable to rename file', sys.exc_info()[0])
  print('    [+] Renaming complete')

def check_db(title, datafile):
  for line in datafile:
    if line.strip("\n") == title:
      return True
    else:
      pass
  return False

def write_db(title, datafile):
  datafile.write(title + '\n')

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
      videos.update({search_result["snippet"]["title"]: "https://youtube.com/watch?v=" + search_result["id"]["videoId"]})
  
  # Print titles found and prompt to continue
  os.system('clear')
  print "\nThis is what I found\n"
  counter = 1
  for title, url in videos.items():
    print '[+] ' + str(counter) + ' ' +  title
    counter += 1
  print '\n'
  print '[1] Enter 1 to download a specific item'
  print '[2] Enter 2 to to continue with the full list'
  print '[3] Enter 3 to exit'
  yes_no = raw_input("[?] How do you want to continue? ")

  if yes_no == '1':

    print '\n'
    download_number = raw_input("Please enter the number of the video you want to download: ")
    print '\n'
    download_number =- 1
    print 'You selected: ' + videos.keys()[download_number]
    new_yes = raw_input("Do you want to continue or select a new song? (yes to continue) ")
   
    if new_yes == 'yes':

      title = videos.keys()[download_number]
      title = title.encode('ascii', errors='ignore')
      urls = videos.values()[download_number]
      datafile = open("./Downloaded_mp3.txt", "r+a")
      print '[!] Checking database for duplicates'
      
      if check_db(title, datafile):
        print "[!] File found in database."
        datafile.close()
        time.sleep(1)
        youtube_search(options)

      else:
        print "[+] Starting Download and Conversion Process"
        download_mp3(title, url)
        print "[+] Writing " + title + " to database"
        write_db(title, datafile)
        datafile.close()
        exit()

    else:
      youtube_search(options)

  elif yes_no == '3':
    print "[!] Exiting"
    exit()

  elif yes_no == '2':

    print '\n'
    # Call the check database file
    for title, url in videos.items():
      
      title = title.encode('ascii', errors='ignore')
      datafile = open("./Downloaded_mp3.txt", "r+a")

      if check_db(title, datafile):
        print "[!] File found in database."
        datafile.close()
      else:
        print "[+] Starting Download and Conversion Process"
        download_mp3(title, url)

        print "[+] Writing " + title + " to database"
        write_db(title, datafile)
        datafile.close()
  else:
    os.system('clear')
    print "[!] Please select 1, 2, or 3."
    youtube_search(options)
      


if __name__ == "__main__":
  
  search_string = raw_input("Please enter a keyword to search: ")
  argparser.add_argument("--q", help="Search term", default=search_string)
  argparser.add_argument("--max-results", help="Max results", default=25)
  args = argparser.parse_args()

  try:
    youtube_search(args)
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)