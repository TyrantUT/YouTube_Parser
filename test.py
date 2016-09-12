#!/usr/bin/python
from pydub import AudioSegment
import os

new_files = AudioSegment.from_mp3("./new.mp3")
new_files.export("./Sup.mp3", format="mp3")
