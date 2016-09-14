#!/usr/bin/python
import os
import io


file = '"3 HOURS Best Female Vocal Dubstep Mix 2015 (by DYJ) - Dubstep Remix 2015.mp3"'

cmd1 = "ffprobe -i "
cmd2 = file
cmd3 = " -show_entries format=duration -v quiet -of csv='p=0'"

full_command = cmd1 + cmd2 + cmd3
output = os.popen(full_command).read().strip("\n")

print output